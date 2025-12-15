from __future__ import annotations
from typing import Dict, Any

from .llm import responses_json_schema
from .schemas import ParsedQuery

PARSED_QUERY_SCHEMA: Dict[str, Any] = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "intent": {
      "type": "string",
      "enum": [
        "TOTAL_SALES",
        "TOTAL_ACTIVE_STORES",
        "BREAKDOWN",
        "COMPARE_YOY",
        "TOP_N",
        "PDF_COMPARE",
        "CLARIFICATION_REQUIRED",
        "UNSUPPORTED"
      ]
    },
    "metric": {"type": ["string","null"], "enum": ["sales","active_stores", None]},
    "filters": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "brand": {"type": ["string","null"]},
        "category": {"type": ["string","null"]},
        "product": {"type": ["string","null"]},
        "region": {"type": ["string","null"]},

        "country": {"type": ["string","null"]},
        "city": {"type": ["string","null"]},
        "area": {"type": ["string","null"]},

        "channel": {"type": ["string","null"]},
        "sub_channel": {"type": ["string","null"]},

        "salesman": {"type": ["string","null"]},

        "customer": {"type": ["string","null"]},
        "customer_account_name": {"type": ["string","null"]},

        "retailer_group": {"type": ["string","null"]},
        "retailer_sub_group": {"type": ["string","null"]},

        "master_distributor": {"type": ["string","null"]},
        "distributor": {"type": ["string","null"]},
        "line_of_business": {"type": ["string","null"]},
        "supplier": {"type": ["string","null"]},
        "agency": {"type": ["string","null"]},
        "segment": {"type": ["string","null"]},
        "sub_brand": {"type": ["string","null"]},
        "promo": {"type": ["string","null"]},

        "month": {"type": ["string","null"], "description": "YYYY-MM"},
        "months": {"type": ["array","null"], "items": {"type": "string"}, "description": "List of YYYY-MM"},
        "year": {"type": ["integer","null"]},
        "quarter": {"type": ["string","null"], "description": "YYYY-Q#"}
      },
      "required": [
        "brand","category","product","region",
        "country","city","area",
        "channel","sub_channel",
        "salesman",
        "customer","customer_account_name",
        "retailer_group","retailer_sub_group",
        "master_distributor","distributor","line_of_business","supplier","agency","segment","sub_brand","promo",
        "month","months","year","quarter"
      ]
    },
    "group_by": {
      "type": ["string","null"],
      "enum": [
        "brand","category","product","region","country","city","area",
        "channel","sub_channel","salesman",
        "customer","customer_account_name",
        "retailer_group","retailer_sub_group",
        "master_distributor","distributor","line_of_business","supplier","agency","segment","sub_brand","promo",
        "month",
        None
      ]
    },
    "limit": {"type": ["integer","null"], "minimum": 1, "maximum": 50},
    "compare_to": {"type": ["string","null"], "enum": ["same_period_last_year", None]},
    "clarification_question": {"type": ["string","null"]}
  },
  "required": ["intent","metric","filters","group_by","limit","compare_to","clarification_question"]
}

PARSER_INSTRUCTIONS = """You are a strict query parser for a business analytics assistant.
Convert the user's question into a JSON plan that matches the provided schema.

Rules:
- NEVER compute or estimate any numbers.
- NEVER invent filter values. Only extract values explicitly mentioned by the user.
- Use intent=CLARIFICATION_REQUIRED if the user asks something but misses required time or grouping details.
- Choose intent:
  - TOTAL_SALES: total sales for given filters/time
  - TOTAL_ACTIVE_STORES: total active stores (unique invoiced stores with sales>0) for given filters/time
  - BREAKDOWN: grouped summary by group_by
  - TOP_N: top N by metric (requires group_by and limit)
  - COMPARE_YOY: compare vs same period last year (requires exactly one time unit: month OR quarter OR year)
  - PDF_COMPARE: when user asks to compare PO vs PI PDFs
  - UNSUPPORTED: outside scope
- If user asks for multiple months (e.g. "Jan, Mar and Apr 2024"), put them into filters.months as ["2024-01","2024-03","2024-04"].
- If user asks for month-wise breakdown, use intent=BREAKDOWN and group_by="month".
- If user asks "sales by salesman", group_by="salesman" (unless they asked a single salesman filter).
- metric:
  - sales => metric="sales"
  - active stores / unique stores invoiced => metric="active_stores"

Output ONLY valid JSON that matches the schema.
"""

def parse_question_to_plan(question: str) -> ParsedQuery:
    prompt = f"""{PARSER_INSTRUCTIONS}

User question:
{question}
"""
    data = responses_json_schema(prompt, PARSED_QUERY_SCHEMA, schema_name="ParsedQuery")
    return ParsedQuery.model_validate(data)
