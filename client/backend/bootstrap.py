# Scrim.GG Client Backend - WebSocket-Based (Performance Optimized)
# Runs alongside Valorant - minimal resource usage

import os
import signal
import atexit
import asyncio
import json
from datetime import datetime
from typing import Set, Dict

from quart import Quart, websocket
from quart_cors import cors

from clientapi import ValorantAPI

# Optional auth import - only needed for certain functions
try:
    import auth
    print("[OK] Auth module imported successfully")
except ImportError as e:
    print(f"[WARNING] Auth module import failed: {e}")
    auth = None

# Initialize Quart application
app = Quart(__name__)

# Configure CORS
app = cors(
    app,
    allow_origin="http://localhost:3000",
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True
)

# Active WebSocket connections (frontend clients)
active_connections: Set = set()

# Store client state
client_states: Dict[int, dict] = {}

def cleanup():
    """Cleanup resources on shutdown."""
    print("Cleaning up resources...")

atexit.register(cleanup)

def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    print(f"Signal {signum} received, exiting gracefully...")
    cleanup()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Global Valorant API instance
try:
    valorant_api = ValorantAPI()
    print("[OK] ValorantAPI initialized successfully")
except Exception as e:
    print(f"[WARNING] ValorantAPI initialization failed: {e}")
    valorant_api = None


# ============================================================
# WebSocket Event Router
# ============================================================

@app.websocket('/ws')
async def websocket_route():
    """
    Main WebSocket endpoint for frontend communication.
    Handles all events via event-driven architecture.
    """
    try:
        ws = websocket
        active_connections.add(ws)
        client_id = id(ws)
        
        client_states[client_id] = {
            'puuid': None,
            'authenticated': False,
            'lobby_id': None,
            'match_id': None,
        }
        
        print(f"[OK] Frontend WebSocket connected: {client_id}")
        
        # Send connection confirmation
        await send_message(ws, 'connected', {'message': 'Connected to Scrim.GG client service'})
        
        # Message loop
        while True:
            message = await ws.receive()
            data = json.loads(message)
            event = data.get('event')
            payload = data.get('payload', {})
            
            print(f"[RECV] Received: {event}")
            
            # Route to appropriate handler
            await route_event(event, payload, client_id, ws)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'ws' in locals():
            active_connections.discard(ws)
        if 'client_id' in locals() and client_id in client_states:
            del client_states[client_id]
        print(f"[DISCONNECT] Frontend WebSocket disconnected")


async def route_event(event: str, payload: dict, client_id: int, ws):
    """
    Route incoming events to appropriate handlers.
    """
    handlers = {
        # Connection and Status
        'connected': handle_connected,
        'get_status': handle_get_status,
        'authenticate': handle_authenticate,
        'get_initial_state': handle_get_initial_state,
        
        # Lobby operations
        'create_lobby': handle_create_lobby,
        'join_lobby': handle_join_lobby,
        'leave_lobby': handle_leave_lobby,
        
        # Queue operations
        'queue_lobby': handle_queue_lobby,
        'dequeue_lobby': handle_dequeue_lobby,
        
        # Match operations
        'accept_match': handle_accept_match,
        'decline_match': handle_decline_match,
        
        # Chat
        'lobby_chat': handle_lobby_chat,
        'direct_message': handle_direct_message,
        
        # Player
        'get_player_data': handle_get_player_data,
    }
    
    handler = handlers.get(event)
    if handler:
        try:
            await handler(payload, client_id, ws)
        except Exception as e:
            await send_error(ws, f"Error handling {event}: {str(e)}")
    else:
        await send_error(ws, f"Unknown event: {event}")


# ============================================================
# Event Handlers
# ============================================================

