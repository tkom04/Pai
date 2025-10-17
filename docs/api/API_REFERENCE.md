# Personal AI Assistant - API Quick Reference

## Base URL
```
http://localhost:8080
```

## Authentication

All endpoints except `/healthz` and OAuth endpoints require API key authentication:

```bash
-H "x-api-key: your-api-key-here"
```

---

## AI Endpoints

### POST /ai/respond
Stream AI responses with tool calling (Server-Sent Events)

**Request Body:**
```json
{
  "prompt": "Create a task to call mom tomorrow at 3pm",
  "history": [],  // Optional: previous conversation history
  "mode": "tools+chat"  // or "chat-only"
}
```

**Response:** SSE Stream
```
data: {"type":"text.delta","content":"I'll"}
data: {"type":"text.delta","content":" create"}
data: {"type":"tool.status","name":"create_task","state":"started"}
data: {"type":"tool.status","name":"create_task","state":"finished"}
data: {"type":"text.delta","content":"Task created!"}
data: {"type":"done"}
```

**cURL Example:**
```bash
curl -N -H "x-api-key: YOUR_KEY" -H "Content-Type: application/json" \
  -X POST http://localhost:8080/ai/respond \
  -d '{"prompt":"Add milk to groceries","mode":"tools+chat"}'
```

---

## Google OAuth Endpoints

### GET /auth/google
Initiate OAuth flow

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

**Usage:**
1. Call this endpoint
2. Open `authorization_url` in browser
3. Grant permissions
4. Get redirected to callback

### GET /auth/google/callback
OAuth callback handler (automatic redirect)

**Query Parameters:**
- `code`: Authorization code from Google

**Response:** Redirects to `/?auth=success`

### GET /auth/google/status
Check authentication status

**Response:**
```json
{
  "authenticated": true,
  "service": "Google Calendar"
}
```

### POST /auth/google/revoke
Revoke OAuth token

**Response:**
```json
{
  "ok": true,
  "message": "Authentication revoked"
}
```

---

## Task Management

### POST /create_task
Create a new task in Notion

**Request Body:**
```json
{
  "title": "Buy groceries",
  "due": "2025-10-05T10:00:00Z",
  "context": "Home",  // Home, Finance, Errand, Project
  "priority": "Med"   // Low, Med, High
}
```

**Response:**
```json
{
  "ok": true,
  "notion_page_id": "abc123..."
}
```

### GET /tasks
List all tasks

**Response:**
```json
{
  "tasks": [
    {
      "id": "abc123",
      "title": "Buy groceries",
      "due": "2025-10-05T10:00:00Z",
      "status": "Not Started"
    }
  ]
}
```

### PATCH /tasks/{task_id}
Update task status

**Request Body:**
```json
{
  "status": "Done"  // Not Started, In Progress, Done
}
```

**Response:**
```json
{
  "ok": true,
  "id": "abc123",
  "status": "Done"
}
```

---

## Grocery List

### POST /add_to_groceries
Add item to shopping list

**Request Body:**
```json
{
  "item": "Milk",
  "qty": 2,
  "notes": "Semi-skimmed"
}
```

**Response:**
```json
{
  "ok": true,
  "id": "xyz789",
  "item": {
    "name": "Milk",
    "qty": 2,
    "status": "Needed"
  }
}
```

### GET /groceries
List grocery items

**Response:**
```json
{
  "items": [
    {
      "id": "xyz789",
      "item": "Milk",
      "qty": 2,
      "status": "Needed"
    }
  ]
}
```

### PATCH /groceries/{item_id}
Update grocery item status

**Request Body:**
```json
{
  "status": "Ordered"  // Needed, Added, Ordered
}
```

---

## Calendar Events

### POST /create_event
Create Google Calendar event

**Request Body:**
```json
{
  "title": "Team Meeting",
  "start": "2025-10-05T14:00:00Z",
  "end": "2025-10-05T15:00:00Z",
  "description": "Weekly sync"
}
```

**Response:**
```json
{
  "ok": true,
  "google_event_id": "abc123xyz"
}
```

### GET /events
List calendar events

**Query Parameters:**
- `start`: ISO datetime (optional)
- `end`: ISO datetime (optional)

**Response:**
```json
{
  "events": [
    {
      "id": "abc123xyz",
      "title": "Team Meeting",
      "start": "2025-10-05T14:00:00Z",
      "end": "2025-10-05T15:00:00Z",
      "html_link": "https://calendar.google.com/..."
    }
  ]
}
```

---

## Budget Management

### POST /budget_scan
Analyze spending for period

**Request Body:**
```json
{
  "period": {
    "from": "2025-10-01",
    "to": "2025-10-31"
  },
  "source": "csv",
  "path": "data/transactions.csv"
}
```

**Response:**
```json
{
  "period": {
    "from": "2025-10-01",
    "to": "2025-10-31"
  },
  "categories": [
    {
      "name": "Food",
      "cap": 600.0,
      "spent": 487.0,
      "delta": 113.0,
      "status": "OK"
    }
  ],
  "buffer_remaining": 450.0
}
```

---

## Home Assistant (Optional)

### POST /ha_service_call
Call Home Assistant service

**Request Body:**
```json
{
  "domain": "light",
  "service": "turn_on",
  "entity_id": "light.living_room",
  "data": {
    "brightness": 255
  }
}
```

**Response:**
```json
{
  "ok": true,
  "called": "light.turn_on",
  "entity_id": "light.living_room"
}
```

### GET /ha_entities
List Home Assistant entities

**Query Parameters:**
- `domain`: Filter by domain (optional)

---

## Health Checks

### GET /ping
Health check (requires authentication)

**Response:**
```json
{
  "status": "ok",
  "time": "2025-10-04T12:00:00Z",
  "version": "1.0.0"
}
```

### GET /healthz
Public health check (no authentication)

**Response:**
```json
{
  "status": "ok",
  "time": "2025-10-04T12:00:00Z"
}
```

---

## Error Responses

All endpoints return consistent error format:

**400 Bad Request:**
```json
{
  "error": "Invalid request",
  "hint": "Check request body format"
}
```

**401 Unauthorized:**
```json
{
  "error": "Invalid or missing API key"
}
```

**404 Not Found:**
```json
{
  "error": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "hint": "Check logs for details"
}
```

---

## Tool Calling (For AI)

Available tools that the AI can call:

1. **budget_scan** - Analyze spending
2. **add_to_groceries** - Add grocery item
3. **update_grocery_status** - Update grocery status
4. **create_task** - Create task
5. **update_task_status** - Update task status
6. **create_event** - Create calendar event
7. **ha_service_call** - Control smart home

Tool schemas are defined in `app/ai/tools.py`.

---

## Rate Limits

**Development:** No rate limits

**Production:** (To be implemented)
- 100 requests/minute per API key
- 10 AI requests/minute per API key
- 1000 requests/hour per API key

---

## WebSocket Support

Not currently implemented. All real-time communication uses Server-Sent Events (SSE).

---

## Interactive Documentation

When the server is running, access:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
