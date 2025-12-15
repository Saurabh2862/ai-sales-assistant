from __future__ import annotations

import re
from typing import Optional, Tuple, Any

import pandas as pd

from ..config import settings
from .sales_schema import Cols

SHEET_NAME = "Sales 2022 Onwards"


COL_MAP = {

    "year": "Year",
    "month": "Month",

    
    "sales_value": "Value",

   
    "brand": "Brand",
    "category": "Category",
    "product_desc": "Item Description",

    
    "country": "Country",
    "city": "City",
    "area": "Area",

    
    "channel": "Channel",
    "sub_channel": "Sub Channel",

    
    "salesman": "Salesmen",

    
    "customer": "Customer",
    "customer_account_name": "Customer Account Name",
    "store_id": "Customer Account Number",

    
    "master_distributor": "Master Distributor",
    "distributor": "Distributor",
    "line_of_business": "Line of Business",
    "supplier": "Supplier",
    "agency": "Agency",
    "segment": "Segment",
    "sub_brand": "Sub Brand",
    "promo": "Promo Item",
}

MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

def _clean_str(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()

def _normalize_month_to_num(series: pd.Series) -> pd.Series:
    def to_month(v: Any) -> Optional[int]:
        if pd.isna(v):
            return None
        x = _clean_str(v).upper()
        x = re.sub(r"\s+", "", x)

        if x.isdigit():
            m = int(x)
            return m if 1 <= m <= 12 else None

        x3 = x[:3]
        if x3 in MONTH_MAP:
            return MONTH_MAP[x3]

        for k, m in MONTH_MAP.items():
            if k in x:
                return m
        return None

    return series.map(to_month)

def _require(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise RuntimeError(
            f"Sheet '{SHEET_NAME}' missing columns: {missing}. "
            f"Available (first 50): {list(df.columns)[:50]}"
        )

def load_sales_dataframe(path: Optional[str] = None) -> Tuple[pd.DataFrame, Cols]:
    path = path or settings.sales_file
    df = pd.read_excel(path, sheet_name=SHEET_NAME, engine="pyxlsb")
    if df is None or df.empty:
        raise RuntimeError(f"Sheet '{SHEET_NAME}' is empty or not found in {path}.")

    # Require minimum columns to function
    _require(df, [COL_MAP["year"], COL_MAP["month"], COL_MAP["sales_value"], COL_MAP["store_id"]])

    # Standard helpers
    df["_year"] = pd.to_numeric(df[COL_MAP["year"]], errors="coerce").astype("Int64")
    df["_month_num"] = _normalize_month_to_num(df[COL_MAP["month"]]).astype("Int64")
    df = df.dropna(subset=["_year", "_month_num"])

    df["_period"] = df["_year"].astype(int).astype(str) + "-" + df["_month_num"].astype(int).astype(str).str.zfill(2)
    df["_quarter"] = df["_year"].astype(int).astype(str) + "-Q" + (((df["_month_num"].astype(int) - 1) // 3) + 1).astype(str)

    df["_sales"] = pd.to_numeric(df[COL_MAP["sales_value"]], errors="coerce").fillna(0.0).astype(float)
    df["_store_id"] = df[COL_MAP["store_id"]].astype(str).str.strip()

    # Build Cols mapping (engine uses these)
    cols = Cols(
        date="_period",
        year="_year",
        quarter="_quarter",
        sales="_sales",

        brand=COL_MAP.get("brand") if COL_MAP.get("brand") in df.columns else None,
        category=COL_MAP.get("category") if COL_MAP.get("category") in df.columns else None,
        product=COL_MAP.get("product_desc") if COL_MAP.get("product_desc") in df.columns else None,

        # For backward-compat “region”
        region=COL_MAP.get("country") if COL_MAP.get("country") in df.columns else None,

        country=COL_MAP.get("country") if COL_MAP.get("country") in df.columns else None,
        city=COL_MAP.get("city") if COL_MAP.get("city") in df.columns else None,
        area=COL_MAP.get("area") if COL_MAP.get("area") in df.columns else None,

        channel=COL_MAP.get("channel") if COL_MAP.get("channel") in df.columns else None,
        sub_channel=COL_MAP.get("sub_channel") if COL_MAP.get("sub_channel") in df.columns else None,
        salesman=COL_MAP.get("salesman") if COL_MAP.get("salesman") in df.columns else None,

        customer=COL_MAP.get("customer") if COL_MAP.get("customer") in df.columns else None,
        customer_account_name=COL_MAP.get("customer_account_name") if COL_MAP.get("customer_account_name") in df.columns else None,

        retailer_group="Retailer Group" if "Retailer Group" in df.columns else None,
        retailer_sub_group="Retailer Sub Group" if "Retailer Sub Group" in df.columns else None,

        master_distributor=COL_MAP.get("master_distributor") if COL_MAP.get("master_distributor") in df.columns else None,
        distributor=COL_MAP.get("distributor") if COL_MAP.get("distributor") in df.columns else None,
        line_of_business=COL_MAP.get("line_of_business") if COL_MAP.get("line_of_business") in df.columns else None,
        supplier=COL_MAP.get("supplier") if COL_MAP.get("supplier") in df.columns else None,
        agency=COL_MAP.get("agency") if COL_MAP.get("agency") in df.columns else None,
        segment=COL_MAP.get("segment") if COL_MAP.get("segment") in df.columns else None,
        sub_brand=COL_MAP.get("sub_brand") if COL_MAP.get("sub_brand") in df.columns else None,
        promo=COL_MAP.get("promo") if COL_MAP.get("promo") in df.columns else None,
    )

    return df, cols
