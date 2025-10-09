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
import auth

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
valorant_api = ValorantAPI()


# ============================================================
# WebSocket Event Router
# ============================================================

@app.websocket('/ws')
async def websocket_route():
    """
    Main WebSocket endpoint for frontend communication.
    Handles all events via event-driven architecture.
    """
    ws = websocket._get_current_object()
    active_connections.add(ws)
    client_id = id(ws)
    
    client_states[client_id] = {
        'puuid': None,
        'authenticated': False,
        'lobby_id': None,
        'match_id': None,
    }
    
    print(f"✅ Frontend WebSocket connected: {client_id}")
    
    try:
        # Send connection confirmation
        await ws.send(json.dumps({
            'event': 'connected',
            'payload': {'message': 'Connected to Scrim.GG client service'}
        }))
        
        # Message loop
        while True:
            message = await ws.receive()
            data = json.loads(message)
            event = data.get('event')
            payload = data.get('payload', {})
            
            print(f"📥 Received: {event}")
            
            # Route to appropriate handler
            await route_event(event, payload, client_id, ws)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.discard(ws)
        if client_id in client_states:
            del client_states[client_id]
        print(f"❌ Frontend WebSocket disconnected: {client_id}")


async def route_event(event: str, payload: dict, client_id: int, ws):
    """
    Route incoming events to appropriate handlers.
    """
    handlers = {
        # Authentication
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

async def handle_authenticate(payload: dict, client_id: int, ws):
    """
    Authenticate with local Valorant client.
    """
    try:
        print("🔐 Authenticating with Valorant client...")
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
    
    print(f"🎮 Queueing lobby {lobby_id} with preferences:", map_preferences, server_preferences)
    
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
    
    print(f"✅ Accepting match {match_id}")
    
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
    
    print(f"❌ Declining match {match_id}")
    
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
        print(f"📤 Sent: {event}")
    except Exception as e:
        print(f"Error sending event {event}: {e}")


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
        print("🚀 Starting Scrim.GG Client Service")
        print("=" * 60)
        print("📡 WebSocket server: ws://localhost:5888/ws")
        print("🎮 Ready to connect to Valorant")
        print("=" * 60)
        
        app.run(host='0.0.0.0', port=5888, debug=False)  # debug=False for better performance
    finally:
        cleanup()
