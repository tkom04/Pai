# Personal AI Assistant - Startup Guide

## Quick Start Scripts

Three startup scripts are provided to make it easy to run both the backend and frontend without manually managing virtual environments.

---

## 🪟 Windows Users

### Option 1: PowerShell Script (Recommended)

**Run this command:**
```powershell
.\start.ps1
```

**Features:**
- ✅ Checks for Python and Node.js
- ✅ Installs dependencies automatically
- ✅ Starts backend and frontend
- ✅ Shows colorful output with status
- ✅ Stops all services with Ctrl+C

**If you get an execution policy error:**
```powershell
# Run this once to allow scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run the script
.\start.ps1
```

### Option 2: Batch File (Alternative)

**Double-click** `start.bat` or run:
```cmd
start.bat
```

**Features:**
- ✅ Opens services in separate windows
- ✅ Automatically opens API docs in browser
- ✅ Services keep running even if you close the main window

---

## 🐧 Linux / macOS Users

**Run this command:**
```bash
./start.sh
```

**Features:**
- ✅ Checks for Python and Node.js
- ✅ Installs dependencies automatically
- ✅ Starts backend and frontend
- ✅ Colorful terminal output
- ✅ Stops all services with Ctrl+C

**If permission denied:**
```bash
chmod +x start.sh
./start.sh
```

---

## What Each Script Does

### 1. **Checks Prerequisites**
- Verifies Python 3.9+ is installed
- Verifies Node.js is installed (optional for frontend)
- Shows version numbers

### 2. **Checks Configuration**
- Looks for `.env` file
- Warns if it's missing
- Creates template if `.env.example` exists

### 3. **Installs Dependencies**
- Installs Python packages from `requirements.txt`
- Installs Node.js packages from `frontend copy/package.json`
- Only installs if not already installed

### 4. **Starts Services**
- **Backend**: Runs on `http://localhost:8080`
  - API docs: `http://localhost:8080/docs`
  - Health check: `http://localhost:8080/healthz`
- **Frontend**: Runs on `http://localhost:3000` (if available)

### 5. **Monitors Services**
- Keeps both services running
- Shows log output in terminal
- Handles Ctrl+C gracefully
- Stops all services cleanly

---

## Troubleshooting

### ❌ "Python is not installed"

**Solution:**
1. Download Python 3.9+ from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart your terminal
4. Run the script again

### ❌ "Node.js is not installed"

**Solution:**
1. Download Node.js from https://nodejs.org/
2. Install LTS version (recommended)
3. Restart your terminal
4. Run the script again

**Note:** Node.js is only needed for the frontend. Backend will work without it.

### ❌ ".env file not found"

**Solution:**
1. Create a `.env` file in the project root
2. Copy the contents from `.env.example` (if it exists)
3. Fill in your actual API keys and credentials
4. See [SETUP_GUIDE.md](SETUP_GUIDE.md) for details

### ❌ "Failed to install dependencies"

**Solution:**
```bash
# Update pip first
python -m pip install --upgrade pip

# Try installing manually
pip install -r requirements.txt
```

### ❌ "Port 8080 already in use"

**Solution:**
```bash
# Windows - Find and kill process on port 8080
netstat -ano | findstr :8080
taskkill /PID <process_id> /F

# Linux/macOS - Find and kill process
lsof -ti:8080 | xargs kill -9
```

Or edit `start.ps1` / `start.bat` / `start.sh` and change port 8080 to another port (e.g., 8000).

### ❌ "PowerShell execution policy error"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

This is safe and only allows scripts you've created or downloaded.

### ⚠️ "NOTION_API_KEY not configured"

**This is just a warning, not an error!**

The server will start successfully. Notion features won't work until you:
1. Get your Notion API key from https://www.notion.so/my-integrations
2. Add it to your `.env` file:
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
3. Restart the server

### ⚠️ Services not stopping properly

**Solution:**

**Windows:**
```powershell
# Stop all Python processes
taskkill /F /IM python.exe

# Stop all Node processes
taskkill /F /IM node.exe
```

**Linux/macOS:**
```bash
# Stop all Python processes
pkill -f uvicorn

# Stop all Node processes
pkill -f "npm run dev"
```

---

## Manual Startup (Alternative)

If you prefer not to use the scripts:

### Backend Only
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Frontend Only
```bash
# Install dependencies
cd "frontend copy"
npm install

# Run frontend
npm run dev
```

---

## Development Mode

All scripts start services in **development mode** with:
- ✅ **Hot reload** - Changes automatically reload
- ✅ **Detailed logs** - See all request/response logs
- ✅ **Debug mode** - Better error messages

---

## Production Deployment

For production, don't use these startup scripts. Instead:

1. **Use Docker** (see `Dockerfile`)
2. **Use a process manager** (PM2, systemd, etc.)
3. **Use a reverse proxy** (nginx, Cloudflare Tunnel)
4. **Set environment variables** properly
5. **Disable debug mode**

See `SETUP_GUIDE.md` for production deployment details.

---

## Script Locations

- `start.ps1` - PowerShell script for Windows
- `start.bat` - Batch file for Windows
- `start.sh` - Shell script for Linux/macOS

---

## What Gets Installed

### Python Packages (Backend)
- FastAPI - Web framework
- Uvicorn - ASGI server
- OpenAI - AI integration
- Notion-client - Notion API
- Google Auth libraries - Calendar OAuth
- And more... (see `requirements.txt`)

### Node.js Packages (Frontend)
- Next.js - React framework
- React - UI library
- Tailwind CSS - Styling
- And more... (see `frontend copy/package.json`)

---

## Accessing the Services

Once started:

### Backend API
- **Base URL**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/healthz
- **OAuth Status**: http://localhost:8080/auth/google/status

### Frontend (if available)
- **Base URL**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **Login**: http://localhost:3000/login

---

## Stopping Services

### Using the Scripts
- Press **Ctrl+C** in the terminal running the script
- Services will stop gracefully

### Windows (Batch File)
- Services run in separate windows
- Close each window individually
- Or use `taskkill` (see troubleshooting)

### Manually
- Find the terminal/command prompt running the service
- Press **Ctrl+C**
- Wait for graceful shutdown

---

## Next Steps

1. ✅ Run a startup script
2. ✅ Check backend is working: http://localhost:8080/docs
3. ✅ Check frontend is working: http://localhost:3000
4. ✅ Configure your `.env` file (see [SETUP_GUIDE.md](SETUP_GUIDE.md))
5. ✅ Complete Google OAuth flow
6. ✅ Test the AI integration

---

## Support

If you encounter issues:
1. Check this troubleshooting section first
2. See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup
3. See [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for technical details
4. Check logs in the terminal for error messages

---

*Last Updated: October 4, 2025*
