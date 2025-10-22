#!/bin/bash
# ScrimGG - Start All Services (Mac/Linux)
# This script starts all required services for the ScrimGG application

echo "========================================"
echo "  Starting ScrimGG Services"
echo "========================================"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to start a service in a new terminal window
start_service_window() {
    local title=$1
    local command=$2
    local working_dir=$3
    
    echo "Starting $title..."
    
    # Detect OS and open terminal accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript <<EOF
tell application "Terminal"
    do script "cd '$working_dir' && $command"
    set custom title of front window to "$title"
end tell
EOF
    else
        # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal --title="$title" -- bash -c "cd '$working_dir' && $command; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -T "$title" -e "cd '$working_dir' && $command; bash" &
        elif command -v konsole &> /dev/null; then
            konsole --title "$title" -e bash -c "cd '$working_dir' && $command; exec bash" &
        else
            echo "No supported terminal emulator found. Please install gnome-terminal, xterm, or konsole."
            exit 1
        fi
    fi
    
    sleep 2
}

# Start Redis (if not already running)
echo "Checking Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - try homebrew redis
        if command -v brew &> /dev/null && brew list redis &> /dev/null; then
            brew services start redis
        else
            redis-server &
        fi
    else
        # Linux
        if systemctl is-active --quiet redis; then
            sudo systemctl start redis
        else
            redis-server &
        fi
    fi
    sleep 3
else
    echo "Redis is already running"
fi

# Start Celery Worker
start_service_window \
    "Celery Worker" \
    "pipenv run celery -A scrimgg worker --loglevel=debug --pool=gevent -Q celery,matchmaking,cleanup" \
    "$SCRIPT_DIR/server"

# Start Celery Beat
start_service_window \
    "Celery Beat" \
    "pipenv run celery -A scrimgg beat --loglevel=info" \
    "$SCRIPT_DIR/server"

# Start Django/Daphne Server
start_service_window \
    "Django Server (Daphne)" \
    "pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application" \
    "$SCRIPT_DIR/server"

# Start Electron Frontend
start_service_window \
    "Electron Frontend" \
    "npm run start:dev" \
    "$SCRIPT_DIR/client/frontend"

echo ""
echo "========================================"
echo "  All Services Started!"
echo "========================================"
echo ""
echo "Services running:"
echo "  - Redis Server"
echo "  - Celery Worker (port: default)"
echo "  - Celery Beat (scheduler)"
echo "  - Django Server (port: 8000)"
echo "  - Electron Frontend"
echo ""
echo "To stop all services, run: ./stop-all.sh"
echo ""
