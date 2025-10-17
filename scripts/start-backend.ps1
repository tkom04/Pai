# Quick backend-only startup script
Write-Host "Starting Backend Server..." -ForegroundColor Cyan

# Activate venv and start uvicorn
& ".\venv\Scripts\Activate.ps1"

Write-Host "Backend will start on http://localhost:8080" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

