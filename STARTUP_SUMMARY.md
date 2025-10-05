# 🚀 Startup Fix Summary

## What Was Fixed

### ❌ Problem: Notion API Key Error
The application was failing to start with:
```
ValueError: NOTION_API_KEY not configured
```

### ✅ Solution: Made Notion Integration Optional

**Changes Made to `app/deps.py`:**

1. **Removed Hard Requirement**
   - Old: Raised `ValueError` if key missing
   - New: Prints warning and continues startup

2. **Added Client Validation**
   - Each Notion method now checks if client is initialized
   - Returns HTTP 503 with helpful message if not configured
   - Server starts successfully even without Notion key

3. **Better Error Messages**
   ```python
   if not self.client:
       raise HTTPException(
           status_code=503,
           detail="Notion API not configured. Set NOTION_API_KEY in .env file."
       )
   ```

**Now you can:**
- ✅ Start server without Notion configured
- ✅ Test other features (OpenAI, Google Calendar)
- ✅ Add Notion key later and restart
- ✅ See helpful error messages when trying to use Notion without key

---

## Startup Scripts Created

Three easy-to-use startup scripts that handle everything:

### 1. **`start.ps1`** (Windows PowerShell)
```powershell
.\start.ps1
```

**Features:**
- Checks Python and Node.js installation
- Installs dependencies automatically
- Starts backend on port 8080
- Starts frontend on port 3000
- Shows colorful status output
- Stops all services with Ctrl+C

### 2. **`start.bat`** (Windows Batch)
```cmd
start.bat
```

**Features:**
- Opens services in separate windows
- Services keep running independently
- Opens API docs in browser automatically
- Great for non-technical users

### 3. **`start.sh`** (Linux/macOS)
```bash
./start.sh
```

**Features:**
- Checks prerequisites with colored output
- Installs dependencies if needed
- Manages both services
- Graceful shutdown with Ctrl+C

---

## How to Use

### First Time Setup

1. **Check your `.env` file exists:**
   ```bash
   # If missing, create from example
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   - At minimum, add `APP_API_KEY` and `OPENAI_API_KEY`
   - Notion and Google Calendar are optional for initial testing

3. **Run the startup script:**

   **Windows PowerShell:**
   ```powershell
   .\start.ps1
   ```

   **Windows CMD:**
   ```cmd
   start.bat
   ```

   **Linux/macOS:**
   ```bash
   ./start.sh
   ```

4. **Wait for services to start:**
   - Backend: http://localhost:8080/docs
   - Frontend: http://localhost:3000

### What You'll See

**✅ With Notion Key Configured:**
```
✓ Python found: Python 3.11.5
✓ Node.js found: v20.10.0
✓ Python dependencies installed
✓ Backend starting on http://localhost:8080
```

**⚠️ Without Notion Key:**
```
✓ Python found: Python 3.11.5
⚠️  WARNING: NOTION_API_KEY not configured. Notion features will not work.
✓ Backend starting on http://localhost:8080
```

**The server will start in both cases!**

---

## What Works Without Notion

Even without Notion configured, you can:

- ✅ Access API docs at `/docs`
- ✅ Test OpenAI streaming at `/ai/respond`
- ✅ Use Google Calendar integration
- ✅ Test OAuth flow at `/auth/google`
- ✅ Check health at `/healthz`

**Notion endpoints will return HTTP 503** with this message:
```json
{
  "detail": "Notion API not configured. Set NOTION_API_KEY in .env file."
}
```

---

## Adding Notion Later

When you're ready to add Notion:

1. **Get your Notion API key:**
   - Visit https://www.notion.so/my-integrations
   - Create integration
   - Copy the API key

2. **Add to `.env`:**
   ```bash
   NOTION_API_KEY=ntn_your_key_here
   NOTION_DB_TASKS=your-tasks-db-id
   NOTION_DB_GROCERIES=your-groceries-db-id
   NOTION_DB_BUDGETS=your-budgets-db-id
   ```

3. **Restart the server:**
   - Press Ctrl+C to stop
   - Run the startup script again
   - Notion features now work!

---

## Troubleshooting

### PowerShell Execution Policy Error

**Error:**
```
start.ps1 cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

**Error:**
```
Python is not installed or not in PATH
```

**Solution:**
1. Install Python from https://www.python.org/downloads/
2. Check "Add Python to PATH" during installation
3. Restart terminal

### Node.js Not Found

**Warning:**
```
Node.js is not installed or not in PATH
```

**Solution:**
- If you only need the backend, ignore this warning
- To use frontend, install Node.js from https://nodejs.org/
- The startup script will automatically detect it

### Port Already in Use

**Error:**
```
[ERROR] Address already in use
```

**Solution:**

**Windows:**
```powershell
netstat -ano | findstr :8080
taskkill /PID <process_id> /F
```

**Linux/macOS:**
```bash
lsof -ti:8080 | xargs kill -9
```

---

## Documentation Files

Comprehensive guides created:

1. **STARTUP_GUIDE.md** - Detailed startup script documentation
2. **STARTUP_SUMMARY.md** - This file (quick reference)
3. **SETUP_GUIDE.md** - Complete external service setup
4. **API_REFERENCE.md** - API endpoint reference
5. **IMPLEMENTATION_NOTES.md** - Technical implementation details

---

## What Changed in Code

### File: `app/deps.py`

**Before:**
```python
def __init__(self):
    self.api_key = os.getenv("NOTION_API_KEY")
    if not self.api_key:
        raise ValueError("NOTION_API_KEY not configured")  # ❌ FAILS HERE
    self.client = NotionClient(auth=self.api_key)
```

**After:**
```python
def __init__(self):
    self.api_key = os.getenv("NOTION_API_KEY")

    # Only initialize client if API key is present
    if self.api_key:
        self.client = NotionClient(auth=self.api_key)
    else:
        self.client = None  # ✅ STARTS SUCCESSFULLY
        print("⚠️  WARNING: NOTION_API_KEY not configured. Notion features will not work.")
```

**All Notion methods now check:**
```python
async def some_notion_method(self):
    if not self.client:
        raise HTTPException(
            status_code=503,
            detail="Notion API not configured. Set NOTION_API_KEY in .env file."
        )
    # ... rest of method
```

---

## Testing the Fix

### Test 1: Start Without Notion
```bash
# Remove Notion key from .env (or leave it blank)
.\start.ps1
```

**Expected:** Server starts with warning, no error

### Test 2: Try Notion Endpoint
```bash
curl -H "x-api-key: your-key" http://localhost:8080/tasks
```

**Expected:** HTTP 503 with helpful error message

### Test 3: Add Notion Key and Restart
```bash
# Add NOTION_API_KEY to .env
.\start.ps1
```

**Expected:** Server starts without warning, Notion works

---

## Success! ✅

Your Personal AI Assistant can now:
- ✅ Start without all API keys configured
- ✅ Give helpful error messages
- ✅ Support gradual configuration
- ✅ Work with just OpenAI initially
- ✅ Easy startup with automated scripts

**Next steps:**
1. Run `.\start.ps1` (or `./start.sh` on Unix)
2. Visit http://localhost:8080/docs
3. Test the AI at `/ai/respond`
4. Configure other services when ready

---

*Fixed: October 4, 2025*
