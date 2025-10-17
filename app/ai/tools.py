"""Tool JSON Schemas aligned with Pydantic models."""
from __future__ import annotations

from typing import Dict, Any


def get_tool_names() -> list[str]:
    """Return list of available tool names."""
    return [
        "budget_scan",
        "add_to_groceries",
        "update_grocery_status",
        "create_task",
        "update_task_status",
        "create_event",
        "list_calendar_events",
        "list_tasks",
        "list_groceries",
        "get_transactions",
    ]


def tool_schemas() -> Dict[str, Dict[str, Any]]:
    """Return OpenAI tool schemas for Chat Completions API."""
    return {
        "budget_scan": {
            "type": "function",
            "function": {
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
            }
        },
        "add_to_groceries": {
            "type": "function",
            "function": {
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
            }
        },
        "update_grocery_status": {
            "type": "function",
            "function": {
                "name": "update_grocery_status",
                "description": "Update a grocery item status. Accepts either a UUID or a 1-based index (e.g., '1' for first item).",
                "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "UUID of the grocery item, or a 1-based numeric index as a string (e.g., '1', '2', '3'). Prefer using the UUID from list results when available."
                    },
                    "status": {"type": "string", "enum": ["Needed", "Added", "Ordered"]},
                },
                "required": ["id", "status"],
                "additionalProperties": False,
                },
            }
        },
        "create_task": {
            "type": "function",
            "function": {
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
            }
        },
        "update_task_status": {
            "type": "function",
            "function": {
                "name": "update_task_status",
                "description": "Update a task status. Accepts either a UUID or a 1-based index (e.g., '1' for first task).",
                "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "UUID of the task, or a 1-based numeric index as a string (e.g., '1', '2', '3'). Prefer using the UUID from list results when available."
                    },
                    "status": {"type": "string", "enum": ["Not Started", "In Progress", "Done"]},
                },
                "required": ["id", "status"],
                "additionalProperties": False,
                },
            }
        },
        "create_event": {
            "type": "function",
            "function": {
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
            }
        },
        "list_calendar_events": {
            "type": "function",
            "function": {
                "name": "list_calendar_events",
                "description": "Read upcoming Google Calendar events within a date window. Returns events with id, summary, start/end times, and location. Defaults to showing next 7 days if no dates specified.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_dt": {"type": "string", "description": "ISO8601 datetime (optional, defaults to now)"},
                        "to_dt": {"type": "string", "description": "ISO8601 datetime (optional, defaults to now + 7 days)"},
                        "max_results": {"type": "integer", "minimum": 1, "maximum": 250, "default": 50}
                    },
                    "additionalProperties": False
                }
            }
        },
        "list_tasks": {
            "type": "function",
            "function": {
                "name": "list_tasks",
                "description": "List tasks with optional status filter. Returns tasks with both idx (1-based index for easy reference like 'task 1') and id (UUID for updates). Use the id field when calling update_task_status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "done", "archived"],
                            "description": "Filter by task status (optional)"
                        },
                        "limit": {"type": "integer", "minimum": 1, "maximum": 250, "default": 50}
                    },
                    "additionalProperties": False
                }
            }
        },
        "list_groceries": {
            "type": "function",
            "function": {
                "name": "list_groceries",
                "description": "List grocery items with optional status filter. Returns items with both idx (1-based index for easy reference like 'item 1') and id (UUID for updates). Use the id field when calling update_grocery_status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["needed", "in_cart", "purchased"],
                            "description": "Filter by grocery status (optional)"
                        },
                        "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 100}
                    },
                    "additionalProperties": False
                }
            }
        },
        "get_transactions": {
            "type": "function",
            "function": {
                "name": "get_transactions",
                "description": "Fetch real bank transactions from Open Banking API. Returns recent spending data with merchant names, amounts, categories, and timestamps. Use this to answer questions about spending habits, budgets, and financial patterns.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Bank account ID to fetch transactions from (optional - if not provided, uses first available account)"
                        },
                        "from_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (optional, defaults to 90 days ago)"
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (optional, defaults to today)"
                        }
                    },
                    "additionalProperties": False
                }
            }
        },
    }


