"""Runtime dispatcher for AI tool calls with validation."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Callable, Awaitable
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
    pass


def _validate(model: type[BaseModel], args: Dict[str, Any]) -> BaseModel:
    try:
        return model.model_validate(args)
    except ValidationError as e:
        raise ToolExecutionError(f"Invalid arguments: {e}")


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
        raise ToolExecutionError("Missing required field 'id'")
    validated = _validate(UpdateGroceryStatusRequest, {"status": args.get("status")})
    ok = await groceries_service.update_item_status(item_id, validated.status)
    if not ok:
        raise ToolExecutionError("Grocery item not found")
    return {"ok": True, "id": item_id, "status": validated.status}


async def _run_create_task(args: Dict[str, Any]) -> Dict[str, Any]:
    validated = _validate(CreateTaskRequest, args)
    result = await tasks_service.create_task(validated)
    return result.model_dump()  # type: ignore[attr-defined]


async def _run_update_task_status(args: Dict[str, Any]) -> Dict[str, Any]:
    task_id = args.get("id")
    if not task_id:
        raise ToolExecutionError("Missing required field 'id'")
    validated = _validate(UpdateTaskStatusRequest, {"status": args.get("status")})
    ok = await tasks_service.update_task_status(task_id, validated.status)
    if not ok:
        raise ToolExecutionError("Task not found")
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


async def dispatch_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Run a tool by name with validated args."""
    if name not in TOOL_DISPATCH:
        raise ToolExecutionError("Tool not allowed")
    safe_args = mask_secrets(arguments)
    logger.info(f"Tool start: {name}", extra={"tool": name, "args": safe_args})
    try:
        result = await TOOL_DISPATCH[name](arguments)
        logger.info(f"Tool finished: {name}", extra={"tool": name})
        return result
    except ToolExecutionError:
        raise
    except Exception as e:
        raise ToolExecutionError(str(e))


