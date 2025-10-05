@echo off
REM Personal AI Assistant - Startup Script (Windows Batch)
REM This script starts both the backend (FastAPI) and frontend (Next.js)

echo ================================================
echo   Personal AI Assistant - Starting Services
echo ================================================
echo.

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.9+ and add it to your PATH
    pause
    exit /b 1
)

python --version
echo.

REM Check for Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Node.js is not installed or not in PATH!
    echo Frontend will not start. Install Node.js if you want to run the frontend.
    set SKIP_FRONTEND=1
) else (
    node --version
    set SKIP_FRONTEND=0
)

echo.

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please create a .env file with your credentials.
    echo See SETUP_GUIDE.md for details.
    echo.
)

REM Install Python dependencies
echo Checking Python dependencies...
pip show fastapi >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing Python dependencies...
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install Python dependencies!
        pause
        exit /b 1
    )
    echo Python dependencies installed successfully
) else (
    echo Python dependencies already installed
)

echo.

REM Install Node dependencies if needed
if %SKIP_FRONTEND% EQU 0 (
    if exist "frontend copy\package.json" (
        echo Checking Node.js dependencies...
        cd "frontend copy"
        if not exist "node_modules" (
            echo Installing Node.js dependencies...
            call npm install
            if %ERRORLEVEL% NEQ 0 (
                echo ERROR: Failed to install Node.js dependencies!
                cd ..
                pause
                exit /b 1
            )
            echo Node.js dependencies installed successfully
        ) else (
            echo Node.js dependencies already installed
        )
        cd ..
        echo.
    )
)

REM Start backend in a new window
echo ================================================
echo Starting Backend (FastAPI)...
echo ================================================
echo.

start "PAI Backend" /MIN cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"
echo Backend starting on http://localhost:8080
echo   - API Docs: http://localhost:8080/docs
echo   - Health Check: http://localhost:8080/healthz
echo.

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window if available
if %SKIP_FRONTEND% EQU 0 (
    if exist "frontend copy\package.json" (
        echo ================================================
        echo Starting Frontend (Next.js)...
        echo ================================================
        echo.

        start "PAI Frontend" /MIN cmd /c "cd frontend copy && npm run dev"
        echo Frontend starting on http://localhost:3000
        echo.
    )
)

echo ================================================
echo   All services started successfully!
echo ================================================
echo.
echo Backend API: http://localhost:8080/docs
if %SKIP_FRONTEND% EQU 0 (
    if exist "frontend copy\package.json" (
        echo Frontend UI: http://localhost:3000
    )
)
echo.
echo Services are running in separate windows.
echo Close those windows to stop the services.
echo.

REM Open browser to API docs
echo Opening API documentation in browser...
timeout /t 2 /nobreak >nul
start http://localhost:8080/docs

echo.
echo Press any key to exit this window (services will continue running)...
pause >nul
