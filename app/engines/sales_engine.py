from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd

from ..schemas import ParsedQuery
from ..data.sales_loader import load_sales_dataframe
from ..data.sales_schema import Cols


class PlanValidationError(ValueError):
    pass


def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = str(s).strip()
    return s if s else None


def _ci_eq(series: pd.Series, value: str) -> pd.Series:
    return series.astype(str).str.strip().str.lower() == value.strip().lower()


def _validate_plan(plan: ParsedQuery, cols: Cols) -> None:
    allowed_intents = {"TOTAL_SALES", "TOTAL_ACTIVE_STORES", "BREAKDOWN", "COMPARE_YOY", "TOP_N"}
    if plan.intent not in allowed_intents:
        raise PlanValidationError(f"Unsupported intent for sales engine: {plan.intent}")

    if plan.metric not in ("sales", "active_stores"):
        raise PlanValidationError("metric must be 'sales' or 'active_stores'")

    if plan.intent in ("BREAKDOWN", "TOP_N"):
        if not plan.group_by:
            raise PlanValidationError("group_by is required for BREAKDOWN and TOP_N")

    # COMPARE_YOY requires exactly one time unit (month OR quarter OR year)
    f = plan.filters
    if plan.intent == "COMPARE_YOY":
        time_count = int(bool(f.month)) + int(bool(f.quarter)) + int(bool(f.year)) + int(bool(f.months))
        if time_count != 1:
            raise PlanValidationError("COMPARE_YOY requires exactly one time filter: month OR months OR quarter OR year.")

    if cols.sales is None:
        raise PlanValidationError("Sales column mapping not available.")


def _apply_filters(df: pd.DataFrame, cols: Cols, plan: ParsedQuery) -> pd.DataFrame:
    f = plan.filters

    # --- dimension filters ---
    def apply_if(attr_name: str, value: Optional[str]) -> None:
        nonlocal df
        v = _norm(value)
        if not v:
            return
        col = getattr(cols, attr_name, None)
        if col is None:
            return
        df = df[_ci_eq(df[col], v)]

    apply_if("brand", f.brand)
    apply_if("category", f.category)
    apply_if("product", f.product)

    # region kept for compat (maps to cols.region)
    apply_if("region", f.region)

    apply_if("country", f.country)
    apply_if("city", f.city)
    apply_if("area", f.area)

    apply_if("channel", f.channel)
    apply_if("sub_channel", f.sub_channel)

    apply_if("salesman", f.salesman)

    apply_if("customer", f.customer)
    apply_if("customer_account_name", f.customer_account_name)

    apply_if("retailer_group", f.retailer_group)
    apply_if("retailer_sub_group", f.retailer_sub_group)

    apply_if("master_distributor", f.master_distributor)
    apply_if("distributor", f.distributor)
    apply_if("line_of_business", f.line_of_business)
    apply_if("supplier", f.supplier)
    apply_if("agency", f.agency)
    apply_if("segment", f.segment)
    apply_if("sub_brand", f.sub_brand)
    apply_if("promo", f.promo)

    # --- time filters ---
    if f.month:
        df = df[df[cols.date] == f.month]

    if f.months:
        df = df[df[cols.date].isin([str(x).strip() for x in f.months if str(x).strip()])]

    if f.quarter:
        df = df[df[cols.quarter] == f.quarter]

    if f.year:
        df = df[df[cols.year] == f.year]

    return df


def _metric_series(df: pd.DataFrame, plan: ParsedQuery, cols: Cols) -> pd.Series:
    if plan.metric == "sales":
        return df[cols.sales]
    # active stores = unique store_id where sales > 0
    df_pos = df[df[cols.sales] > 0]
    return df_pos["_store_id"]


def _group_col(cols: Cols, gb: str) -> Optional[str]:
    if gb == "month":
        return cols.date
    return getattr(cols, gb, None)


