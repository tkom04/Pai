# Tool Execution Flow Diagram

## Complete Request Flow with Correlation ID Tracing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ User types: "Add milk to groceries"
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (localhost:3000)                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  AiChat.tsx                                                       │  │
│  │  - Sends POST to /ai/respond                                      │  │
│  │  - Opens SSE connection                                           │  │
│  │  - Body: {"prompt": "...", "mode": "tools+chat"}                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTP POST + SSE
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKEND (localhost:8080)                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  app/ai/router.py :: _stream_response()                          │  │
│  │                                                                   │  │
│  │  1. Generate correlation_id = "abc-123"                          │  │
│  │     LOG: "Starting AI stream response" [correlation_id: abc-123] │  │
│  │                                                                   │  │
│  │  2. Build messages with SYSTEM_PROMPT                            │  │
│  │     messages = [                                                  │  │
│  │       {"role": "system", "content": SYSTEM_PROMPT},              │  │
│  │       {"role": "user", "content": "Add milk to groceries"}       │  │
│  │     ]                                                             │  │
│  │                                                                   │  │
│  │  3. Get tool schemas (7 tools)                                   │  │
│  │     tools = list(tool_schemas().values())                        │  │
│  │     LOG: "Registered 7 tools" [correlation_id: abc-123]          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Call OpenAI API
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPENAI API                                       │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Model: gpt-4o-mini                                               │  │
│  │  - Receives system prompt with tool instructions                  │  │
│  │  - Receives user message                                          │  │
│  │  - Has access to 7 tool schemas                                   │  │
│  │                                                                   │  │
│  │  Decision: Use tool "add_to_groceries"                           │  │
│  │  Arguments: {"item": "milk", "qty": 1}                           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Returns tool_calls in stream
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKEND - Tool Processing                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  app/ai/router.py :: _stream_response() [continued]              │  │
│  │                                                                   │  │
│  │  4. Receive tool_calls from stream                               │  │
│  │     LOG: "Model requested 1 tool call(s)" [correlation_id]       │  │
│  │                                                                   │  │
│  │  5. Validate tool call structure                                 │  │
│  │     ✓ Has ID: "call_abc123"                                      │  │
│  │     ✓ Has function name: "add_to_groceries"                      │  │
│  │     ✓ Has arguments: '{"item":"milk","qty":1}'                   │  │
│  │                                                                   │  │
│  │  6. Emit SSE: {"type": "tool.status", "state": "started"}       │  │
│  │     LOG: "Executing tool" [correlation_id, tool_name]            │  │
│  │                                                                   │  │
│  │  7. Parse arguments                                               │  │
│  │     args = {"item": "milk", "qty": 1}                            │  │
│  │     LOG: "Parsed tool arguments" [correlation_id]                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Call dispatch_tool()
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    TOOL RUNTIME DISPATCHER                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  app/ai/tool_runtime.py :: dispatch_tool()                       │  │
│  │                                                                   │  │
│  │  8. Check tool exists in TOOL_DISPATCH                           │  │
│  │     ✓ "add_to_groceries" found                                   │  │
│  │     LOG: "Tool start" [correlation_id, tool_name, args]          │  │
│  │                                                                   │  │
│  │  9. Call _run_add_to_groceries(args)                             │  │
│  │     - Validate with Pydantic: AddToGroceriesRequest              │  │
│  │     - ✓ item: "milk" (string, required)                          │  │
│  │     - ✓ qty: 1 (integer, default)                                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Call service
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  app/services/groceries.py :: add_item()                         │  │
│  │                                                                   │  │
│  │  10. Create item in Notion database                              │  │
│  │      - Item: "milk"                                               │  │
│  │      - Qty: 1                                                     │  │
│  │      - Status: "Needed"                                           │  │
│  │                                                                   │  │
│  │  11. Return response                                              │  │
│  │      {"ok": true, "id": "notion-id-123", "item": "milk"}        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Success response
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    TOOL RUNTIME - Return                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  app/ai/tool_runtime.py :: dispatch_tool() [continued]           │  │
│  │                                                                   │  │
│  │  12. Success!                                                     │  │
│  │      LOG: "Tool finished" [correlation_id, tool_result: success] │  │
│  │      Return: {"ok": true, "id": "...", "item": "milk"}          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Result as JSON string
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKEND - Continue Stream                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  app/ai/router.py :: _stream_response() [continued]              │  │
│  │                                                                   │  │
│  │  13. Emit SSE: {"type": "tool.status", "state": "finished"}     │  │
│  │      LOG: "Tool execution successful" [correlation_id]           │  │
│  │                                                                   │  │
│  │  14. Add tool result to messages                                 │  │
│  │      messages.append({                                            │  │
│  │        "role": "tool",                                            │  │
│  │        "tool_call_id": "call_abc123",                            │  │
│  │        "content": '{"ok": true, ...}'                            │  │
│  │      })                                                            │  │
│  │                                                                   │  │
│  │  15. Call OpenAI again with tool result                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Second OpenAI call
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPENAI API (Round 2)                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Model receives tool result                                       │  │
│  │  Generates natural language response:                             │  │
│  │  "I've added milk to your grocery list."                         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Stream response text
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKEND - Stream to Frontend                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  16. Stream text deltas via SSE                                  │  │
│  │      {"type": "text.delta", "content": "I've "}                  │  │
│  │      {"type": "text.delta", "content": "added "}                 │  │
│  │      {"type": "text.delta", "content": "milk "}                  │  │
│  │      {"type": "text.delta", "content": "to your grocery list."} │  │
│  │      {"type": "done"}                                             │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ SSE events
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND - Display Response                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  AiChat.tsx                                                       │  │
│  │  - Accumulates text deltas                                        │  │
│  │  - Shows tool status indicators                                   │  │
│  │  - Displays final message:                                        │  │
│  │    "I've added milk to your grocery list."                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                            USER SEES RESULT ✓
```

## Error Flow (If Tool Execution Fails)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Tool Execution Error Scenario                         │
└─────────────────────────────────────────────────────────────────────────┘

If step 11 (Service Layer) fails:
  │
  ├─► Service throws error
  │
  ├─► tool_runtime catches exception
  │
  ├─► Creates ToolExecutionError with:
  │     - error_type: "validation_error" | "not_found" | etc.
  │     - details: {...context...}
  │
  ├─► LOG: "Tool execution error" [correlation_id, error_type]
  │
  ├─► Returns structured error:
  │     {"ok": false, "error": "...", "error_type": "...", "details": {...}}
  │
  ├─► router.py logs error with full context
  │
  ├─► Error passed to OpenAI as tool result
  │
  ├─► OpenAI generates apologetic response:
  │     "I wasn't able to add that item. The error was: ..."
  │
  └─► User sees friendly error message
```

