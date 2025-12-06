#!/bin/bash
# ScrimGG - Start Client Only (Mac/Linux)
# This script starts only the client services (backend + frontend)

echo "========================================"
echo "  Starting ScrimGG Client"
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

# Start Client Backend (Quart server)
start_service_window \
    "Client Backend" \
    "pipenv run python run.py" \
    "$SCRIPT_DIR/client/backend"

# Start Electron Frontend
start_service_window \
    "Electron Frontend" \
    "npm run start:dev" \
    "$SCRIPT_DIR/client/frontend"

echo ""
echo "========================================"
echo "  Client Services Started!"
echo "========================================"
echo ""
echo "Services running:"
echo "  - Client Backend (port: 5888)"
echo "  - Electron Frontend"
echo ""
echo "To stop client services, run: ./stop-client.sh"
echo ""

