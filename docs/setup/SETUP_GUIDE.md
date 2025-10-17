# Personal AI Assistant - Setup Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [OpenAI Setup](#openai-setup)
4. [Notion Integration Setup](#notion-integration-setup)
5. [Google Calendar OAuth Setup](#google-calendar-oauth-setup)
6. [Environment Configuration](#environment-configuration)
7. [Installation & Running](#installation--running)
8. [Testing the Integrations](#testing-the-integrations)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This Personal AI Assistant (PAI) integrates with:
- **OpenAI GPT-4o-mini** for intelligent conversation and tool calling
- **Notion** for task management, grocery lists, and budget tracking
- **Google Calendar** for event management with full OAuth2 authentication
- **Home Assistant** for smart home control (optional)

---

## Prerequisites

- Python 3.9 or higher
- pip package manager
- A modern web browser
- Active accounts for:
  - OpenAI (API access)
  - Notion (workspace with integration access)
  - Google Cloud Platform (for Calendar API)

---

## OpenAI Setup

### Step 1: Get Your API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to **API Keys** section
4. Click **"Create new secret key"**
5. Copy the key (it starts with `sk-proj-...`)
6. Add to your `.env` file:

```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
```

### Step 2: Verify Model Access

- The default model is `gpt-4o-mini` (recommended for cost-effectiveness)
- Ensure your OpenAI account has access to this model
- Alternative models: `gpt-4o`, `gpt-4-turbo`

### Important Notes:
- **Never commit** your API key to version control
- Monitor your usage at [OpenAI Usage Dashboard](https://platform.openai.com/usage)
- Set usage limits to prevent unexpected charges

---

## Notion Integration Setup

### Step 1: Create a Notion Integration

1. Visit [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Configure:
   - **Name**: Personal AI Assistant
   - **Associated workspace**: Choose your workspace
   - **Capabilities**:
     - ✅ Read content
     - ✅ Update content
     - ✅ Insert content
4. Click **"Submit"**
5. Copy the **Internal Integration Token** (starts with `secret_...` or `ntn_...`)

### Step 2: Create Notion Databases

You need three databases:

#### Tasks Database
1. Create a new database in Notion
2. Add these properties:
   - **Title** (Title)
   - **Due** (Date)
   - **Context** (Select: Home, Finance, Errand, Project)
   - **Priority** (Select: Low, Med, High)
   - **Status** (Select: Not Started, In Progress, Done)
3. Share the database with your integration

#### Groceries Database
1. Create a new database
2. Add these properties:
   - **Item** (Title)
   - **Qty** (Number)
   - **Notes** (Text)
   - **Status** (Select: Needed, Added, Ordered)
3. Share with your integration

#### Budgets Database
1. Create a new database
2. Add these properties:
   - **Category** (Select: Food, Transport, Entertainment, etc.)
   - **Cap** (Number)
   - **Spent** (Number)
   - **Delta** (Number)
   - **Status** (Select: OK, WARN)
   - **Month** (Date)
3. Share with your integration

### Step 3: Get Database IDs

1. Open each database in Notion
2. Click **"Share"** → **"Copy link"**
3. The database ID is the 32-character string in the URL:
   ```
   https://www.notion.so/{workspace}/{DATABASE_ID}?v=...
   ```
4. Add to `.env`:

```bash
NOTION_API_KEY=ntn_your-integration-token-here
NOTION_DB_TASKS=your-tasks-database-id
NOTION_DB_GROCERIES=your-groceries-database-id
NOTION_DB_BUDGETS=your-budgets-database-id
```

### Step 4: Share Databases with Integration

For each database:
1. Click **"..."** (more options) in top-right
2. Click **"Add connections"**
3. Select your "Personal AI Assistant" integration
4. Click **"Confirm"**

---

## Google Calendar OAuth Setup

### Step 1: Create Google Cloud Project

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Project name: `Personal AI Assistant`
4. Click **"Create"**

### Step 2: Enable Calendar API

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Calendar API"**
3. Click on it and click **"Enable"**

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** (unless you have Google Workspace)
3. Fill in required fields:
   - **App name**: Personal AI Assistant
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **"Save and Continue"**
5. **Scopes**: Click **"Add or Remove Scopes"**
   - Search and add: `https://www.googleapis.com/auth/calendar`
6. Click **"Save and Continue"**
7. **Test users**: Add your Google account email
8. Click **"Save and Continue"**

### Step 4: Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Web application"**
4. Name: `PAI Web Client`
5. **Authorized redirect URIs**: Add:
   ```
   http://localhost:8080/auth/google/callback
   http://127.0.0.1:8080/auth/google/callback
   ```
6. Click **"Create"**
7. Copy the **Client ID** and **Client Secret**

### Step 5: Configure Environment

Add to `.env`:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback
```

---

## Environment Configuration

### Complete .env Template

Create a `.env` file in your project root:

```bash
# API Security
APP_API_KEY=your-secure-random-api-key-here

# Supabase (if using)
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Notion Integration
NOTION_API_KEY=ntn_your-notion-integration-token
NOTION_DB_BUDGETS=your-budgets-database-id
NOTION_DB_TASKS=your-tasks-database-id
NOTION_DB_GROCERIES=your-groceries-database-id

# Google Calendar Integration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback
GOOGLE_CALENDAR_ID=primary

# OpenAI Integration
OPENAI_API_KEY=sk-proj-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_REASONING_EFFORT=medium
OPENAI_TEXT_VERBOSITY=medium
OPENAI_MAX_OUTPUT_TOKENS=800

# Home Assistant (optional)
HA_BASE_URL=http://homeassistant.local:8123
HA_TOKEN=your-home-assistant-long-lived-token

# Notion Page ID for MCP
NOTION_PAGE_ID=your-main-notion-page-id
```

---

## Installation & Running

### Step 1: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Verify Configuration

```bash
# Check that .env is properly configured
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OPENAI_API_KEY:', bool(os.getenv('OPENAI_API_KEY')))"
```

### Step 3: Run the Application

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Step 4: Access API Documentation

Open your browser:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

---

## Testing the Integrations

### Test OpenAI Integration

1. Open Swagger UI at http://localhost:8080/docs
2. Authorize with your `APP_API_KEY`
3. Test the `/ai/respond` endpoint:

```json
{
  "prompt": "Create a task called 'Buy groceries' due tomorrow",
  "mode": "tools+chat"
}
```

### Test Notion Integration

Create a task via API:

```bash
curl -X POST "http://localhost:8080/create_task" \
  -H "X-Api-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "due": "2025-10-05T10:00:00Z",
    "context": "Home",
    "priority": "Med"
  }'
```

### Test Google Calendar OAuth

1. **Initiate OAuth**: Visit http://localhost:8080/auth/google
2. **Response**: You'll get an `authorization_url`
3. **Authorize**: Open the URL in your browser
4. **Grant Access**: Click "Allow" for Calendar access
5. **Callback**: You'll be redirected back to your app
6. **Check Status**: http://localhost:8080/auth/google/status

```json
{
  "authenticated": true,
  "service": "Google Calendar"
}
```

7. **Create Event**:

```bash
curl -X POST "http://localhost:8080/create_event" \
  -H "X-Api-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "start": "2025-10-05T14:00:00Z",
    "end": "2025-10-05T15:00:00Z",
    "description": "Weekly sync"
  }'
```

### Test Combined Workflow (AI → Notion → Calendar)

Use the AI to create a task and schedule it:

```json
{
  "prompt": "Create a task 'Prepare presentation' for tomorrow at 2 PM and add it to my calendar",
  "mode": "tools+chat"
}
```

This should:
1. ✅ Create a Notion task page
2. ✅ Create a Google Calendar event
3. ✅ Return confirmation message

---

## Troubleshooting

### OpenAI Issues

**Error: "Invalid API key"**
- Verify your key starts with `sk-proj-`
- Check for extra spaces in `.env`
- Ensure key is active at platform.openai.com

**Error: "Model not found"**
- Verify model name is correct: `gpt-4o-mini`
- Check your account has access to the model

### Notion Issues

**Error: "NOTION_API_KEY not configured"**
- Ensure `.env` has `NOTION_API_KEY=ntn_...`
- Restart the server after updating `.env`

**Error: "Failed to create page"**
- Verify database ID is correct (32 characters)
- Check database is shared with integration
- Verify property names match exactly (case-sensitive)

### Google Calendar Issues

**Error: "Not authenticated with Google Calendar"**
- Complete OAuth flow via `/auth/google`
- Check `google_token.json` exists in project root
- Token may have expired - re-authenticate

**Error: "Failed to create calendar event"**
- Ensure Calendar API is enabled in Google Cloud
- Verify OAuth scopes include calendar access
- Check token hasn't been revoked

**OAuth redirect fails**
- Verify redirect URI matches exactly in Google Cloud Console
- Must be: `http://localhost:8080/auth/google/callback`
- Check firewall/antivirus isn't blocking port 8080

### General Issues

**Port 8080 already in use**
```bash
# Find process using port
# Windows:
netstat -ano | findstr :8080
# macOS/Linux:
lsof -i :8080

# Change port in startup command
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Dependencies fail to install**
```bash
# Update pip
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

---

## Important Notes

### OpenAI Tool Schema Requirements

The AI tool calling requires specific schema format. All tools are defined in `app/ai/tools.py` with:
- `type: "function"`
- `name`: Tool function name
- `description`: Clear description for AI
- `parameters`: JSON Schema with required fields

If adding new tools:
1. Update `app/ai/tools.py` with schema
2. Implement handler in `app/ai/tool_runtime.py`
3. Register in `TOOL_DISPATCH` dictionary

### Security Best Practices

1. **Never commit** `.env` to version control
2. **Use strong** random API keys
3. **Rotate tokens** regularly
4. **Monitor usage** of all APIs
5. **Restrict OAuth** scopes to minimum needed
6. **Use HTTPS** in production

### Production Deployment

For production deployment:
1. Update CORS settings in `app/main.py`
2. Use proper domain for Google OAuth redirect URI
3. Enable HTTPS/TLS
4. Set up proper logging and monitoring
5. Use environment-specific .env files
6. Consider rate limiting and authentication

---

## Support & Resources

- **OpenAI Docs**: https://platform.openai.com/docs
- **Notion API**: https://developers.notion.com/
- **Google Calendar API**: https://developers.google.com/calendar
- **FastAPI Docs**: https://fastapi.tiangolo.com/

For issues with this implementation, check:
- Application logs for detailed error messages
- API documentation at `/docs`
- Status endpoint: `/ping`

---

## Success Criteria

Your setup is complete when:
- ✅ `/ping` endpoint returns 200 OK
- ✅ `/auth/google/status` shows `authenticated: true`
- ✅ OpenAI streaming works in `/ai/respond`
- ✅ Notion pages are created successfully
- ✅ Google Calendar events are created
- ✅ Combined AI workflow creates task → calendar event

**Test with**: "Hey AI, remind me to call mom tomorrow at 3 PM and add it to my calendar"
