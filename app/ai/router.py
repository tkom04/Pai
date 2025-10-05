"""AI router: Chat Completions API SSE streaming with tool-calling."""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from openai import OpenAI

from ..deps import get_api_key, get_openai_client, settings
from ..util.logging import logger, mask_secrets, generate_correlation_id
from .tools import tool_schemas
from .tool_runtime import dispatch_tool, ToolExecutionError


router = APIRouter(prefix="/ai", tags=["ai"])


# System prompt to instruct the model on tool usage
SYSTEM_PROMPT = """You are a helpful personal AI assistant with access to tools for managing:
- Budget tracking (budget_scan) - scan and analyze budget data for a date period
- Grocery lists (add_to_groceries, update_grocery_status) - add items and update their status
- Tasks (create_task, update_task_status) - create and manage tasks
- Calendar events (create_event) - create calendar events
- Home automation (ha_service_call) - control Home Assistant devices and services

When users request these actions, use the appropriate tools with the correct parameters. After tool execution completes successfully, confirm what was done in a natural, conversational way. Be specific about what was created or updated."""


async def _sse_yield(data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _stream_response(
    *,
    client: OpenAI,
    prompt: str,
    history: Optional[List[Dict[str, Any]]] = None,
    mode: str = "tools+chat",
) -> AsyncGenerator[str, None]:
    # Generate correlation ID for tracking this request
    correlation_id = generate_correlation_id()

    logger.info(
        f"Starting AI stream response",
        extra={
            "correlation_id": correlation_id,
            "prompt_length": len(prompt),
            "mode": mode,
            "has_history": bool(history)
        }
    )

    # Build messages with system prompt
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    # Get tool schemas if tool mode is enabled
    tool_schemas_dict = tool_schemas() if mode == "tools+chat" else None
    tools = list(tool_schemas_dict.values()) if tool_schemas_dict else None

    if tools:
        logger.info(
            f"Registered {len(tools)} tools for this request",
            extra={
                "correlation_id": correlation_id,
                "tool_count": len(tools),
                "tool_names": list(tool_schemas_dict.keys()) if tool_schemas_dict else []
            }
        )

    max_iterations = 5  # Prevent infinite tool call loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        try:
            # Create streaming chat completion with tools
            stream = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                tools=tools,
                temperature=0.3,
                stream=True,
                timeout=settings.OPENAI_REQUEST_TIMEOUT_S,
            )

            accumulated_content = ""
            tool_calls = []
            current_tool_call = None

            # Process the stream
            for chunk in stream:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta
                finish_reason = choice.finish_reason

                # Handle content deltas
                if delta.content:
                    accumulated_content += delta.content
                    yield await _sse_yield({"type": "text.delta", "content": delta.content})

                # Handle tool call deltas
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        idx = tool_call_delta.index

                        # Initialize new tool call
                        if idx >= len(tool_calls):
                            tool_calls.append({
                                "id": tool_call_delta.id or "",
                                "type": "function",
                                "function": {
                                    "name": "",
                                    "arguments": ""
                                }
                            })

                        # Accumulate tool call data
                        if tool_call_delta.id:
                            tool_calls[idx]["id"] = tool_call_delta.id
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_calls[idx]["function"]["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                tool_calls[idx]["function"]["arguments"] += tool_call_delta.function.arguments

                # Check if we need to execute tool calls
                if finish_reason == "tool_calls" and tool_calls:
                    logger.info(
                        f"Model requested {len(tool_calls)} tool call(s)",
                        extra={
                            "correlation_id": correlation_id,
                            "tool_count": len(tool_calls),
                            "iteration": iteration
                        }
                    )

                    # Validate tool calls before adding to messages
                    valid_tool_calls = []
                    for tc in tool_calls:
                        if not tc.get("id"):
                            logger.warning(
                                "Tool call missing ID, skipping",
                                extra={"correlation_id": correlation_id, "tool_call": tc}
                            )
                            continue
                        if not tc.get("function", {}).get("name"):
                            logger.warning(
                                "Tool call missing function name, skipping",
                                extra={"correlation_id": correlation_id, "tool_call": tc}
                            )
                            continue
                        valid_tool_calls.append(tc)

                    if not valid_tool_calls:
                        logger.error(
                            "No valid tool calls found",
                            extra={"correlation_id": correlation_id}
                        )
                        yield await _sse_yield({
                            "type": "error",
                            "content": "Tool invocation failed: no valid tool calls"
                        })
                        break

                    # Add assistant message with tool calls to history
                    messages.append({
                        "role": "assistant",
                        "content": accumulated_content if accumulated_content else None,
                        "tool_calls": valid_tool_calls
                    })

                    # Execute each tool call
                    for tool_call in valid_tool_calls:
                        name = tool_call["function"]["name"]
                        args_str = tool_call["function"]["arguments"]
                        tool_call_id = tool_call["id"]

                        logger.info(
                            f"Executing tool: {name}",
                            extra={
                                "correlation_id": correlation_id,
                                "tool_name": name,
                                "tool_call_id": tool_call_id,
                                "args_raw": args_str[:200]  # Log first 200 chars
                            }
                        )

                        yield await _sse_yield({"type": "tool.status", "name": name, "state": "started"})

                        try:
                            args = json.loads(args_str) if args_str else {}
                            logger.info(
                                f"Parsed tool arguments",
                                extra={
                                    "correlation_id": correlation_id,
                                    "tool_name": name,
                                    "tool_args": mask_secrets(args)
                                }
                            )
                            result = await dispatch_tool(name, args, correlation_id)
                            result_str = json.dumps(result)
                            logger.info(
                                f"Tool execution successful: {name}",
                                extra={
                                    "correlation_id": correlation_id,
                                    "tool_name": name,
                                    "result_length": len(result_str)
                                }
                            )
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Failed to parse tool arguments: {name}",
                                extra={
                                    "correlation_id": correlation_id,
                                    "tool_name": name,
                                    "error": str(e),
                                    "args_str": args_str
                                }
                            )
                            result_str = json.dumps({
                                "ok": False,
                                "error": f"Invalid JSON arguments: {str(e)}",
                                "error_type": "json_parse_error"
                            })
                        except ToolExecutionError as e:
                            logger.error(
                                f"Tool execution failed: {name}",
                                extra={
                                    "correlation_id": correlation_id,
                                    "tool_name": name,
                                    "error": str(e),
                                    "error_type": e.error_type
                                }
                            )
                            result_str = json.dumps(e.to_dict())
                        except Exception as e:
                            logger.error(
                                f"Unexpected error during tool execution: {name}",
                                extra={
                                    "correlation_id": correlation_id,
                                    "tool_name": name,
                                    "error": str(e)
                                },
                                exc_info=True
                            )
                            result_str = json.dumps({
                                "ok": False,
                                "error": f"Unexpected error: {str(e)}",
                                "error_type": "unexpected_error"
                            })

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": result_str
                        })

                        yield await _sse_yield({"type": "tool.status", "name": name, "state": "finished"})

                    # Break to continue with next iteration (tool response)
                    break

                # If response is complete without tool calls, we're done
                if finish_reason == "stop":
                    yield await _sse_yield({"type": "done"})
                    return

        except Exception as e:
            logger.error(
                f"OpenAI API error",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "iteration": iteration
                },
                exc_info=True
            )
            raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")

    # If we've exhausted iterations, yield done
    logger.warning(
        f"Max iterations ({max_iterations}) reached",
        extra={"correlation_id": correlation_id}
    )
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


@router.post("/conversation")
async def conversation(
    body: Dict[str, Any],
    api_key: str = Depends(get_api_key),
) -> Dict[str, Any]:
    """Non-streaming conversation endpoint for compatibility."""
    prompt = body.get("message") or body.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise HTTPException(status_code=422, detail="Missing 'message' or 'prompt' as non-empty string")

    history = body.get("history")
    client = get_openai_client()

    # Collect all streamed responses
    full_response = ""
    async for chunk_str in _stream_response(client=client, prompt=prompt, history=history, mode="tools+chat"):
        # Parse SSE data
        if chunk_str.startswith("data: "):
            try:
                chunk_data = json.loads(chunk_str[6:])
                if chunk_data.get("type") == "text.delta":
                    full_response += chunk_data.get("content", "")
            except json.JSONDecodeError:
                pass

    return {"response": full_response}