async def check_valorant_status():
    """
    Check if Valorant client is running and accessible.
    Always performs a fresh check, not relying on cached client.
    """
    try:
        # Check if valorant_api is initialized
        if valorant_api is None:
            return {
                'status': 'not_running',
                'message': 'Valorant API not initialized',
                'details': None
            }
        
        # Always try to create a fresh client instance to verify Valorant is actually running
        # This ensures we don't rely on stale/cached client data
        from valclient import Client
        temp_client = Client(region='na')
        
        # CRITICAL: Call activate() to actually test if Valorant is running
        # This is what throws the exception when Valorant is not running
        temp_client.activate()
        
        # If we get here, Valorant is running and we can connect to it
        is_authenticated = (valorant_api.client is not None and 
                          hasattr(valorant_api.client, 'puuid') and 
                          valorant_api.client.puuid is not None)
        
        return {
            'status': 'running',
            'message': 'Valorant client is running',
            'details': {
                'region': temp_client.region,
                'is_authenticated': is_authenticated
            }
        }
            
    except Exception as e:
        # If we can't create a client or activate it, Valorant is probably not running
        error_msg = str(e).lower()
        if 'unable to activate' in error_msg or 'valorant running' in error_msg:
            return {
                'status': 'not_running',
                'message': 'Valorant client is not running or not accessible',
                'details': None
            }
        elif 'connection' in error_msg or 'refused' in error_msg or 'timeout' in error_msg:
            return {
                'status': 'not_running',
                'message': 'Valorant client is not running or not accessible',
                'details': None
            }
        else:
            return {
                'status': 'not_running',
                'message': f'Valorant client error: {str(e)}',
                'details': None
            }

async def handle_connected(payload: dict, client_id: int, ws):
    """
    Handle client connection - send initial status.
    """
    try:
        print(f"[CONNECT] Client {client_id} connected")
        # Send initial status immediately when client connects
        await handle_get_status(payload, client_id, ws)
    except Exception as e:
        print(f"[ERROR] Error handling connection: {str(e)}")

async def handle_get_status(payload: dict, client_id: int, ws):
    """
    Get current system status (backend + Valorant).
    """
    try:
        valorant_status = await check_valorant_status()
        status = {
            'backend_connected': True,
            'valorant': valorant_status,
            'authenticated': client_states[client_id].get('authenticated', False)
        }
        await send_message(ws, 'status_update', status)
    except Exception as e:
        await send_error(ws, f"Error getting status: {str(e)}")

async def handle_authenticate(payload: dict, client_id: int, ws):
    """
    Authenticate with local Valorant client.
    """
    try:
        print("[AUTH] Authenticating with Valorant client...")
        
        # Check if valorant_api is initialized
        if valorant_api is None:
            await send_message(ws, 'authentication_error', {
                'message': 'Valorant API not initialized. Please restart the client.',
                'timeout': 5
            })
            return
        
        # First check if Valorant is running
        valorant_status = await check_valorant_status()
        if valorant_status['status'] != 'running':
            await send_message(ws, 'authentication_error', {
                'message': 'Valorant client is not running. Please launch Valorant first.',
                'timeout': 5
            })
            return
        
        result = await valorant_api.login("na")
        
        if result.get('status') == 'success':
            client_states[client_id]['authenticated'] = True
            client_states[client_id]['puuid'] = valorant_api.client.puuid
            
            # Get player data from Django server
            player_result = await valorant_api.get_player_model()
            
            await send_event(ws, 'authentication_success', {
                'puuid': valorant_api.client.puuid,
                'player_data': player_result.get('data', {})
            })
        else:
            await send_error(ws, "Valorant authentication failed. Is Valorant running?")
            
    except Exception as e:
        await send_error(ws, f"Authentication error: {str(e)}")


async def handle_get_initial_state(payload: dict, client_id: int, ws):
    """
    Get current state (after reconnect or refresh).
    """
    if not client_states[client_id]['authenticated']:
        await send_event(ws, 'not_authenticated', {})
        return
    
    # Get player data from Django
    result = await valorant_api.get_player_model()
    
    await send_event(ws, 'initial_state', {
        'player_data': result.get('data'),
        'lobby_id': client_states[client_id].get('lobby_id'),
        'match_id': client_states[client_id].get('match_id'),
    })


async def handle_create_lobby(payload: dict, client_id: int, ws):
    """
    Create a new lobby on the Django server.
    """
    if not client_states[client_id]['authenticated']:
        await send_error(ws, "Not authenticated")
        return
    
    print("🏠 Creating lobby...")
    result = await valorant_api.createlobby()
    
    if result.get('status') == 'success':
        lobby_id = result['data']['id']
        client_states[client_id]['lobby_id'] = lobby_id
        
        await send_event(ws, 'lobby_created', result['data'])
    else:
        await send_error(ws, "Failed to create lobby")


async def handle_queue_lobby(payload: dict, client_id: int, ws):
    """
    Queue the lobby for matchmaking.
    """
    lobby_id = client_states[client_id].get('lobby_id')
    if not lobby_id:
        await send_error(ws, "Not in a lobby")
        return
    
    map_preferences = payload.get('map_preferences', [])
    server_preferences = payload.get('server_preferences', [])
    
    print(f"[QUEUE] Queueing lobby {lobby_id} with preferences:", map_preferences, server_preferences)
    
    # Send queue request to Django server via WebSocket
    await valorant_api.pugsocket.send_message('add_lobby_to_queue', {
        'lobby_id': lobby_id,
        'lobby_rating': 1000,  # TODO: Get from lobby data
        'map_preferences': map_preferences,
        'server_preferences': server_preferences,
    })
    
    await send_event(ws, 'queue_status', {
        'in_queue': True,
        'estimated_wait': 60
    })


