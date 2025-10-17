# Orbit - Start Website Only
# This script starts only the marketing website

Write-Host "Starting Orbit Marketing Website..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
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

# Check if node_modules exist in website
if (-not (Test-Path "$rootPath\..\website\node_modules")) {
    Write-Host "WARNING: Website dependencies not found. Installing..." -ForegroundColor Yellow
    Set-Location "$rootPath\..\website"
    npm install
    Set-Location $rootPath
    Write-Host "SUCCESS: Website dependencies installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting Marketing Website on Port 3001..." -ForegroundColor Green
Write-Host ""

# Start Website
Set-Location "$rootPath\..\website"
Write-Host "[WEBSITE] Site Running on http://localhost:3001" -ForegroundColor Green
npm run dev
