# Orbit - Start All Services Script
# This script starts the backend API, PWA, and marketing website

Write-Host "Starting Orbit - Personal AI Command Center" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$rootPath = $PSScriptRoot

# Function to check if a command exists
function Test-Command($command) {
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-Command "python")) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

if (-not (Test-Command "node")) {
    Write-Host "ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

if (-not (Test-Command "npm")) {
    Write-Host "ERROR: npm is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Prerequisites check passed" -ForegroundColor Green
Write-Host ""

# Check if venv exists
if (-not (Test-Path "$rootPath\venv")) {
    Write-Host "WARNING: Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "SUCCESS: Virtual environment created" -ForegroundColor Green
}

# Check if node_modules exist in PWA
if (-not (Test-Path "$rootPath\pwa\node_modules")) {
    Write-Host "WARNING: PWA dependencies not found. Installing..." -ForegroundColor Yellow
    Set-Location "$rootPath\pwa"
    npm install
    Set-Location $rootPath
    Write-Host "SUCCESS: PWA dependencies installed" -ForegroundColor Green
}

# Check if node_modules exist in website
if (-not (Test-Path "$rootPath\website\node_modules")) {
    Write-Host "WARNING: Website dependencies not found. Installing..." -ForegroundColor Yellow
    Set-Location "$rootPath\website"
    npm install
    Set-Location $rootPath
    Write-Host "SUCCESS: Website dependencies installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting all services..." -ForegroundColor Cyan
Write-Host ""

# Start Backend API
Write-Host "[BACKEND] Starting Backend API on Port 8080..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootPath'; .\venv\Scripts\activate; Write-Host '[BACKEND] API Running on http://localhost:8080' -ForegroundColor Magenta; uvicorn app.main:app --reload --port 8080"

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Start PWA
Write-Host "[PWA] Starting PWA Application on Port 3000..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootPath\pwa'; Write-Host '[PWA] App Running on http://localhost:3000' -ForegroundColor Blue; npm run dev"

# Wait a moment
Start-Sleep -Seconds 2

# Start Website
Write-Host "[WEBSITE] Starting Marketing Website on Port 3001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootPath\website'; Write-Host '[WEBSITE] Site Running on http://localhost:3001' -ForegroundColor Green; npm run dev"

# Wait for services to be ready
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "SUCCESS: All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Yellow
Write-Host "   [WEBSITE] Marketing Site: http://localhost:3001" -ForegroundColor Green
Write-Host "   [PWA]     Application:    http://localhost:3000" -ForegroundColor Blue
Write-Host "   [API]     Backend:        http://localhost:8080" -ForegroundColor Magenta
Write-Host "   [DOCS]    API Docs:       http://localhost:8080/docs" -ForegroundColor Magenta
Write-Host ""
Write-Host "TIP: Each service runs in its own window" -ForegroundColor Cyan
Write-Host "TIP: Close windows or press Ctrl+C to stop" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to open the marketing website in your browser..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open marketing website in default browser
Start-Process "http://localhost:3001"

Write-Host ""
Write-Host "Orbit is now running! Happy organizing!" -ForegroundColor Cyan

