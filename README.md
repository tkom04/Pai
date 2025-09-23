# Personal AI Assistant (PAI)

A centralized household operations API that integrates with Notion, Google Calendar, and Home Assistant to manage budgets, groceries, tasks, and home automation.

## Features

- **Budget Management**: CSV parsing and categorization with spending analysis
- **Grocery Lists**: Add and manage shopping items
- **Task Management**: Create and track household tasks
- **Calendar Integration**: Create events visible on FamilyWall via Google Calendar
- **Home Automation**: Control Home Assistant devices and services
- **Scheduled Jobs**: Automated morning briefs, budget checks, and weekly reports

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
# - APP_API_KEY: Secure API key for authentication
# - NOTION_API_KEY: Your Notion integration token
# - GOOGLE_CALENDAR_ID: Your Google Calendar ID
# - HA_TOKEN: Home Assistant long-lived access token
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 3. Docker Deployment

```bash
# Build the image
docker build -t personal-ai .

# Run with environment file
docker run -d -p 8080:8080 --env-file .env personal-ai
```

## API Endpoints

All endpoints require the `x-api-key` header except `/healthz`.

### Core Endpoints

- `GET /ping` - Health check with authentication
- `GET /healthz` - Health check without authentication (for Cloudflare Tunnel)
- `POST /budget_scan` - Analyze spending for a date period
- `POST /add_to_groceries` - Add items to shopping list
- `POST /create_task` - Create a new task
- `POST /create_event` - Create a calendar event
- `POST /ha_service_call` - Call Home Assistant service

### Example Usage

```bash
# Health check
curl -H "x-api-key: your-api-key" http://localhost:8080/ping

# Add groceries
curl -X POST -H "x-api-key: your-api-key" -H "Content-Type: application/json" \
  -d '{"item":"milk","qty":2,"notes":"semi-skimmed"}' \
  http://localhost:8080/add_to_groceries

# Create event
curl -X POST -H "x-api-key: your-api-key" -H "Content-Type: application/json" \
  -d '{"title":"Dentist","start":"2025-02-01T16:00:00+01:00","end":"2025-02-01T16:30:00+01:00"}' \
  http://localhost:8080/create_event
```

## Architecture

```
[AI Client] → [PAI FastAPI] → [Notion] [Google Calendar] [Home Assistant]
                                      ↓
                                 [FamilyWall Display]
```

## Development Status

- ✅ **Phase 1**: FastAPI skeleton with authentication
- ✅ **Phase 2**: Core endpoints with stub implementations
- 🔄 **Phase 3**: Real integrations (Notion, Google Calendar, HA)
- ⏳ **Phase 4**: Scheduled jobs and automations
- ⏳ **Phase 5**: Production deployment and monitoring

## Project Structure

```
personal-ai/
├── app/
│   ├── main.py              # FastAPI application
│   ├── deps.py              # Dependencies and clients
│   ├── models.py            # Pydantic models
│   ├── services/            # Business logic
│   │   ├── budgets.py
│   │   ├── groceries.py
│   │   ├── tasks.py
│   │   ├── calendar.py
│   │   └── ha.py
│   ├── jobs/                # Scheduled jobs (Phase 4)
│   └── util/                # Utilities
│       ├── logging.py
│       └── time.py
├── data/
│   └── sample_transactions.csv
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## Next Steps

1. **Phase 3**: Implement real Notion, Google Calendar, and Home Assistant integrations
2. **Phase 4**: Add APScheduler for automated jobs
3. **Phase 5**: Deploy to Raspberry Pi with Cloudflare Tunnel
4. **Future**: MCP server integration for broader AI tool compatibility

## License

Private project - All rights reserved.
