# ScrimGG - Stop All Services
# This script stops all running services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Stopping ScrimGG Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to stop processes by name
function Stop-ServiceByName {
    param(
        [string]$ProcessName,
        [string]$DisplayName
    )
    
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "Stopping $DisplayName..." -ForegroundColor Yellow
        $processes | Stop-Process -Force
        Write-Host "$DisplayName stopped" -ForegroundColor Green
    } else {
        Write-Host "$DisplayName is not running" -ForegroundColor Gray
    }
}

# Stop Celery processes
$celeryProcesses = Get-Process | Where-Object { $_.CommandLine -like "*celery*" -and $_.ProcessName -eq "python" }
if ($celeryProcesses) {
    Write-Host "Stopping Celery processes..." -ForegroundColor Yellow
    $celeryProcesses | Stop-Process -Force
    Write-Host "Celery processes stopped" -ForegroundColor Green
} else {
    Write-Host "No Celery processes found" -ForegroundColor Gray
}

# Stop Daphne/Django
$daphneProcesses = Get-Process | Where-Object { $_.CommandLine -like "*daphne*" -and $_.ProcessName -eq "python" }
if ($daphneProcesses) {
    Write-Host "Stopping Django/Daphne server..." -ForegroundColor Yellow
    $daphneProcesses | Stop-Process -Force
    Write-Host "Django/Daphne server stopped" -ForegroundColor Green
} else {
    Write-Host "No Django/Daphne processes found" -ForegroundColor Gray
}

# Stop Node/Electron processes
$nodeProcesses = Get-Process | Where-Object { $_.CommandLine -like "*react-scripts*" -or $_.CommandLine -like "*electron*" }
if ($nodeProcesses) {
    Write-Host "Stopping Node/Electron processes..." -ForegroundColor Yellow
    $nodeProcesses | Stop-Process -Force
    Write-Host "Node/Electron processes stopped" -ForegroundColor Green
}

Stop-ServiceByName -ProcessName "node" -DisplayName "Node.js processes"

# Optionally stop Redis (commented out by default)
# Uncomment the line below if you want to stop Redis as well
# Stop-ServiceByName -ProcessName "redis-server" -DisplayName "Redis Server"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Services Stopped!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: Redis server was not stopped (if running)" -ForegroundColor Gray
Write-Host "To stop Redis, run: Stop-Process -Name redis-server -Force" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
