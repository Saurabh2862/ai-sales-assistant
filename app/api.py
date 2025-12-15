from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ChatRequest, ChatResponse, PdfCompareResponse
from .planner import parse_question_to_plan
from .engines.sales_engine import SalesEngine
from .engines.pdf_compare import compare_po_pi
from .answer_writer import write_answer
from .config import settings

app = FastAPI(title="Accurate Sales + PDF Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sales_engine = None

def sales_engine() -> SalesEngine:
    global _sales_engine
    if _sales_engine is None:
        _sales_engine = SalesEngine.from_file(settings.sales_file)
    return _sales_engine

@app.get("/")
def health():
    return {"ok": True, "service": "Accurate Sales + PDF Assistant"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    plan = parse_question_to_plan(req.question)

    if plan.intent == "CLARIFICATION_REQUIRED":
        result = {"clarification_required": True}
        answer = plan.clarification_question or "Could you clarify your request?"
        return ChatResponse(plan=plan, result=result, answer=answer)

    if plan.intent == "UNSUPPORTED":
        result = {"unsupported": True}
        answer = "Sorry — I can only answer sales/active stores questions, or compare PO vs PI PDFs."
        return ChatResponse(plan=plan, result=result, answer=answer)

    if plan.intent == "PDF_COMPARE":
        result = {"hint": "Call POST /pdf/compare to generate discrepancy report."}
        answer = "To compare the Purchase Order vs Proforma Invoice, call POST /pdf/compare (it generates CSV/JSON reports)."
        return ChatResponse(plan=plan, result=result, answer=answer)

    try:
        result = sales_engine().execute(plan)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    answer = write_answer(req.question, plan, result)
    return ChatResponse(plan=plan, result=result, answer=answer)

@app.post("/pdf/compare", response_model=PdfCompareResponse)
def pdf_compare():
    try:
        discrepancies, summary, csv_path, json_path = compare_po_pi(settings.po_pdf, settings.pi_pdf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PdfCompareResponse(
        discrepancies=discrepancies,
        summary=summary,
        csv_path=csv_path,
        json_path=json_path,
    )
