#!/bin/bash
# ScrimGG - Stop Client Only (Mac/Linux)
# This script stops only the client services (backend + frontend)

echo "========================================"
echo "  Stopping ScrimGG Client"
echo "========================================"
echo ""

# Function to stop processes by name
stop_service_by_name() {
    local process_name=$1
    local display_name=$2
    
    if pgrep -f "$process_name" > /dev/null; then
        echo "Stopping $display_name..."
        pkill -f "$process_name"
        echo "$display_name stopped"
    else
        echo "$display_name is not running"
    fi
}

# Stop Electron processes
stop_service_by_name "electron.*scrimgg" "Electron"
stop_service_by_name "electron" "Electron processes"

# Stop Node/React processes
stop_service_by_name "react-scripts" "React Development Server"
stop_service_by_name "npm.*start:dev" "NPM Start Dev"

# Stop Python backend processes (client backend)
stop_service_by_name "python.*run.py" "Client Backend"
stop_service_by_name "python.*client/backend" "Client Backend processes"

echo ""
echo "========================================"
echo "  Client Services Stopped!"
echo "========================================"
echo ""

