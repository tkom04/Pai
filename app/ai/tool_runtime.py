"""Runtime dispatcher for AI tool calls with validation."""
from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, Callable, Awaitable, Optional
from pydantic import BaseModel, ValidationError

from ..models import (
    BudgetScanRequest,
    AddToGroceriesRequest,
    UpdateGroceryStatusRequest,
    CreateTaskRequest,
    UpdateTaskStatusRequest,
    CreateEventRequest,
    ListCalendarEventsRequest,
    ListTasksRequest,
    ListGroceriesRequest,
    GetTransactionsRequest,
)
from ..services.budgets import budget_service
from ..services.groceries import groceries_service
from ..services.tasks import tasks_service
from ..services.calendar import calendar_service
from ..services.open_banking import open_banking_service
from ..auth.google_oauth import oauth_manager
from ..auth.open_banking import open_banking_oauth_manager
from ..util.logging import logger, mask_secrets


# UUID validation regex
_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")

def _is_uuid(s: str) -> bool:
    """Check if string is a valid UUID."""
    return isinstance(s, str) and bool(_UUID_RE.match(s))


# Grocery status mapping: human-readable → purchased boolean
_GROCERY_STATUS_TO_PURCHASED = {
    "needed": False,
    "added": False,      # still on list / in basket
    "ordered": True,     # consider complete/purchased
}


# Task status mapping: UI/human-readable → DB status
_TASK_UI_TO_DB = {
    "not started": "todo",
    "in progress": "in_progress",
    "done": "done",
    "completed": "done",
}


