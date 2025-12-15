from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Cols:
    # Time
    date: str
    year: str
    quarter: str

    # Metrics
    sales: Optional[str] = None

    # Core dims
    brand: Optional[str] = None
    category: Optional[str] = None
    product: Optional[str] = None
    region: Optional[str] = None  # backward compat (we can map to country)

    # Extra dims
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
