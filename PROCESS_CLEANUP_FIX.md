# Process Cleanup Fix

## Problem
When closing the Electron client, the Python backend process was not being properly terminated, leading to:
- Multiple orphaned Python backend processes accumulating
- False "Game Connected" status when Valorant is not running
- Ability to log in even when Valorant is closed (using stale backend data)

## Root Causes
1. **Inadequate process termination**: `pythonProcess.kill()` only sent SIGTERM, which Python didn't handle properly on Windows
2. **No child process cleanup**: The shell-spawned Python process created child processes that weren't being killed
3. **Stale Valorant status**: The `check_valorant_status()` function relied on cached client data instead of performing fresh checks

## Solutions Implemented

### 1. Proper Process Cleanup (`client/frontend/main.js`)
- Added `killPythonBackend()` function that uses Windows `taskkill /T /F` to forcefully kill the process and all its children
- Stores the process PID for reliable termination
- Added `before-quit` event handler to ensure cleanup happens before app exits
- Set `detached: false` to keep the process attached to Electron

### 2. Fresh Valorant Status Checks (`client/backend/bootstrap.py`)
- Modified `check_valorant_status()` to always create a fresh `Client` instance
- No longer relies on cached `valorant_api.client` data
- Ensures accurate real-time status of Valorant game client

### 3. Cleanup Utility Script (`client/kill-backend.ps1`)
- **DEVELOPMENT ONLY** - PowerShell script to manually kill orphaned processes
- Useful during development for cleaning up after crashes or improper shutdowns
- **NOT INCLUDED IN PRODUCTION BUILDS** - The electron-builder config excludes it

## How to Use

### Normal Operation
Just use the client normally - the backend will now be properly terminated when you close the Electron app.

### Manual Cleanup (if needed)
If you notice multiple backend processes or false status, run:
```powershell
cd client
.\kill-backend.ps1
```

Or manually kill all Python processes:
```powershell
taskkill /f /im python.exe
```

## Testing
1. Start the client with `npm run start:dev`
2. Check Task Manager - should see one python.exe process
3. Close the Electron window
4. Check Task Manager - python.exe should be gone
5. Open client again - should show "Valorant Not Running" if Valorant is closed

## Changes Made
- `client/frontend/main.js`: Added proper process cleanup with taskkill
- `client/backend/bootstrap.py`: Updated `check_valorant_status()` to always perform fresh checks
- `client/kill-backend.ps1`: New cleanup utility script

