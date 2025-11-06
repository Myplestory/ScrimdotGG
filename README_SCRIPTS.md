# ScrimGG - Quick Start Scripts

This folder contains scripts to easily start and stop all ScrimGG services with one click.

## Files

### Windows
- **`start-all.bat`** - Double-click this to start all services (recommended)
- **`start-all.ps1`** - PowerShell script that starts all services
- **`stop-all.bat`** - Double-click this to stop all services
- **`stop-all.ps1`** - PowerShell script that stops all services

### Mac/Linux
- **`start-all.sh`** - Bash script to start all services
- **`stop-all.sh`** - Bash script to stop all services

## Usage

### Windows

#### Starting Services

**Option 1: Double-click** (Easiest)
1. Double-click `start-all.bat`
2. Wait for all service windows to open
3. The application will be ready in ~10-15 seconds

**Option 2: PowerShell**
```powershell
.\start-all.ps1
```

**Option 3: Command Prompt**
```cmd
start-all.bat
```

#### Stopping Services

**Option 1: Double-click**
1. Double-click `stop-all.bat`
2. All services will be stopped

**Option 2: PowerShell**
```powershell
.\stop-all.ps1
```

### Mac/Linux

#### First Time Setup
Make the scripts executable:
```bash
chmod +x start-all.sh stop-all.sh
```

#### Starting Services
```bash
./start-all.sh
```

#### Stopping Services
```bash
./stop-all.sh
```

## What Gets Started

When you run `start-all`, the following services start in separate windows:

1. **Redis Server** - Data cache and message broker (minimized)
2. **Celery Worker** - Background task processing
3. **Celery Beat** - Task scheduler
4. **Django Server (Daphne)** - Backend API and WebSocket server (port 8000)
5. **Electron Frontend** - Client application with React

## Requirements

Before using these scripts, ensure:

- Redis is installed and in your PATH
- Python dependencies are installed (`pipenv install` in `server/` folder)
- Node dependencies are installed (`npm install` in `client/frontend/` folder)

## Troubleshooting

### Windows: "Cannot be loaded because running scripts is disabled"

If you get a PowerShell execution policy error:

1. Open PowerShell as Administrator
2. Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Type `Y` to confirm

### Mac/Linux: "Permission denied"

If you get a permission denied error:

```bash
chmod +x start-all.sh stop-all.sh
```

### Mac: Redis installation

If Redis is not installed on Mac:

```bash
brew install redis
```

### Linux: Redis installation

Ubuntu/Debian:
```bash
sudo apt-get install redis-server
```

Fedora/CentOS:
```bash
sudo dnf install redis
```

### Services won't start

- Check if Redis is installed: `redis-server --version`
- Check if Python environment is set up: `cd server && pipenv --venv`
- Check if Node modules are installed: `cd client/frontend && npm list`

### Port already in use

If port 8000 is already in use:
1. Run `stop-all.bat` to clean up
2. Check for stuck processes: `Get-Process | Where-Object {$_.ProcessName -eq "python" -or $_.ProcessName -eq "node"}`
3. Kill manually if needed: `Stop-Process -Id <PID> -Force`

## Platform-Specific Notes

### macOS
- The script automatically detects and uses macOS Terminal
- If Redis is installed via Homebrew, it will use `brew services`
- Each service opens in a new Terminal tab/window

### Linux
- Supports gnome-terminal, xterm, and konsole
- Uses systemctl for Redis if available
- Each service opens in a new terminal window

### Windows
- Each service opens in a new PowerShell window
- Redis runs minimized to save taskbar space
- All windows have descriptive titles for easy identification

## Manual Service Management

If you prefer to manage services individually:

### Start Redis
```powershell
redis-server
```

### Start Celery Worker
```powershell
cd server
pipenv run celery -A scrimgg worker --loglevel=debug --pool=gevent -Q celery,matchmaking,cleanup
```

### Start Celery Beat
```powershell
cd server
pipenv run celery -A scrimgg beat --loglevel=info
```

### Start Django Server
```powershell
cd server
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application
```

### Start Frontend
```powershell
cd client/frontend
npm run start:dev
```

## Notes

- Each service runs in its own PowerShell window for easy monitoring
- Redis runs minimized to save taskbar space
- The stop script does NOT stop Redis by default (to preserve data)
- All windows can be closed individually if needed
