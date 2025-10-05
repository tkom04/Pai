# Testing Tool Invocation - Quick Reference

## Prerequisites

- Backend running on port 8080
- Frontend running on port 3000
- Valid API key in `.env`: `APP_API_KEY=dev-api-key-12345`
- Valid OpenAI API key configured

## Quick Test Commands

### 1. Health Check (Most Important First!)

```bash
curl http://localhost:8080/ai/tools/health \
  -H "X-API-Key: dev-api-key-12345"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "tools": {
    "total_schemas": 7,
    "total_dispatchers": 7
  },
  "test": "add_to_groceries function is accessible",
  "openai_api_key_configured": true
}
```

✅ If you see this, your tools are properly configured!

### 2. Test Grocery List Addition (Simplest Tool)

```bash
curl -N -X POST http://localhost:8080/ai/respond \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Accept: text/event-stream" \
  -d '{
    "prompt": "Add milk to my grocery list",
    "mode": "tools+chat"
  }'
```

**Watch for SSE Events:**
```
data: {"type":"tool.status","name":"add_to_groceries","state":"started"}
data: {"type":"tool.status","name":"add_to_groceries","state":"finished"}
data: {"type":"text.delta","content":"I've added "}
data: {"type":"text.delta","content":"milk "}
data: {"type":"text.delta","content":"to your grocery list"}
data: {"type":"done"}
```

### 3. Test Task Creation

```bash
curl -N -X POST http://localhost:8080/ai/respond \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Accept: text/event-stream" \
  -d '{
    "prompt": "Create a task to buy groceries due tomorrow",
    "mode": "tools+chat"
  }'
```

### 4. Test Calendar Event

```bash
curl -N -X POST http://localhost:8080/ai/respond \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Accept: text/event-stream" \
  -d '{
    "prompt": "Create a meeting tomorrow at 2pm for 1 hour",
    "mode": "tools+chat"
  }'
```

## Start the Backend

```bash
# Option 1: Direct Python
cd "C:\1 Projects\Orbit\Pai"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Option 2: Using your start script
.\start.ps1
```

## Watch the Logs

**What to Look For:**

✅ **Successful Tool Invocation:**
```json
{"level":"INFO","correlation_id":"abc-123","message":"Starting AI stream response"}
{"level":"INFO","correlation_id":"abc-123","message":"Registered 7 tools for this request"}
{"level":"INFO","correlation_id":"abc-123","message":"Model requested 1 tool call(s)"}
{"level":"INFO","correlation_id":"abc-123","tool_name":"add_to_groceries","message":"Executing tool"}
{"level":"INFO","correlation_id":"abc-123","tool_name":"add_to_groceries","message":"Parsed tool arguments"}
{"level":"INFO","correlation_id":"abc-123","tool_name":"add_to_groceries","message":"Tool execution successful"}
```

❌ **Failed Tool Invocation:**
```json
{"level":"ERROR","correlation_id":"abc-123","tool_name":"add_to_groceries","error_type":"validation_error"}
```

## Frontend Testing

1. **Start Frontend:**
```bash
cd "frontend copy"
npm run dev
```

2. **Open Browser:**
   - Navigate to `http://localhost:3000`
   - Login if required

3. **Test in Chat:**
   - Type: "Add milk to my grocery list"
   - Watch for confirmation message
   - Check backend logs for correlation_id

4. **Check Browser Console:**
   - Open DevTools → Network tab
   - Filter by "respond"
   - Click the SSE request
   - View EventStream tab to see tool events

## Common Test Scenarios

### Test 1: Simple Grocery Addition
**Prompt:** "Add eggs to my grocery list"
**Expected Tool:** `add_to_groceries`
**Expected Args:** `{"item": "eggs", "qty": 1}`

### Test 2: Grocery with Quantity
**Prompt:** "Add 2 cartons of milk to my grocery list"
**Expected Tool:** `add_to_groceries`
**Expected Args:** `{"item": "milk", "qty": 2, "notes": "cartons"}`

### Test 3: Task Creation
**Prompt:** "Create a high priority task to call the dentist due tomorrow"
**Expected Tool:** `create_task`
**Expected Args:** `{"title": "call the dentist", "due": "2025-10-06T...", "priority": "High"}`

### Test 4: Calendar Event
**Prompt:** "Schedule a team meeting on Monday at 10am for 30 minutes"
**Expected Tool:** `create_event`
**Expected Args:** Contains start, end times

### Test 5: Budget Scan
**Prompt:** "Show me my budget for October"
**Expected Tool:** `budget_scan`
**Expected Args:** `{"period": {"from": "2025-10-01", "to": "2025-10-31"}}`

## Debugging Failed Tool Calls

### Step 1: Check Health Endpoint
```bash
curl http://localhost:8080/ai/tools/health -H "X-API-Key: dev-api-key-12345"
```
- Verify `status: "healthy"`
- Check `total_schemas` and `total_dispatchers` match

### Step 2: Find Correlation ID
Look in backend logs for your request:
```
{"correlation_id":"550e8400-e29b-41d4-a716-446655440000","message":"Starting AI stream response"}
```

### Step 3: Trace Full Flow
Search logs for that correlation ID:
```bash
# Windows PowerShell
Select-String -Pattern "550e8400" -Path logs.txt

# Linux/Mac
grep "550e8400" logs.txt
```

### Step 4: Check Error Type
Look for `error_type` in logs:
- `validation_error` → Check tool arguments
- `tool_not_found` → Check tool name spelling
- `missing_parameter` → Required field not provided
- `not_found` → Item ID doesn't exist (for update operations)

### Step 5: Check OpenAI API Key
```bash
# In PowerShell from project directory
$env:OPENAI_API_KEY
```
Should show your API key (starts with `sk-proj-...`)

## Verification Checklist

Before declaring success, verify:

- [ ] Health endpoint returns "healthy"
- [ ] All 7 tools appear in health check
- [ ] Simple grocery addition works
- [ ] Backend logs show correlation IDs
- [ ] Tool execution logs show "success"
- [ ] Frontend displays confirmation message
- [ ] No error logs appear in backend
- [ ] OpenAI API key is valid and configured

## Expected Behavior

### ✅ Success Indicators
1. Tool status events in SSE stream
2. Confirmation message from AI
3. Logs show "Tool execution successful"
4. Item appears in database (Notion/Supabase)
5. No error-type fields in logs

### ❌ Failure Indicators
1. Generic error message to user
2. Missing tool.status events
3. Logs show error_type
4. No database entry created
5. 502 error from backend

## Performance Expectations

- Health check: < 100ms
- Tool invocation: 2-5 seconds (depends on OpenAI API)
- SSE stream start: < 500ms
- Total request (with tool): 3-8 seconds

## Troubleshooting Common Issues

### "Tool not found" error
- Check tool name matches in `tool_schemas()` and `TOOL_DISPATCH`
- Verify import statements in `app/main.py`

### "Invalid arguments" error
- Check Pydantic model in `app/models.py`
- Look at validation_errors in log details
- Verify required fields are provided

### No tool invocation at all
- Check system prompt is present
- Verify tools list passed to OpenAI (should be list, not dict)
- Check OpenAI API key is valid

### OpenAI API timeout
- Check network connectivity
- Verify API key hasn't hit rate limits
- Check OPENAI_REQUEST_TIMEOUT_S setting

---

**Quick Win Test:** Run the health check first - if that works, everything else should too!

