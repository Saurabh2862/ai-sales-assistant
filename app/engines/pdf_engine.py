from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
import pdfplumber
import pandas as pd

SKU_RE = re.compile(r"^A\d{4}$")

@dataclass
class LineItem:
    sku: str
    description: str
    qty: int
    unit_price: float
    discount_pct: float
    tax_pct: float

def _to_float(x: Any) -> float:
    try:
        return float(str(x).replace(",", "").strip())
    except Exception:
        return float("nan")

def _to_int(x: Any) -> int:
    try:
        return int(float(str(x).replace(",", "").strip()))
    except Exception:
        return -1

def extract_line_items(pdf_path: str, table_start_header: str = "SKU") -> List[LineItem]:
    """Extracts line items from a semi-structured PDF table using pdfplumber.

    Assumes the table has a header row containing: SKU, Description, Qty, Unit Price, Discount %, Tax %
    (additional columns are ignored).
    """
    items: List[LineItem] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for tbl in tables:
                if not tbl or len(tbl) < 2:
                    continue
                header = [str(h or "").strip() for h in tbl[0]]
                header_join = " ".join(h.lower() for h in header)
                if "sku" not in header_join or "qty" not in header_join:
                    continue

                # Map column indices by header name (flexible)
                def find_idx(keys):
                    for k in keys:
                        for i, h in enumerate(header):
                            if k in h.lower():
                                return i
                    return None

                idx_sku = find_idx(["sku"])
                idx_desc = find_idx(["description"])
                idx_qty = find_idx(["qty"])
                idx_price = find_idx(["unit price", "price"])
                idx_disc = find_idx(["discount"])
                idx_tax = find_idx(["tax %", "tax"])

                if idx_sku is None or idx_qty is None or idx_price is None:
                    continue

                for row in tbl[1:]:
                    if not row or idx_sku >= len(row):
                        continue
                    sku = str(row[idx_sku] or "").strip()
                    if not SKU_RE.match(sku):
                        continue
                    desc = str(row[idx_desc] or "").strip() if idx_desc is not None and idx_desc < len(row) else ""
                    qty = _to_int(row[idx_qty]) if idx_qty is not None and idx_qty < len(row) else -1
                    unit_price = _to_float(row[idx_price]) if idx_price is not None and idx_price < len(row) else float("nan")
                    discount = _to_float(row[idx_disc]) if idx_disc is not None and idx_disc < len(row) else 0.0
                    tax = _to_float(row[idx_tax]) if idx_tax is not None and idx_tax < len(row) else 0.0

                    items.append(LineItem(sku=sku, description=desc, qty=qty, unit_price=unit_price, discount_pct=discount, tax_pct=tax))

    if not items:
        raise RuntimeError(f"No line items extracted from {pdf_path}. Try adjusting extraction heuristics.")
    return items

def items_to_df(items: List[LineItem]) -> pd.DataFrame:
    return pd.DataFrame([{
        "sku": it.sku,
        "description": it.description,
        "qty": it.qty,
        "unit_price": it.unit_price,
        "discount_pct": it.discount_pct,
        "tax_pct": it.tax_pct,
    } for it in items])
