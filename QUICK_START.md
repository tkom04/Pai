
# 🚀 Quick Start - Personal AI Assistant

## Fastest Way to Start

**Just run this command:**

```powershell
.\start.ps1
```

**That's it!** 🎉

---

## What It Does

The script automatically:
1. ✅ Checks Python and Node.js are installed
2. ✅ Installs all dependencies
3. ✅ Starts backend on http://localhost:8080
4. ✅ Starts frontend on http://localhost:3000
5. ✅ Shows you where to access the services

---

## Expected Output

```
================================================
  Personal AI Assistant - Starting Services
================================================

Checking prerequisites...
✓ Python found: Python 3.11.5
✓ Node.js found: v20.10.0

⚠️  WARNING: NOTION_API_KEY not configured. Notion features will not work.

Checking Python dependencies...
✓ Python dependencies already installed

================================================
Starting Backend (FastAPI)...
================================================

✓ Backend starting on http://localhost:8080
  - API Docs: http://localhost:8080/docs
  - Health Check: http://localhost:8080/healthz

================================================
  All services started successfully!
================================================

Backend API: http://localhost:8080/docs

Press Ctrl+C to stop all services
```

---

## Access Your Services

Once started:

### 🔧 Backend API
- **Docs**: http://localhost:8080/docs
- **Health**: http://localhost:8080/healthz
- **OAuth Status**: http://localhost:8080/auth/google/status

### 🎨 Frontend (if Node.js installed)
- **Dashboard**: http://localhost:3000

---

## Stop Services

Press **Ctrl+C** in the terminal running the script.

All services will stop gracefully.

---

## Common Issues

### ❌ "Execution Policy Error"

**Error:**
```
start.ps1 cannot be loaded because running scripts is disabled
```

**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1
```

### ⚠️ "NOTION_API_KEY not configured"

**This is just a warning!** The server will start fine.

- Notion features won't work yet
- OpenAI and Google Calendar will work
- Add Notion key later (see SETUP_GUIDE.md)

### ❌ "Python is not installed"

1. Download from https://python.org/downloads/
2. During install, check "Add Python to PATH"
3. Restart terminal
4. Run `.\start.ps1` again

### ❌ "Port 8080 already in use"

**Find and kill the process:**
```powershell
# Find process
netstat -ano | findstr :8080

# Kill it (replace <PID> with the number from above)
taskkill /PID <PID> /F

# Or restart your computer
```

---

## What You Can Do Now

### 1. Test the AI
Visit http://localhost:8080/docs

Try the `/ai/respond` endpoint:
```json
{
  "prompt": "Hello! What can you help me with?",
  "mode": "tools+chat"
}
```

### 2. Set Up Google Calendar
Visit: http://localhost:8080/auth/google

Follow the OAuth flow to connect your calendar.

### 3. Add Notion (Optional)
1. Get API key from https://www.notion.so/my-integrations
2. Add to `.env`:
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
3. Restart with `.\start.ps1`

---

## Need More Help?

- **Full Setup**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **API Reference**: See [API_REFERENCE.md](API_REFERENCE.md)
- **Troubleshooting**: See [STARTUP_GUIDE.md](STARTUP_GUIDE.md)

---

## ⚡ You're Done!

Your Personal AI Assistant is running and ready to use at:

**http://localhost:8080/docs**

Start exploring! 🎉
