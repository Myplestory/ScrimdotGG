# ScrimGG - Start Client Only
# This script starts only the client services (backend + frontend)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting ScrimGG Client" -ForegroundColor Cyan
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

# Start Client Backend (Quart server)
Start-ServiceWindow `
    -Title "Client Backend" `
    -Command "pipenv run python run.py" `
    -WorkingDirectory "$ROOT_DIR\client\backend"

# Start Electron Frontend
Start-ServiceWindow `
    -Title "Electron Frontend" `
    -Command "npm run start:dev" `
    -WorkingDirectory "$ROOT_DIR\client\frontend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Client Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services running:" -ForegroundColor Yellow
Write-Host "  - Client Backend (port: 5888)" -ForegroundColor White
Write-Host "  - Electron Frontend" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

