"""Runtime dispatcher for AI tool calls with validation."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Callable, Awaitable, Optional
from pydantic import BaseModel, ValidationError

from ..models import (
    BudgetScanRequest,
    AddToGroceriesRequest,
    UpdateGroceryStatusRequest,
    CreateTaskRequest,
    UpdateTaskStatusRequest,
    CreateEventRequest,
    HAServiceCallRequest,
)
from ..services.budgets import budget_service
from ..services.groceries import groceries_service
from ..services.tasks import tasks_service
from ..services.calendar import calendar_service
from ..services.ha import ha_service
from ..util.logging import logger, mask_secrets


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


async def _run_budget_scan(args: Dict[str, Any]) -> Dict[str, Any]:
    validated = _validate(BudgetScanRequest, args)
    result = await budget_service.scan_budget(validated)
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_add_to_groceries(args: Dict[str, Any]) -> Dict[str, Any]:
    validated = _validate(AddToGroceriesRequest, args)
    result = await groceries_service.add_item(validated)
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_update_grocery_status(args: Dict[str, Any]) -> Dict[str, Any]:
    item_id = args.get("id")
    if not item_id:
        raise ToolExecutionError(
            "Missing required field 'id'",
            error_type="missing_parameter",
            details={"required_field": "id", "provided_args": args}
        )
    validated = _validate(UpdateGroceryStatusRequest, {"status": args.get("status")})
    ok = await groceries_service.update_item_status(item_id, validated.status)
    if not ok:
        raise ToolExecutionError(
            f"Grocery item with id '{item_id}' not found",
            error_type="not_found",
            details={"item_id": item_id}
        )
    return {"ok": True, "id": item_id, "status": validated.status}


async def _run_create_task(args: Dict[str, Any]) -> Dict[str, Any]:
    validated = _validate(CreateTaskRequest, args)
    result = await tasks_service.create_task(validated)
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_update_task_status(args: Dict[str, Any]) -> Dict[str, Any]:
    task_id = args.get("id")
    if not task_id:
        raise ToolExecutionError(
            "Missing required field 'id'",
            error_type="missing_parameter",
            details={"required_field": "id", "provided_args": args}
        )
    validated = _validate(UpdateTaskStatusRequest, {"status": args.get("status")})
    ok = await tasks_service.update_task_status(task_id, validated.status)
    if not ok:
        raise ToolExecutionError(
            f"Task with id '{task_id}' not found",
            error_type="not_found",
            details={"task_id": task_id}
        )
    return {"ok": True, "id": task_id, "status": validated.status}


async def _run_create_event(args: Dict[str, Any]) -> Dict[str, Any]:
    validated = _validate(CreateEventRequest, args)
    result = await calendar_service.create_event(validated)
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_ha_service_call(args: Dict[str, Any]) -> Dict[str, Any]:
    validated = _validate(HAServiceCallRequest, args)
    result = await ha_service.call_service(validated)
    return result.model_dump()  # type: ignore[attr-defined]


TOOL_DISPATCH: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
    "budget_scan": _run_budget_scan,
    "add_to_groceries": _run_add_to_groceries,
    "update_grocery_status": _run_update_grocery_status,
    "create_task": _run_create_task,
    "update_task_status": _run_update_task_status,
    "create_event": _run_create_event,
    "ha_service_call": _run_ha_service_call,
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


