# Orbit - Start Frontend (PWA) Only
# This script starts only the PWA frontend application

Write-Host "Starting Orbit PWA Frontend..." -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

$rootPath = $PSScriptRoot

# Check prerequisites
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: npm is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if node_modules exist in PWA
if (-not (Test-Path "$rootPath\..\pwa\node_modules")) {
    Write-Host "WARNING: PWA dependencies not found. Installing..." -ForegroundColor Yellow
    Set-Location "$rootPath\..\pwa"
    npm install
    Set-Location $rootPath
    Write-Host "SUCCESS: PWA dependencies installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting PWA Frontend on Port 3000..." -ForegroundColor Blue
Write-Host ""

# Start PWA
Set-Location "$rootPath\..\pwa"
Write-Host "[PWA] App Running on http://localhost:3000" -ForegroundColor Blue
npm run dev
