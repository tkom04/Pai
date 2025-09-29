"""AI router: Responses API SSE streaming with tool-calling."""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from openai import OpenAI

from ..deps import get_api_key, get_openai_client, settings
from ..util.logging import logger, mask_secrets
from .tools import tool_schemas
from .tool_runtime import dispatch_tool, ToolExecutionError


router = APIRouter(prefix="/ai", tags=["ai"])


async def _sse_yield(data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _stream_response(
    *,
    client: OpenAI,
    prompt: str,
    history: Optional[List[Dict[str, Any]]] = None,
    mode: str = "tools+chat",
) -> AsyncGenerator[str, None]:
    messages: List[Dict[str, Any]] = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    tools = tool_schemas() if mode == "tools+chat" else None

    stream = client.responses.stream(
        model=settings.OPENAI_MODEL,
        input=messages,
        tools=list(tools.values()) if tools else None,
        temperature=0.3,
        timeout=settings.OPENAI_REQUEST_TIMEOUT_S,
    )

    with stream as s:
        try:
            for event in s:
                et = event.type
                if et == "response.output_text.delta":
                    yield await _sse_yield({"type": "text.delta", "content": event.delta})
                elif et == "response.error":
                    raise HTTPException(status_code=502, detail=str(getattr(event, "error", "OpenAI error")))
                elif et == "response.required_action":
                    # Tool calls required
                    required = event.required_action
                    tool_outputs: List[Dict[str, Any]] = []
                    for call in required.submit_tool_outputs.tool_calls:
                        name = call.function.name
                        args = json.loads(call.function.arguments or "{}")
                        yield await _sse_yield({"type": "tool.status", "name": name, "state": "started"})
                        try:
                            result = await dispatch_tool(name, args)
                        except ToolExecutionError as e:
                            result = {"ok": False, "error": str(e)}
                        tool_outputs.append({"tool_call_id": call.id, "output": json.dumps(result)})
                        yield await _sse_yield({"type": "tool.status", "name": name, "state": "finished"})

                    # Submit outputs and continue
                    s = s  # keep type checker happy
                    s = s  # no-op; using same variable
                    stream_result = s.submit_tool_outputs(tool_outputs=tool_outputs)
                    for event2 in stream_result:
                        if event2.type == "response.output_text.delta":
                            yield await _sse_yield({"type": "text.delta", "content": event2.delta})
                        elif event2.type == "response.error":
                            raise HTTPException(status_code=502, detail=str(getattr(event2, "error", "OpenAI error")))
                elif et == "response.completed":
                    break
                else:
                    # ignore other event types to keep payload minimal
                    continue
        finally:
            yield await _sse_yield({"type": "done"})


@router.post("/respond")
async def respond(
    body: Dict[str, Any],
    api_key: str = Depends(get_api_key),
) -> EventSourceResponse:
    prompt = body.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise HTTPException(status_code=422, detail="Missing 'prompt' as non-empty string")
    history = body.get("history")
    mode = body.get("mode", "tools+chat")
    client = get_openai_client()

    async def event_generator():
        async for chunk in _stream_response(client=client, prompt=prompt, history=history, mode=mode):
            yield chunk

    return EventSourceResponse(event_generator())


@router.post("/chat")
async def chat(
    body: Dict[str, Any],
    api_key: str = Depends(get_api_key),
) -> EventSourceResponse:
    # Thin alias
    return await respond(body, api_key)  # type: ignore[arg-type]