class ToolExecutionError(Exception):
    """Exception raised during tool execution with detailed context."""
    def __init__(self, message: str, error_type: str = "execution_error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to structured error dictionary."""
        return {
            "ok": False,
            "error": str(self),
            "error_type": self.error_type,
            "details": self.details
        }


def _validate(model: type[BaseModel], args: Dict[str, Any]) -> BaseModel:
    try:
        return model.model_validate(args)
    except ValidationError as e:
        errors = e.errors()
        raise ToolExecutionError(
            f"Invalid arguments: {errors[0]['msg']}",
            error_type="validation_error",
            details={"validation_errors": errors, "provided_args": args}
        )


async def _resolve_grocery_id(item_id: str, user_id: str) -> str:
    """
    Resolve grocery item ID: accepts UUID or numeric index (1-based).
    Returns the actual UUID from the database.
    """
    if _is_uuid(item_id):
        return item_id

    # Treat numeric string as 1-based index
    try:
        idx = int(item_id)
    except ValueError:
        raise ToolExecutionError(
            f"Invalid grocery id '{item_id}'. Provide a UUID or a numeric index (e.g., '1').",
            error_type="validation_error",
            details={"provided_id": item_id}
        )

    # Fetch items and resolve index
    items = await groceries_service.get_items(user_id)
    if idx < 1 or idx > len(items):
        raise ToolExecutionError(
            f"Grocery index {idx} out of range (valid: 1-{len(items) or 0}).",
            error_type="not_found",
            details={"index": idx, "total_items": len(items)}
        )

    return items[idx - 1]["id"]


async def _resolve_task_id(task_id: str, user_id: str) -> str:
    """
    Resolve task ID: accepts UUID or numeric index (1-based).
    Returns the actual UUID from the database.
    """
    if _is_uuid(task_id):
        return task_id

    # Treat numeric string as 1-based index
    try:
        idx = int(task_id)
    except ValueError:
        raise ToolExecutionError(
            f"Invalid task id '{task_id}'. Provide a UUID or a numeric index (e.g., '1').",
            error_type="validation_error",
            details={"provided_id": task_id}
        )

    # Fetch tasks and resolve index
    tasks = await tasks_service.get_tasks(user_id)
    if idx < 1 or idx > len(tasks):
        raise ToolExecutionError(
            f"Task index {idx} out of range (valid: 1-{len(tasks) or 0}).",
            error_type="not_found",
            details={"index": idx, "total_tasks": len(tasks)}
        )

    return tasks[idx - 1]["id"]


async def _run_budget_scan(args: Dict[str, Any]) -> Dict[str, Any]:
    validated = _validate(BudgetScanRequest, args)
    result = await budget_service.scan_budget(validated)
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_add_to_groceries(args: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    validated = _validate(AddToGroceriesRequest, args)
    result = await groceries_service.add_item(validated, user_id or "default-user")
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_update_grocery_status(args: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """Update grocery item status with smart ID resolution and status mapping."""
    item_id = args.get("id")
    if not item_id:
        raise ToolExecutionError(
            "Missing required field 'id'",
            error_type="missing_parameter",
            details={"required_field": "id", "provided_args": args}
        )

    # Validate status
    validated = _validate(UpdateGroceryStatusRequest, {"status": args.get("status")})

    # Map human-readable status → purchased boolean
    purchased = _GROCERY_STATUS_TO_PURCHASED.get(validated.status.lower())
    if purchased is None:
        # Fallback for unknown statuses (shouldn't happen with enum validation, but be safe)
        purchased = validated.status.lower() in ['added', 'purchased', 'done', 'ordered']

    # Resolve ID (UUID or numeric index)
    uid = await _resolve_grocery_id(item_id, user_id or "default-user")

    # Update item
    ok = await groceries_service.update_item_status(uid, user_id or "default-user", purchased)
    if not ok:
        raise ToolExecutionError(
            f"Grocery item with id '{uid}' not found",
            error_type="not_found",
            details={"item_id": uid, "original_id": item_id}
        )

    return {"ok": True, "id": uid, "status": validated.status}


async def _run_create_task(args: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    validated = _validate(CreateTaskRequest, args)
    result = await tasks_service.create_task(validated, user_id or "default-user")
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_update_task_status(args: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """Update task status with smart ID resolution and status mapping."""
    task_id = args.get("id")
    if not task_id:
        raise ToolExecutionError(
            "Missing required field 'id'",
            error_type="missing_parameter",
            details={"required_field": "id", "provided_args": args}
        )

    # Validate status
    validated = _validate(UpdateTaskStatusRequest, {"status": args.get("status")})

    # Map human-readable status → DB status
    db_status = _TASK_UI_TO_DB.get(validated.status.lower())
    if not db_status:
        raise ToolExecutionError(
            f"Invalid status '{validated.status}'. Valid statuses: Not Started, In Progress, Done",
            error_type="validation_error",
            details={"provided_status": validated.status, "valid_statuses": list(_TASK_UI_TO_DB.keys())}
        )

    # Resolve ID (UUID or numeric index)
    uid = await _resolve_task_id(task_id, user_id or "default-user")

    # Update task
    ok = await tasks_service.update_task_status(uid, user_id or "default-user", db_status)
    if not ok:
        raise ToolExecutionError(
            f"Task with id '{uid}' not found",
            error_type="not_found",
            details={"task_id": uid, "original_id": task_id}
        )

    return {"ok": True, "id": uid, "status": validated.status}


async def _run_create_event(args: Dict[str, Any]) -> Dict[str, Any]:
    validated = _validate(CreateEventRequest, args)
    result = await calendar_service.create_event(validated)
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_list_calendar_events(args: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """List calendar events with OAuth check."""
    validated = _validate(ListCalendarEventsRequest, args)

    # Check authentication
    uid = user_id or "default-user"
    is_auth = await oauth_manager.is_authenticated(uid)
    if not is_auth:
        raise ToolExecutionError(
            "Missing Google Calendar authorization. Please complete OAuth flow.",
            error_type="auth_required",
            details={"service": "google_calendar", "user_id": uid}
        )

    # Fetch events from calendar service
    items = await calendar_service.list_events(
        validated.from_dt,
        validated.to_dt,
        validated.max_results
    )

    return {"events": items}


async def _run_list_tasks(args: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """List tasks with idx+id pattern."""
    validated = _validate(ListTasksRequest, args)

    # Fetch tasks from service
    items = await tasks_service.list_tasks(
        user_id or "default-user",
        validated.status,
        validated.limit
    )

    return {"items": items}


async def _run_list_groceries(args: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """List grocery items with idx+id pattern."""
    validated = _validate(ListGroceriesRequest, args)

    # Fetch grocery items from service
    items = await groceries_service.list_items(
        user_id or "default-user",
        validated.status,
        validated.limit
    )

    return {"items": items}


async def _run_get_transactions(args: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """Fetch real bank transactions from Open Banking API."""
    # Check authentication
    uid = user_id or "default-user"
    is_auth = await open_banking_oauth_manager.is_authenticated(uid)
    if not is_auth:
        raise ToolExecutionError(
            "Missing Open Banking authorization. Please connect your bank first.",
            error_type="auth_required",
            details={"service": "open_banking", "user_id": uid}
        )

    # Get account_id - if not provided, use first available account
    account_id = args.get("account_id")
    if not account_id:
        accounts = await open_banking_service.get_stored_bank_accounts(uid)
        if not accounts:
            raise ToolExecutionError(
                "No bank accounts found. Please connect your bank first.",
                error_type="no_accounts",
                details={"user_id": uid}
            )
        account_id = accounts[0].provider_account_id

    # Validate with optional parameters
    validated = _validate(GetTransactionsRequest, {
        "account_id": account_id,
        "from_date": args.get("from_date"),
        "to_date": args.get("to_date")
    })

    # Fetch transactions in real-time
    transactions = await open_banking_service.get_transactions(
        user_id=uid,
        account_id=validated.account_id,
        from_date=validated.from_date,
        to_date=validated.to_date
    )

    # Convert to serializable format
    transactions_data = [tx.model_dump() for tx in transactions]

    return {
        "ok": True,
        "account_id": validated.account_id,
        "transactions": transactions_data,
        "count": len(transactions_data)
    }


async def _run_budget_refresh(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Refresh budget data by fetching and processing transactions."""
    try:
        import requests

        lookback_days = arguments.get("lookback_days", 90)

        # Call the budget refresh endpoint
        response = requests.post(
            "http://localhost:8080/api/budget/refresh",
            params={"lookback_days": lookback_days},
            timeout=60,
            headers={"X-API-Key": "your-api-key"}  # Add API key for authentication
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 409:
            return {
                "ok": False,
                "error": "refresh_in_progress",
                "message": "Budget refresh is already running. Please wait for it to complete."
            }
        else:
            raise Exception(f"Budget refresh failed: {response.text}")

    except Exception as e:
        logger.error(f"Failed to refresh budget: {e}", exc_info=True)
        raise ToolExecutionError(
            f"Failed to refresh budget data: {str(e)}",
            error_type="service_error"
        )


async def _run_get_budget_summary(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get budget summary for a specific period."""
    try:
        import requests

        period = arguments.get("period")
        params = {}
        if period:
            params["period"] = period

        # Call the budget summary endpoint
        response = requests.get(
            "http://localhost:8080/api/budget/summary",
            params=params,
            timeout=30,
            headers={"X-API-Key": "your-api-key"}  # Add API key for authentication
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            return {
                "ok": False,
                "error": "no_data",
                "message": "No budget data available. Please run budget_refresh first."
            }
        else:
            raise Exception(f"Budget summary failed: {response.text}")

    except Exception as e:
        logger.error(f"Failed to get budget summary: {e}", exc_info=True)
        raise ToolExecutionError(
            f"Failed to get budget summary: {str(e)}",
            error_type="service_error"
        )


async def _run_create_budget_category(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new budget category."""
    try:
        import requests

        # Validate required fields
        if not arguments.get("key") or not arguments.get("label") or not arguments.get("target"):
            raise ToolExecutionError(
                "Missing required fields: key, label, and target are required",
                error_type="validation_error"
            )

        # Call the create category endpoint
        response = requests.post(
            "http://localhost:8080/api/budget/categories",
            json=arguments,
            timeout=30,
            headers={"X-API-Key": "your-api-key"}  # Add API key for authentication
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Category creation failed: {response.text}")

    except Exception as e:
        logger.error(f"Failed to create budget category: {e}", exc_info=True)
        raise ToolExecutionError(
            f"Failed to create budget category: {str(e)}",
            error_type="service_error"
        )


async def _run_create_budget_rule(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new budget categorization rule."""
    try:
        import requests

        # Validate required fields
        if not arguments.get("category_key"):
            raise ToolExecutionError(
                "Missing required field: category_key is required",
                error_type="validation_error"
            )

        # Build matchers object
        matchers = {}
        if arguments.get("merchant"):
            matchers["merchant"] = arguments["merchant"]
        if arguments.get("description_contains"):
            matchers["description_contains"] = arguments["description_contains"]
        if arguments.get("amount_min") is not None:
            matchers["amount_min"] = arguments["amount_min"]
        if arguments.get("amount_max") is not None:
            matchers["amount_max"] = arguments["amount_max"]

        rule_data = {
            "category_key": arguments["category_key"],
            "priority": arguments.get("priority", 100),
            "matchers": matchers
        }

        # Call the create rule endpoint
        response = requests.post(
            "http://localhost:8080/api/budget/rules",
            json=rule_data,
            timeout=30,
            headers={"X-API-Key": "your-api-key"}  # Add API key for authentication
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Rule creation failed: {response.text}")

    except Exception as e:
        logger.error(f"Failed to create budget rule: {e}", exc_info=True)
        raise ToolExecutionError(
            f"Failed to create budget rule: {str(e)}",
            error_type="service_error"
        )


TOOL_DISPATCH: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
    "budget_scan": _run_budget_scan,
    "add_to_groceries": _run_add_to_groceries,
    "update_grocery_status": _run_update_grocery_status,
    "create_task": _run_create_task,
    "update_task_status": _run_update_task_status,
    "create_event": _run_create_event,
    "list_calendar_events": _run_list_calendar_events,
    "list_tasks": _run_list_tasks,
    "list_groceries": _run_list_groceries,
    "get_transactions": _run_get_transactions,
    "budget_refresh": _run_budget_refresh,
    "get_budget_summary": _run_get_budget_summary,
    "create_budget_category": _run_create_budget_category,
    "create_budget_rule": _run_create_budget_rule,
}


async def dispatch_tool(name: str, arguments: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
    """Run a tool by name with validated args."""
    if name not in TOOL_DISPATCH:
        raise ToolExecutionError(
            f"Tool '{name}' is not allowed or does not exist",
            error_type="tool_not_found",
            details={"tool_name": name, "available_tools": list(TOOL_DISPATCH.keys())}
        )

    safe_args = mask_secrets(arguments)
    logger.info(
        f"Tool start: {name}",
        extra={
            "tool_name": name,
            "tool_args": safe_args,
            "correlation_id": correlation_id
        }
    )

    try:
        result = await TOOL_DISPATCH[name](arguments)
        logger.info(
            f"Tool finished: {name}",
            extra={
                "tool_name": name,
                "tool_result": "success",
                "correlation_id": correlation_id
            }
        )
        return result
    except ToolExecutionError as e:
        logger.error(
            f"Tool execution error: {name} - {str(e)}",
            extra={
                "tool_name": name,
                "tool_result": "error",
                "error_type": e.error_type,
                "correlation_id": correlation_id
            }
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected tool error: {name} - {str(e)}",
            extra={
                "tool_name": name,
                "tool_result": "error",
                "correlation_id": correlation_id
            },
            exc_info=True
        )
        raise ToolExecutionError(
            f"Unexpected error: {str(e)}",
            error_type="unexpected_error",
            details={"exception_type": type(e).__name__}
        )


