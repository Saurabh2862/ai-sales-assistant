from __future__ import annotations
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
from pathlib import Path

from .pdf_engine import extract_line_items, items_to_df

def compare_po_pi(po_pdf: str, pi_pdf: str, out_dir: str = "outputs") -> Tuple[List[Dict[str, Any]], Dict[str, Any], str, str]:
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)

    po_items = items_to_df(extract_line_items(po_pdf))
    pi_items = items_to_df(extract_line_items(pi_pdf))

    # Merge on SKU
    merged = po_items.merge(
        pi_items,
        on="sku",
        how="outer",
        suffixes=("_po","_pi"),
        indicator=True
    )

    def neq(a, b, tol=1e-6):
        if pd.isna(a) and pd.isna(b):
            return False
        if isinstance(a, (int, float, np.number)) and isinstance(b, (int, float, np.number)):
            return abs(float(a) - float(b)) > tol
        return str(a) != str(b)

    discrepancies = []
    for _, r in merged.iterrows():
        issues = []
        if r["_merge"] != "both":
            issues.append("MISSING_IN_" + ("PI" if r["_merge"] == "left_only" else "PO"))

        if neq(r.get("qty_po"), r.get("qty_pi"), tol=0):
            issues.append("QTY_MISMATCH")
        if neq(r.get("unit_price_po"), r.get("unit_price_pi"), tol=0.01):
            issues.append("UNIT_PRICE_MISMATCH")
        if neq(r.get("discount_pct_po"), r.get("discount_pct_pi"), tol=0.01):
            issues.append("DISCOUNT_MISMATCH")
        if neq(r.get("tax_pct_po"), r.get("tax_pct_pi"), tol=0.01):
            issues.append("TAX_MISMATCH")

        if issues:
            discrepancies.append({
                "sku": r["sku"],
                "issues": issues,
                "po": {
                    "description": r.get("description_po"),
                    "qty": r.get("qty_po"),
                    "unit_price": r.get("unit_price_po"),
                    "discount_pct": r.get("discount_pct_po"),
                    "tax_pct": r.get("tax_pct_po"),
                },
                "pi": {
                    "description": r.get("description_pi"),
                    "qty": r.get("qty_pi"),
                    "unit_price": r.get("unit_price_pi"),
                    "discount_pct": r.get("discount_pct_pi"),
                    "tax_pct": r.get("tax_pct_pi"),
                }
            })

    disc_df = pd.DataFrame([{
        "sku": d["sku"],
        "issues": ";".join(d["issues"]),
        "qty_po": d["po"]["qty"],
        "qty_pi": d["pi"]["qty"],
        "unit_price_po": d["po"]["unit_price"],
        "unit_price_pi": d["pi"]["unit_price"],
        "discount_po": d["po"]["discount_pct"],
        "discount_pi": d["pi"]["discount_pct"],
        "tax_po": d["po"]["tax_pct"],
        "tax_pi": d["pi"]["tax_pct"],
    } for d in discrepancies])

    csv_path = str(outp / "pdf_discrepancies.csv")
    json_path = str(outp / "pdf_discrepancies.json")
    disc_df.to_csv(csv_path, index=False)
    disc_df.to_json(json_path, orient="records", indent=2)

    summary = {
        "po_items": int(len(po_items)),
        "pi_items": int(len(pi_items)),
        "discrepancy_count": int(len(discrepancies)),
        "skus_with_issues": [d["sku"] for d in discrepancies],
    }
    return discrepancies, summary, csv_path, json_path
