# ScrimGG - Start All Services
# This script starts all required services for the ScrimGG application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting ScrimGG Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Function to start a process in a new window
function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory
    )
    
    Write-Host "Starting $Title..." -ForegroundColor Green
    
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "& { `$host.UI.RawUI.WindowTitle = '$Title'; cd '$WorkingDirectory'; $Command }"
    )
    
    Start-Sleep -Seconds 2
}

# Start Redis (if not already running)
Write-Host "Checking Redis..." -ForegroundColor Yellow
$redisProcess = Get-Process redis-server -ErrorAction SilentlyContinue
if (-not $redisProcess) {
    Write-Host "Starting Redis..." -ForegroundColor Green
    Start-Process redis-server -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "Redis is already running" -ForegroundColor Green
}

# Start Celery Worker
Start-ServiceWindow `
    -Title "Celery Worker" `
    -Command "pipenv run celery -A scrimgg worker --loglevel=debug --pool=gevent -Q celery,matchmaking,cleanup" `
    -WorkingDirectory "$ROOT_DIR\server"

# Start Celery Beat
Start-ServiceWindow `
    -Title "Celery Beat" `
    -Command "pipenv run celery -A scrimgg beat --loglevel=info" `
    -WorkingDirectory "$ROOT_DIR\server"

# Start Django/Daphne Server
Start-ServiceWindow `
    -Title "Django Server (Daphne)" `
    -Command "pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application" `
    -WorkingDirectory "$ROOT_DIR\server"

# Start Electron Frontend
Start-ServiceWindow `
    -Title "Electron Frontend" `
    -Command "npm run start:dev" `
    -WorkingDirectory "$ROOT_DIR\client\frontend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services running:" -ForegroundColor Yellow
Write-Host "  - Redis Server (minimized)" -ForegroundColor White
Write-Host "  - Celery Worker (port: default)" -ForegroundColor White
Write-Host "  - Celery Beat (scheduler)" -ForegroundColor White
Write-Host "  - Django Server (port: 8000)" -ForegroundColor White
Write-Host "  - Electron Frontend" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
