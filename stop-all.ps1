# ScrimGG - Stop All Services
# This script stops all running services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Stopping ScrimGG Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to stop processes by matching command line pattern
function Stop-ProcessByCommandLine {
    param(
        [string]$Pattern,
        [string]$DisplayName,
        [string]$ProcessName = $null
    )
    
    try {
        # Use Get-CimInstance to access CommandLine property
        $processes = Get-CimInstance Win32_Process | Where-Object {
            $commandLine = $_.CommandLine
            if ($null -eq $commandLine) { return $false }
            if ($ProcessName -and $_.Name -ne $ProcessName) { return $false }
            return $commandLine -like "*$Pattern*"
        }
        
        if ($processes) {
            Write-Host "Stopping $DisplayName..." -ForegroundColor Yellow
            foreach ($proc in $processes) {
                try {
                    # Kill process tree using taskkill (more reliable on Windows)
                    $pid = $proc.ProcessId
                    Start-Process -FilePath "taskkill" -ArgumentList "/PID", $pid, "/F", "/T" -Wait -NoNewWindow -ErrorAction SilentlyContinue
                } catch {
                    # Fallback to Stop-Process if taskkill fails
                    try {
                        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
                    } catch {
                        # Process may have already terminated
                    }
                }
            }
            Write-Host "$DisplayName stopped" -ForegroundColor Green
            return $true
        } else {
            Write-Host "$DisplayName is not running" -ForegroundColor Gray
            return $false
        }
    } catch {
        Write-Host "Error stopping $DisplayName : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to stop processes by name (kills all instances)
function Stop-ServiceByName {
    param(
        [string]$ProcessName,
        [string]$DisplayName
    )
    
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "Stopping $DisplayName..." -ForegroundColor Yellow
        foreach ($proc in $processes) {
            try {
                # Kill process tree
                Start-Process -FilePath "taskkill" -ArgumentList "/PID", $proc.Id, "/F", "/T" -Wait -NoNewWindow -ErrorAction SilentlyContinue
            } catch {
                try {
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                } catch {
                    # Process may have already terminated
                }
            }
        }
        Write-Host "$DisplayName stopped" -ForegroundColor Green
    } else {
        Write-Host "$DisplayName is not running" -ForegroundColor Gray
    }
}

# Stop Electron processes first (they lock files)
Stop-ProcessByCommandLine -Pattern "electron" -DisplayName "Electron processes" -ProcessName "electron"
Stop-ProcessByCommandLine -Pattern "electron" -DisplayName "Electron processes" -ProcessName "Scrim.GG"

# Stop Node processes related to the project
Stop-ProcessByCommandLine -Pattern "react-scripts" -DisplayName "React development server" -ProcessName "node"
Stop-ProcessByCommandLine -Pattern "concurrently" -DisplayName "Concurrently processes" -ProcessName "node"
Stop-ProcessByCommandLine -Pattern "start:dev" -DisplayName "Start dev processes" -ProcessName "node"

# Stop any remaining Node processes that might be related (only if they're in the project directory)
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$nodeProcesses = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "node.exe" -and $_.CommandLine -like "*$projectPath*"
}
if ($nodeProcesses) {
    Write-Host "Stopping Node.js processes in project directory..." -ForegroundColor Yellow
    foreach ($proc in $nodeProcesses) {
        try {
            Start-Process -FilePath "taskkill" -ArgumentList "/PID", $proc.ProcessId, "/F", "/T" -Wait -NoNewWindow -ErrorAction SilentlyContinue
        } catch {
            try {
                Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            } catch {}
        }
    }
    Write-Host "Node.js processes stopped" -ForegroundColor Green
}

# Stop Celery processes
# Find all processes with "celery" in command line, then filter by beat/worker
$celeryProcesses = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "python.exe" -and $_.CommandLine -like "*celery*"
}
if ($celeryProcesses) {
    foreach ($proc in $celeryProcesses) {
        $commandLine = $proc.CommandLine
        if ($commandLine -like "*beat*") {
            Write-Host "Stopping Celery Beat (PID: $($proc.ProcessId))..." -ForegroundColor Yellow
            try {
                Start-Process -FilePath "taskkill" -ArgumentList "/PID", $proc.ProcessId, "/F", "/T" -Wait -NoNewWindow -ErrorAction SilentlyContinue
            } catch {
                Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            }
        } elseif ($commandLine -like "*worker*") {
            Write-Host "Stopping Celery Worker (PID: $($proc.ProcessId))..." -ForegroundColor Yellow
            try {
                Start-Process -FilePath "taskkill" -ArgumentList "/PID", $proc.ProcessId, "/F", "/T" -Wait -NoNewWindow -ErrorAction SilentlyContinue
            } catch {
                Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            }
        }
    }
    Write-Host "Celery processes stopped" -ForegroundColor Green
} else {
    Write-Host "No Celery processes found" -ForegroundColor Gray
}

# Stop Daphne/Django
Stop-ProcessByCommandLine -Pattern "daphne" -DisplayName "Django/Daphne server" -ProcessName "python.exe"

# Stop Python backend processes (client backend)
Stop-ProcessByCommandLine -Pattern "run.py" -DisplayName "Client backend (run.py)" -ProcessName "python.exe"
Stop-ProcessByCommandLine -Pattern "client\backend" -DisplayName "Client backend processes" -ProcessName "python.exe"

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
