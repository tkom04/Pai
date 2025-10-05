# Personal AI Assistant - Startup Script (PowerShell)
# This script starts both the backend (FastAPI) and frontend (Next.js)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Personal AI Assistant - Starting Services   " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-CommandExists {
    param($Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $Command) {
            return $true
        }
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-CommandExists "python")) {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ and add it to your PATH" -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "âœ“ Python found: $pythonVersion" -ForegroundColor Green

$skipFrontend = $false
if (-not (Test-CommandExists "node")) {
    Write-Host "WARNING: Node.js is not installed or not in PATH!" -ForegroundColor Yellow
    Write-Host "Frontend will not start. Install Node.js if you want to run the frontend." -ForegroundColor Yellow
    $skipFrontend = $true
} else {
    $nodeVersion = node --version 2>&1
    Write-Host "âœ“ Node.js found: $nodeVersion" -ForegroundColor Green
}

Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host "The server will start but some features may not work." -ForegroundColor Yellow
    Write-Host "Please create a .env file with your credentials (see SETUP_GUIDE.md)" -ForegroundColor Yellow
    Write-Host ""
}

# Install Python dependencies if needed
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "requirements.txt")) {
    Write-Host "ERROR: requirements.txt not found!" -ForegroundColor Red
    exit 1
}

# Check if packages are installed
$pipList = pip list 2>&1 | Out-String
if ($pipList -notmatch "fastapi") {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Python dependencies!" -ForegroundColor Red
        exit 1
    }
    Write-Host "âœ“ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "âœ“ Python dependencies already installed" -ForegroundColor Green
}

Write-Host ""

# Install Node dependencies if frontend exists and Node is available
if ((-not $skipFrontend) -and (Test-Path "frontend copy/package.json")) {
    Write-Host "Checking Node.js dependencies..." -ForegroundColor Yellow
    Push-Location "frontend copy"

    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing Node.js dependencies (this may take a few minutes)..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to install Node.js dependencies!" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Write-Host "âœ“ Node.js dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "âœ“ Node.js dependencies already installed" -ForegroundColor Green
    }

    Pop-Location
    Write-Host ""
}

# Start backend
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Starting Backend (FastAPI)..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$backendJob = Start-Job -ScriptBlock {
    param($WorkDir)
    Set-Location $WorkDir
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
} -ArgumentList $PWD

Write-Host "âœ“ Backend starting on http://localhost:8080" -ForegroundColor Green
Write-Host "  - API Docs: http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "  - Health Check: http://localhost:8080/healthz" -ForegroundColor Cyan
Write-Host ""

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend if available
$frontendJob = $null
if ((-not $skipFrontend) -and (Test-Path "frontend copy/package.json")) {
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "Starting Frontend (Next.js)..." -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""

    $frontendJob = Start-Job -ScriptBlock {
        param($WorkDir)
        Set-Location "$WorkDir/frontend copy"
        npm run dev
    } -ArgumentList $PWD

    Write-Host "âœ“ Frontend starting on http://localhost:3000" -ForegroundColor Green
    Write-Host ""
}

Write-Host "================================================" -ForegroundColor Green
Write-Host "  All services started successfully!          " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API: http://localhost:8080/docs" -ForegroundColor Cyan
if ((-not $skipFrontend) -and (Test-Path "frontend copy/package.json")) {
    Write-Host "Frontend UI: http://localhost:3000" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Monitor jobs and display output
try {
    while ($true) {
        # Check if backend is still running
        $backendState = $backendJob.State
        if ($backendState -ne "Running") {
            Write-Host "Backend stopped unexpectedly! State: $backendState" -ForegroundColor Red
            Receive-Job -Job $backendJob
            break
        }

        # Receive and display output from backend
        Receive-Job -Job $backendJob

        # Receive and display output from frontend if it exists
        if ($frontendJob) {
            $frontendState = $frontendJob.State
            if ($frontendState -ne "Running") {
                Write-Host "Frontend stopped unexpectedly! State: $frontendState" -ForegroundColor Red
                Receive-Job -Job $frontendJob
            } else {
                Receive-Job -Job $frontendJob
            }
        }

        Start-Sleep -Seconds 1
    }
} finally {
    # Cleanup on exit
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow

    if ($backendJob) {
        Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $backendJob -Force -ErrorAction SilentlyContinue
        Write-Host "âœ“ Backend stopped" -ForegroundColor Green
    }

    if ($frontendJob) {
        Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $frontendJob -Force -ErrorAction SilentlyContinue
        Write-Host "âœ“ Frontend stopped" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "All services stopped. Goodbye!" -ForegroundColor Cyan
}