async def handle_accept_match(payload: dict, client_id: int, ws):
    """
    Accept a found match.
    """
    match_id = payload.get('match_id')
    if not match_id:
        await send_error(ws, "No match ID provided")
        return
    
    print(f"[ACCEPT] Accepting match {match_id}")
    
    # Send acceptance to Django server
    await valorant_api.pugsocket.send_message('accept_match', {
        'match_id': match_id,
        'puuid': client_states[client_id]['puuid']
    })
    
    client_states[client_id]['match_id'] = match_id
    
    await send_event(ws, 'match_accepted', {
        'match_id': match_id
    })


async def handle_decline_match(payload: dict, client_id: int, ws):
    """
    Decline a found match.
    """
    match_id = payload.get('match_id')
    if not match_id:
        return
    
    print(f"[DECLINE] Declining match {match_id}")
    
    await valorant_api.pugsocket.send_message('decline_match', {
        'match_id': match_id,
        'puuid': client_states[client_id]['puuid']
    })


async def handle_lobby_chat(payload: dict, client_id: int, ws):
    """
    Send lobby chat message.
    """
    lobby_id = payload.get('lobby_id')
    if not lobby_id:
        await send_error(ws, "Not in a lobby")
        return
    
    message = payload.get('message')
    if not message:
        return
    
    # Get player name for the message
    puuid = client_states[client_id].get('puuid')
    
    await valorant_api.send_lobby_message({
        'message': message,
        'lobby_id': lobby_id,
        'userAlias': puuid or 'Anonymous',  # TODO: Get actual alias
        'timestamp': payload.get('timestamp', datetime.now().isoformat())
    })
    
    # Echo back to sender (Django will broadcast to others)
    await send_event(ws, 'lobby_message', {
        'username': puuid or 'Anonymous',
        'message': message,
        'timestamp': payload.get('timestamp', datetime.now().isoformat())
    })


async def handle_get_player_data(payload: dict, client_id: int, ws):
    """
    Fetch player data from Django server.
    """
    result = await valorant_api.get_player_model()
    
    await send_event(ws, 'player_data', result.get('data', {}))


# Stub handlers for other events
async def handle_join_lobby(payload: dict, client_id: int, ws): pass
async def handle_leave_lobby(payload: dict, client_id: int, ws): pass
async def handle_dequeue_lobby(payload: dict, client_id: int, ws): pass
async def handle_direct_message(payload: dict, client_id: int, ws): pass


# ============================================================
# Utility Functions
# ============================================================

async def send_event(ws, event: str, payload: dict):
    """
    Send an event to a specific WebSocket client.
    """
    message = json.dumps({'event': event, 'payload': payload})
    try:
        await ws.send(message)
        print(f"[SENT] Sent: {event}")
    except Exception as e:
        print(f"Error sending event {event}: {e}")

async def send_message(ws, event: str, payload: dict):
    """
    Alias for send_event for backward compatibility.
    """
    await send_event(ws, event, payload)


async def send_error(ws, message: str):
    """
    Send an error message to a client.
    """
    await send_event(ws, 'error', {'message': message})


async def broadcast_to_all(event: str, payload: dict):
    """
    Send an event to all connected clients.
    """
    message = json.dumps({'event': event, 'payload': payload})
    
    for conn in list(active_connections):
        try:
            await conn.send(message)
        except Exception as e:
            print(f"Error broadcasting: {e}")
            active_connections.discard(conn)


# ============================================================
# Application Entry Point
# ============================================================

if __name__ == '__main__':
    try:
        print("=" * 60)
        print("Starting Scrim.GG Client Service")
        print("=" * 60)
        print("WebSocket server: ws://localhost:5888/ws")
        print("Ready to connect to Valorant")
        print("=" * 60)
        
        print(f"ValorantAPI status: {'Initialized' if valorant_api else 'None'}")
        print(f"Auth module status: {'Available' if auth else 'None'}")
        
        app.run(host='0.0.0.0', port=5888, debug=True)  # debug=True for troubleshooting
    finally:
        cleanup()
