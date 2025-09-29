import asyncio
import pytest

from app.ai.tool_runtime import dispatch_tool, ToolExecutionError


@pytest.mark.asyncio
async def test_dispatch_add_to_groceries_happy():
    out = await dispatch_tool("add_to_groceries", {"item": "Milk", "qty": 2})
    assert out["ok"] is True
    assert out["id"]


@pytest.mark.asyncio
async def test_dispatch_update_grocery_status_missing_id():
    with pytest.raises(ToolExecutionError):
        await dispatch_tool("update_grocery_status", {"status": "Needed"})


@pytest.mark.asyncio
async def test_dispatch_unknown_tool():
    with pytest.raises(ToolExecutionError):
        await dispatch_tool("unknown", {})


