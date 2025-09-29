"""Tool JSON Schemas aligned with Pydantic models."""
from __future__ import annotations

from typing import Dict, Any


def tool_schemas() -> Dict[str, Dict[str, Any]]:
    """Return OpenAI tool schemas for Responses API."""
    return {
        "budget_scan": {
            "type": "function",
            "name": "budget_scan",
            "description": "Scan budget summarizing categories and buffer for a date period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "object",
                        "properties": {
                            "from": {"type": "string", "description": "YYYY-MM-DD"},
                            "to": {"type": "string", "description": "YYYY-MM-DD"},
                        },
                        "required": ["from", "to"],
                    },
                    "source": {
                        "type": "string",
                        "enum": ["csv", "notion"],
                        "default": "csv",
                    },
                    "path": {"type": "string"},
                },
                "required": ["period"],
                "additionalProperties": False,
            },
        },
        "add_to_groceries": {
            "type": "function",
            "name": "add_to_groceries",
            "description": "Add an item to the groceries list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "qty": {"type": "integer", "minimum": 1, "default": 1},
                    "notes": {"type": "string"},
                },
                "required": ["item"],
                "additionalProperties": False,
            },
        },
        "update_grocery_status": {
            "type": "function",
            "name": "update_grocery_status",
            "description": "Update a grocery item status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "status": {"type": "string", "enum": ["Needed", "Added", "Ordered"]},
                },
                "required": ["id", "status"],
                "additionalProperties": False,
            },
        },
        "create_task": {
            "type": "function",
            "name": "create_task",
            "description": "Create a task in the tasks list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "due": {"type": "string", "description": "ISO8601 date-time"},
                    "context": {"type": "string"},
                    "priority": {"type": "string", "enum": ["Low", "Med", "High"], "default": "Med"},
                },
                "required": ["title", "due"],
                "additionalProperties": False,
            },
        },
        "update_task_status": {
            "type": "function",
            "name": "update_task_status",
            "description": "Update a task status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "status": {"type": "string", "enum": ["Not Started", "In Progress", "Done"]},
                },
                "required": ["id", "status"],
                "additionalProperties": False,
            },
        },
        "create_event": {
            "type": "function",
            "name": "create_event",
            "description": "Create a calendar event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start": {"type": "string", "description": "ISO8601 date-time"},
                    "end": {"type": "string", "description": "ISO8601 date-time"},
                    "description": {"type": "string"},
                },
                "required": ["title", "start", "end"],
                "additionalProperties": False,
            },
        },
        "ha_service_call": {
            "type": "function",
            "name": "ha_service_call",
            "description": "Call a Home Assistant service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string"},
                    "service": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "data": {"type": "object"},
                },
                "required": ["domain", "service"],
                "additionalProperties": False,
            },
        },
    }


