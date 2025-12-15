from __future__ import annotations
import json
from typing import Any, Dict, Optional

from openai import OpenAI
from .config import settings

_client: Optional[OpenAI] = None

def client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client

def responses_json_schema(prompt: str, schema: Dict[str, Any], schema_name: str = "Schema") -> Dict[str, Any]:
    """
    Calls the OpenAI Responses API with Structured Outputs (json_schema),
    returning parsed JSON as a Python dict.

    The model is instructed to return ONLY JSON matching the schema.
    """
    resp = client().responses.create(
        model=settings.openai_model,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        },
        # lower temperature keeps it deterministic
        temperature=0,
        max_output_tokens=800,
    )
    # The SDK provides output_text as a convenience (string)
    raw = resp.output_text.strip()
    return json.loads(raw)

def responses_text(prompt: str) -> str:
    resp = client().responses.create(
        model=settings.openai_model,
        input=prompt,
        temperature=0.2,
        max_output_tokens=600,
    )
    return resp.output_text
