#!/bin/bash
# ScrimGG - Stop All Services (Mac/Linux)
# This script stops all running services

echo "========================================"
echo "  Stopping ScrimGG Services"
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

# Stop Celery processes
stop_service_by_name "celery.*worker" "Celery Worker"
stop_service_by_name "celery.*beat" "Celery Beat"

# Stop Daphne/Django
stop_service_by_name "daphne.*scrimgg" "Django/Daphne Server"

# Stop Node/React/Electron processes
stop_service_by_name "react-scripts" "React Development Server"
stop_service_by_name "electron.*scrimgg" "Electron"

echo ""
echo "========================================"
echo "  Services Stopped!"
echo "========================================"
echo ""
echo "Note: Redis server was not stopped (if running)"
echo "To stop Redis:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  macOS: brew services stop redis"
else
    echo "  Linux: sudo systemctl stop redis"
fi
echo "  Manual: pkill redis-server"
echo ""
