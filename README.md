# Personal AI Assistant (PAI)

A centralized household operations API powered by OpenAI GPT-4o-mini that integrates with Notion, Google Calendar, and Home Assistant to intelligently manage budgets, groceries, tasks, and home automation.

## 🚀 Features

- **🤖 AI-Powered Assistance**: OpenAI GPT-4o-mini with streaming responses and function calling
- **📝 Notion Integration**: Full CRUD operations for tasks, groceries, and budgets with dynamic database discovery
- **📅 Google Calendar OAuth**: Complete OAuth2 flow with secure token management and event CRUD
- **💰 Budget Management**: CSV parsing and categorization with spending analysis
- **🛒 Grocery Lists**: Intelligent shopping list management synced with Notion
- **✅ Task Management**: Create, track, and update household tasks
- **🏠 Home Automation**: Control Home Assistant devices and services (optional)
- **🔄 Combined Workflows**: AI creates tasks → Notion pages → Calendar events in one conversation

## 📚 Documentation

- **[Complete Setup Guide](SETUP_GUIDE.md)** - Detailed configuration for all integrations
- **[API Documentation](http://localhost:8080/docs)** - Interactive Swagger UI (when running)

## ⚡ Quick Start

### Option 1: Use Startup Scripts (Easiest! 🚀)

**Windows:**
```powershell
.\start.ps1
```

**Linux/macOS:**
```bash
./start.sh
```

**That's it!** The script will:
- ✅ Check prerequisites
- ✅ Install dependencies
- ✅ Start backend and frontend
- ✅ Open API docs in browser

See [STARTUP_GUIDE.md](STARTUP_GUIDE.md) for details.

---

### Option 2: Manual Setup

### 1. Prerequisites

- Python 3.9+
- OpenAI API key
- Notion workspace with integration
- Google Cloud project with Calendar API enabled

### 2. Installation

```bash
# Clone and navigate to project
cd personal-ai

# Install dependencies (no venv needed with startup scripts)
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file (see [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions):

```bash
# Required
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini

NOTION_API_KEY=ntn_your-token-here
NOTION_DB_TASKS=your-tasks-db-id
NOTION_DB_GROCERIES=your-groceries-db-id
NOTION_DB_BUDGETS=your-budgets-db-id

GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback

APP_API_KEY=your-secure-random-key
```

### 4. Run the Application

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 5. Complete Google OAuth

1. Visit: http://localhost:8080/auth/google
2. Copy the `authorization_url` and open in browser
3. Grant Calendar access
4. You'll be redirected back (authentication complete!)

### 6. Test It Out

Visit http://localhost:8080/docs and try:

```json
{
  "prompt": "Create a task 'Buy groceries' for tomorrow and add it to my calendar at 2 PM",
  "mode": "tools+chat"
}
```

The AI will automatically:
1. Create a Notion task page
2. Create a Google Calendar event
3. Confirm completion in natural language

## 🔌 API Endpoints

All endpoints require `x-api-key` header except `/healthz` and OAuth endpoints.

### AI Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/respond` | Stream AI responses with tool calling (SSE) |
| POST | `/ai/chat` | Alias for `/ai/respond` |

**AI Streaming Example:**
```bash
curl -N -H "x-api-key: your-key" -H "Content-Type: application/json" \
  -X POST http://localhost:8080/ai/respond \
  -d '{"prompt":"remind me to call mom tomorrow at 3pm","mode":"tools+chat"}'
```

**SSE Event Types:**
- `{"type":"text.delta","content":"..."}` - AI response text
- `{"type":"tool.status","name":"create_task","state":"started"}` - Tool execution
- `{"type":"done"}` - Stream complete

### Google OAuth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/google` | Get OAuth authorization URL |
| GET | `/auth/google/callback` | OAuth callback handler |
| GET | `/auth/google/status` | Check authentication status |
| POST | `/auth/google/revoke` | Revoke OAuth token |

### Core Business Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ping` | Health check (authenticated) |
| GET | `/healthz` | Health check (public) |
| POST | `/budget_scan` | Analyze spending for date period |
| POST | `/add_to_groceries` | Add item to shopping list |
| GET | `/groceries` | List grocery items |
| PATCH | `/groceries/{id}` | Update grocery item status |
| POST | `/create_task` | Create a new task |
| GET | `/tasks` | List tasks |
| PATCH | `/tasks/{id}` | Update task status |
| POST | `/create_event` | Create calendar event (Google) |
| GET | `/events` | List calendar events |
| POST | `/ha_service_call` | Call Home Assistant service |
| GET | `/ha_entities` | List Home Assistant entities |

### Example: Combined Workflow

```bash
# The AI can chain multiple operations in one request
curl -N -H "x-api-key: your-key" -H "Content-Type: application/json" \
  -X POST http://localhost:8080/ai/respond \
  -d '{
    "prompt": "Create a task for the dentist appointment on Friday at 2pm, add it to my calendar, and remind me to bring my insurance card",
    "mode": "tools+chat"
  }'
```

This will:
1. ✅ Create Notion task: "Dentist appointment"
2. ✅ Create Calendar event: Friday 2pm
3. ✅ Add note about insurance card
4. ✅ Return natural language confirmation

## 🏗️ Architecture

```
┌─────────────┐
│   AI Chat   │ ← User conversation
└──────┬──────┘
       │
       ↓
┌──────────────────────────────────────────┐
│        PAI FastAPI Application           │
│  ┌────────────────────────────────────┐  │
│  │  OpenAI GPT-4o-mini               │  │
│  │  - Streaming responses             │  │
│  │  - Function/tool calling           │  │
│  │  - Context management              │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  Integration Layer                 │  │
│  │  - Notion Service (CRUD)           │  │
│  │  - Google Calendar (OAuth + API)   │  │
│  │  - Home Assistant Client           │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
       │         │            │
       ↓         ↓            ↓
   ┌──────┐  ┌────────┐  ┌───────────┐
   │Notion│  │ Google │  │   Home    │
   │  DB  │  │Calendar│  │ Assistant │
   └──────┘  └────────┘  └───────────┘
```

## ✅ Implementation Status (Oct 2025)

- ✅ **Phase 1**: FastAPI skeleton with authentication
- ✅ **Phase 2**: Core endpoints with models and validation
- ✅ **Phase 3**: Full integration implementations
  - ✅ OpenAI GPT-4o-mini with streaming & tool calling
  - ✅ Notion API with dynamic CRUD operations
  - ✅ Google Calendar OAuth2 + full event management
- ⏳ **Phase 4**: Scheduled jobs and automations
- ⏳ **Phase 5**: Production deployment and monitoring

## 📁 Project Structure

```
personal-ai/
├── app/
│   ├── main.py              # FastAPI application + OAuth endpoints
│   ├── deps.py              # Dependencies and service clients
│   ├── models.py            # Pydantic request/response models
│   ├── auth/                # Authentication modules
│   │   ├── __init__.py
│   │   └── google_oauth.py  # Google OAuth2 manager
│   ├── ai/                  # AI integration
│   │   ├── router.py        # OpenAI streaming endpoints
│   │   ├── tools.py         # Tool schemas for AI
│   │   └── tool_runtime.py  # Tool execution dispatcher
│   ├── services/            # Business logic
│   │   ├── budgets.py       # Budget analysis
│   │   ├── groceries.py     # Grocery list management
│   │   ├── tasks.py         # Task management
│   │   ├── calendar.py      # Google Calendar service
│   │   └── ha.py            # Home Assistant integration
│   ├── jobs/                # Scheduled jobs (Phase 4)
│   └── util/                # Utilities
│       ├── logging.py       # Structured logging
│       └── time.py          # Time utilities
├── data/
│   └── sample_transactions.csv
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── .env                    # Environment config (gitignored)
├── .gitignore
├── SETUP_GUIDE.md          # Complete setup instructions
└── README.md               # This file
```

## 🔮 Next Steps

1. ✅ **Phase 3 Complete**: All integrations fully implemented
2. ⏳ **Phase 4**: Scheduled Jobs
   - Morning briefing with weather, calendar, tasks
   - Weekly budget summary
   - Automated reminders
3. ⏳ **Phase 5**: Production Deployment
   - Docker containerization
   - Cloudflare Tunnel setup
   - Monitoring and alerting
4. 🔮 **Future Enhancements**:
   - MCP server for broader AI tool compatibility
   - Voice interface integration
   - Mobile app notifications
   - Advanced budget forecasting with ML

## 🔒 Security Notes

- **Never commit** `.env` to version control (already in `.gitignore`)
- **Rotate API keys** regularly
- **Monitor usage** at OpenAI and Google Cloud dashboards
- **Use HTTPS** in production
- **Restrict OAuth scopes** to minimum necessary
- **Set rate limits** on all endpoints in production

## 🐛 Troubleshooting

For detailed troubleshooting, see [SETUP_GUIDE.md](SETUP_GUIDE.md#troubleshooting).

Common issues:
- **"Not authenticated with Google Calendar"** → Complete OAuth flow at `/auth/google`
- **"Invalid API key"** → Check `.env` has correct OpenAI key
- **"Database not found"** → Verify Notion database IDs and sharing permissions
- **Port 8080 in use** → Change port: `uvicorn app.main:app --port 8000`

## 📊 Usage Examples

### Example 1: Simple Task Creation
**User:** "Add a task to water the plants tomorrow"

**AI Response:**
1. Creates Notion task: "Water the plants" (due: tomorrow)
2. Returns: "I've added a task to water the plants tomorrow. It's now in your Notion tasks database."

### Example 2: Combined Workflow
**User:** "Schedule a dentist appointment for next Friday at 2 PM and remind me to bring my insurance card"

**AI Response:**
1. Creates Notion task: "Dentist appointment" (due: next Friday, 2 PM)
2. Creates Google Calendar event: "Dentist appointment" (next Friday, 2-3 PM)
3. Adds note: "Bring insurance card"
4. Returns: "I've scheduled your dentist appointment for next Friday at 2 PM. I've added it to your calendar and created a task reminder to bring your insurance card."

### Example 3: Budget Analysis
**User:** "How much have I spent on food this month?"

**AI Response:**
1. Calls `budget_scan` tool with current month period
2. Analyzes food category spending
3. Returns: "This month you've spent $487 on food out of your $600 budget. You have $113 remaining (19% of budget)."

## 🤝 Contributing

This is a private project, but feedback and suggestions are welcome!

## 📝 License

Private project - All rights reserved.
