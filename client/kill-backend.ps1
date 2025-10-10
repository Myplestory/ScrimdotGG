# Kill orphaned Python backend processes
# 
# ⚠️ DEVELOPMENT TOOL ONLY - DO NOT SHIP TO PRODUCTION
# 
# This script is only needed during development if:
# - The Electron app crashes before cleanup runs
# - You force-kill the app from Task Manager
# - Processes get orphaned during rapid restarts
#
# Run this if you notice multiple backend processes running

Write-Host "🔍 Looking for Python backend processes..." -ForegroundColor Yellow

# Find all python.exe processes running bootstrap.py
$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -and ($_.CommandLine -like "*bootstrap.py*" -or $_.Path -like "*backend*")
}

if ($processes) {
    Write-Host "Found $($processes.Count) Python backend process(es):" -ForegroundColor Cyan
    $processes | ForEach-Object {
        Write-Host "  PID: $($_.Id) - Path: $($_.Path)" -ForegroundColor Gray
    }
    
    Write-Host "`n🛑 Killing all Python backend processes..." -ForegroundColor Red
    $processes | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force
            Write-Host "  ✅ Killed PID: $($_.Id)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Failed to kill PID: $($_.Id) - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`n✅ Cleanup complete!" -ForegroundColor Green
} else {
    Write-Host "✅ No orphaned Python backend processes found." -ForegroundColor Green
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

