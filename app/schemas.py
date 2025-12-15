from __future__ import annotations

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field

Intent = Literal[
    "TOTAL_SALES",
    "TOTAL_ACTIVE_STORES",
    "BREAKDOWN",
    "COMPARE_YOY",
    "TOP_N",
    "PDF_COMPARE",
    "CLARIFICATION_REQUIRED",
    "UNSUPPORTED",
]

# NOTE: group_by is allowed on these dimensions
GroupBy = Literal[
    "brand",
    "category",
    "product",
    "region",
    "country",
    "city",
    "area",
    "channel",
    "sub_channel",
    "salesman",
    "customer",
    "customer_account_name",
    "retailer_group",
    "retailer_sub_group",
    "master_distributor",
    "distributor",
    "line_of_business",
    "supplier",
    "agency",
    "segment",
    "sub_brand",
    "promo",
    "month",
]


class Filters(BaseModel):
    # Core dims
    brand: Optional[str] = None
    category: Optional[str] = None
    product: Optional[str] = None  # item description (preferred)
    region: Optional[str] = None   # keep for backward compat; mapped to country/city/area if needed

    # Extra dims from your Excel
    country: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None

    channel: Optional[str] = None
    sub_channel: Optional[str] = None

    salesman: Optional[str] = None

    customer: Optional[str] = None
    customer_account_name: Optional[str] = None

    retailer_group: Optional[str] = None
    retailer_sub_group: Optional[str] = None

    master_distributor: Optional[str] = None
    distributor: Optional[str] = None
    line_of_business: Optional[str] = None
    supplier: Optional[str] = None
    agency: Optional[str] = None
    segment: Optional[str] = None
    sub_brand: Optional[str] = None
    promo: Optional[str] = None

    # Time filters
    month: Optional[str] = Field(default=None, description="YYYY-MM")
    months: Optional[List[str]] = Field(default=None, description="List of YYYY-MM")
    year: Optional[int] = None
    quarter: Optional[str] = Field(default=None, description="e.g. 2024-Q2")


class ParsedQuery(BaseModel):
    intent: Intent
    metric: Optional[Literal["sales", "active_stores"]] = None
    filters: Filters = Field(default_factory=Filters)

    group_by: Optional[GroupBy] = None
    limit: Optional[int] = Field(default=None, ge=1, le=50)

    compare_to: Optional[Literal["same_period_last_year"]] = None
    clarification_question: Optional[str] = None


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    plan: ParsedQuery
    result: Dict[str, Any]
    answer: str


class PdfCompareResponse(BaseModel):
    discrepancies: List[Dict[str, Any]]
    summary: Dict[str, Any]
    csv_path: str
    json_path: str
