from __future__ import annotations
import json
from typing import Any, Dict
from .llm import responses_text
from .schemas import ParsedQuery

ANSWER_INSTRUCTIONS = """You are a response writer for a business analytics assistant.
You will receive:
1) the user question
2) the parsed JSON plan
3) the verified backend results

Rules:
- Use ONLY the provided backend results for any numbers.
- Do NOT invent missing metrics, trends, reasons, or additional calculations.
- If the plan intent is CLARIFICATION_REQUIRED, ask the clarification_question.
- If a table is present in result.table, summarize it briefly (top rows).
- Keep the answer concise and business-friendly.
"""

def write_answer(question: str, plan: ParsedQuery, result: Dict[str, Any]) -> str:
    payload = {"question": question, "plan": plan.model_dump(), "result": result}
    prompt = f"""{ANSWER_INSTRUCTIONS}

INPUT (JSON):
{json.dumps(payload, indent=2)}
"""
    return responses_text(prompt).strip()