def _aggregate(df: pd.DataFrame, plan: ParsedQuery, cols: Cols) -> Dict[str, Any]:
    if df.empty:
        return {"ok": True, "rows": 0, "message": "No data matched the filters.", "value": 0}

    if plan.intent in ("TOTAL_SALES", "TOTAL_ACTIVE_STORES"):
        if plan.metric == "sales":
            total = float(_metric_series(df, plan, cols).sum())
            return {"ok": True, "rows": int(len(df)), "metric": "sales", "value": total}
        stores = int(_metric_series(df, plan, cols).nunique())
        return {"ok": True, "rows": int(len(df)), "metric": "active_stores", "value": stores}

    if plan.intent in ("BREAKDOWN", "TOP_N"):
        gb = plan.group_by
        assert gb is not None

        group_col = _group_col(cols, gb)
        if group_col is None:
            raise PlanValidationError(f"Cannot group by '{gb}' (no column mapping).")

        if plan.metric == "sales":
            out = df.groupby(group_col)[cols.sales].sum().sort_values(ascending=False)
        else:
            out = df[df[cols.sales] > 0].groupby(group_col)["_store_id"].nunique().sort_values(ascending=False)

        if plan.intent == "TOP_N":
            out = out.head(int(plan.limit or 5))

        table = [{"group": str(idx), "value": float(val)} for idx, val in out.items()]
        return {"ok": True, "rows": int(len(df)), "metric": plan.metric, "group_by": gb, "table": table}

    if plan.intent == "COMPARE_YOY":
        # total current
        base_total = _aggregate(df, ParsedQuery(**{**plan.model_dump(), "intent": "TOTAL_SALES" if plan.metric == "sales" else "TOTAL_ACTIVE_STORES"}), cols)

        f = plan.filters.model_dump()
        # shift -1 year
        if f.get("month"):
            y, m = f["month"].split("-")
            f["month"] = f"{int(y)-1:04d}-{int(m):02d}"
        if f.get("months"):
            shifted = []
            for mm in f["months"]:
                y, m = str(mm).split("-")
                shifted.append(f"{int(y)-1:04d}-{int(m):02d}")
            f["months"] = shifted
        if f.get("quarter"):
            y, q = f["quarter"].split("-Q")
            f["quarter"] = f"{int(y)-1:04d}-Q{q}"
        if f.get("year"):
            f["year"] = int(f["year"]) - 1

        plan_ly = ParsedQuery(**{**plan.model_dump(), "filters": f})
        # reuse loaded df via module cache
        df_ly = _apply_filters(_GLOBAL_DF, cols, plan_ly)  # type: ignore[arg-type]
        ly_total = _aggregate(df_ly, ParsedQuery(**{**plan_ly.model_dump(), "intent": "TOTAL_SALES" if plan.metric == "sales" else "TOTAL_ACTIVE_STORES"}), cols)

        cur_val = float(base_total["value"])
        ly_val = float(ly_total["value"])
        delta = cur_val - ly_val
        pct = (delta / ly_val * 100.0) if ly_val != 0 else None

        return {"ok": True, "metric": plan.metric, "current": cur_val, "last_year": ly_val, "delta": delta, "delta_pct": pct}

    raise PlanValidationError(f"Unhandled intent: {plan.intent}")


_GLOBAL_DF: Optional[pd.DataFrame] = None
_GLOBAL_COLS: Optional[Cols] = None


class SalesEngine:
    def __init__(self, df: pd.DataFrame, cols: Cols):
        self.df = df
        self.cols = cols

    @classmethod
    def from_file(cls, path: str) -> "SalesEngine":
        global _GLOBAL_DF, _GLOBAL_COLS
        df, cols = load_sales_dataframe(path)
        _GLOBAL_DF, _GLOBAL_COLS = df, cols
        return cls(df, cols)

    def execute(self, plan: ParsedQuery) -> Dict[str, Any]:
        _validate_plan(plan, self.cols)
        df = _apply_filters(self.df, self.cols, plan)
        return _aggregate(df, plan, self.cols)