## Correlation ID Tracing Example

**Search logs for correlation_id="550e8400-e29b-41d4-a716-446655440000":**

```
[INFO ] correlation_id=550e8400 | Starting AI stream response
[INFO ] correlation_id=550e8400 | Registered 7 tools for this request
[INFO ] correlation_id=550e8400 | Model requested 1 tool call(s)
[INFO ] correlation_id=550e8400 | tool_name=add_to_groceries | Executing tool
[INFO ] correlation_id=550e8400 | tool_name=add_to_groceries | Parsed tool arguments
[INFO ] correlation_id=550e8400 | tool_name=add_to_groceries | Tool start
[INFO ] correlation_id=550e8400 | tool_name=add_to_groceries | Tool finished
[INFO ] correlation_id=550e8400 | tool_name=add_to_groceries | Tool execution successful
```

**Every line has the same correlation_id → full request trace!**

## Key Improvements Visualized

### Before: Silent Failure
```
User → Frontend → Backend → OpenAI → ??? → Error (no details)
                                      ↓
                                 [BLACK BOX]
```

### After: Full Visibility
```
User → Frontend → Backend → OpenAI → Tool Validation → Dispatcher → Service
         ↓           ↓         ↓            ↓              ↓           ↓
      Display    Log Start  Log Tools   Log Validate   Log Execute  Log Result
                    ↓         ↓            ↓              ↓           ↓
              correlation_id is the same everywhere → Full Trace
```

## Component Responsibilities

| Component | Responsibility | Logging |
|-----------|---------------|---------|
| **Frontend** | User interaction, SSE display | Browser console |
| **router.py** | Request orchestration, OpenAI calls | Start, tools, iterations |
| **tool_runtime.py** | Tool dispatch, validation | Execution, errors |
| **Service Layer** | Business logic, database | Service-specific |
| **OpenAI** | Intent recognition, response generation | N/A |

## Health Check Flow

```
curl /ai/tools/health
        ↓
app/main.py :: ai_tools_health()
        ↓
Check: tool_schemas()     → Returns 7 tools
       TOOL_DISPATCH      → Has 7 tools
       Compare names      → All match ✓
        ↓
Return: {"status": "healthy", ...}
```

---

**This flow diagram shows exactly how tool invocation works with full tracing!**

