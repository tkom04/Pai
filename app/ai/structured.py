"""Structured response helpers for JSON output formats."""
from __future__ import annotations

from typing import Dict, Any


def json_schema_response(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Build strict response_format for OpenAI Responses API."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema.get("name", "structured_output"),
            "schema": schema["schema"],
            "strict": True,
        },
    }


