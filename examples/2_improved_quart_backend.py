# Scrim.GG_Client/scrimgg/backend/bootstrap_improved.py
# Improved WebSocket-based backend (replace bootstrap.py)

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
from game_monitor import ValorantGameMonitor
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
client_states: Dict[str, dict] = {}

def cleanup():
    print("Cleaning up resources...")

atexit.register(cleanup)

def signal_handler(signum, frame):
    print(f"Signal {signum} received, exiting gracefully...")
    cleanup()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Global services
valorant_api = ValorantAPI()
game_monitor = None  # Initialize after client login


# ============================================================
# WebSocket Event Router
# ============================================================

@app.websocket('/ws')
async def websocket_route():
    """
    Main WebSocket endpoint for frontend communication.
    Handles all events via event-driven architecture.
    """
    active_connections.add(websocket._get_current_object())
    client_id = id(websocket._get_current_object())
    client_states[client_id] = {
        'puuid': None,
        'authenticated': False,
        'lobby_id': None,
        'match_id': None,
    }
    
    print(f"Frontend WebSocket connected: {client_id}")
    
    try:
        # Send connection confirmation
        await websocket.send(json.dumps({
            'event': 'connected',
            'payload': {'message': 'Connected to Scrim.GG client service'}
        }))
        
        # Message loop
        while True:
            message = await websocket.receive()
            data = json.loads(message)
            event = data.get('event')
            payload = data.get('payload', {})
            
            print(f"Received event from frontend: {event}")
            
            # Route to appropriate handler
            await route_event(event, payload, client_id)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket._get_current_object())
        if client_id in client_states:
            del client_states[client_id]
        print(f"Frontend WebSocket disconnected: {client_id}")


async def route_event(event: str, payload: dict, client_id: int):
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
        'invite_to_lobby': handle_invite_to_lobby,
        'kick_from_lobby': handle_kick_from_lobby,
        
        # Queue operations
        'queue_lobby': handle_queue_lobby,
        'dequeue_lobby': handle_dequeue_lobby,
        
        # Match operations
        'accept_match': handle_accept_match,
        'decline_match': handle_decline_match,
        'join_custom_game': handle_join_custom_game,
        
        # Veto operations
        'veto_ban_map': handle_veto_ban_map,
        'veto_pick_map': handle_veto_pick_map,
        'veto_ban_server': handle_veto_ban_server,
        'veto_pick_server': handle_veto_pick_server,
        
        # Chat
        'lobby_chat': handle_lobby_chat,
        'direct_message': handle_direct_message,
        
        # Player
        'get_player_data': handle_get_player_data,
        'update_settings': handle_update_settings,
    }
    
    handler = handlers.get(event)
    if handler:
        try:
            await handler(payload, client_id)
        except Exception as e:
            await send_error(client_id, f"Error handling {event}: {str(e)}")
    else:
        await send_error(client_id, f"Unknown event: {event}")


# ============================================================
# Event Handlers
# ============================================================

async def handle_authenticate(payload: dict, client_id: int):
    """
    Authenticate with local Valorant client.
    """
    global game_monitor
    
    try:
        # Authenticate with Valorant
        result = await valorant_api.login("na")
        
        if result.get('status') == 'success':
            client_states[client_id]['authenticated'] = True
            client_states[client_id]['puuid'] = valorant_api.client.puuid
            
            # Start game state monitor
            if not game_monitor:
                game_monitor = ValorantGameMonitor(valorant_api.client)
                asyncio.create_task(game_monitor.start_monitoring(broadcast_to_frontend))
            
            await broadcast_to_client(client_id, 'authentication_success', {
                'puuid': valorant_api.client.puuid,
                'player_data': result.get('data', {})
            })
        else:
            await send_error(client_id, "Authentication failed")
            
    except Exception as e:
        await send_error(client_id, f"Authentication error: {str(e)}")


async def handle_get_initial_state(payload: dict, client_id: int):
    """
    Get current state (after reconnect or refresh).
    """
    if not client_states[client_id]['authenticated']:
        await broadcast_to_client(client_id, 'not_authenticated', {})
        return
    
    # Get player data, lobby status, etc.
    result = await valorant_api.get_player_model()
    
    await broadcast_to_client(client_id, 'initial_state', {
        'player_data': result.get('data'),
        'lobby_id': client_states[client_id].get('lobby_id'),
        'match_id': client_states[client_id].get('match_id'),
    })


async def handle_create_lobby(payload: dict, client_id: int):
    """
    Create a new lobby on the Django server.
    """
    if not client_states[client_id]['authenticated']:
        await send_error(client_id, "Not authenticated")
        return
    
    result = await valorant_api.createlobby()
    
    if result.get('status') == 'success':
        lobby_id = result['data']['id']
        client_states[client_id]['lobby_id'] = lobby_id
        
        await broadcast_to_client(client_id, 'lobby_created', result['data'])
    else:
        await send_error(client_id, "Failed to create lobby")


async def handle_queue_lobby(payload: dict, client_id: int):
    """
    Queue the lobby for matchmaking.
    """
    lobby_id = client_states[client_id].get('lobby_id')
    if not lobby_id:
        await send_error(client_id, "Not in a lobby")
        return
    
    map_preferences = payload.get('map_preferences', [])
    server_preferences = payload.get('server_preferences', [])
    
    # Send queue request to Django server via WebSocket
    await valorant_api.pugsocket.send_message('add_lobby_to_queue', {
        'lobby_id': lobby_id,
        'map_preferences': map_preferences,
        'server_preferences': server_preferences,
    })
    
    await broadcast_to_client(client_id, 'queue_status', {
        'in_queue': True,
        'estimated_wait': 60  # Get from matchmaking engine
    })


async def handle_accept_match(payload: dict, client_id: int):
    """
    Accept a found match.
    """
    match_id = payload.get('match_id')
    if not match_id:
        await send_error(client_id, "No match ID provided")
        return
    
    # Send acceptance to Django server
    await valorant_api.pugsocket.send_message('accept_match', {
        'match_id': match_id,
        'puuid': client_states[client_id]['puuid']
    })
    
    client_states[client_id]['match_id'] = match_id
    
    await broadcast_to_client(client_id, 'match_accepted', {
        'match_id': match_id
    })


async def handle_join_custom_game(payload: dict, client_id: int):
    """
    Join the custom game when ready.
    This is called automatically when match is ready.
    """
    pregame_id = payload.get('pregame_id')
    is_constructor = payload.get('is_constructor', False)
    
    if is_constructor:
        # This client creates the custom game
        result = await valorant_api.create_custom_game(payload)
        await broadcast_to_client(client_id, 'custom_game_created', result)
    else:
        # Join existing custom game
        valorant_api.client.party_join(pregame_id)
        await broadcast_to_client(client_id, 'joined_custom_game', {
            'pregame_id': pregame_id
        })


async def handle_veto_ban_map(payload: dict, client_id: int):
    """
    Ban a map during veto phase.
    """
    await valorant_api.pugsocket.send_message('veto_action', {
        'match_id': payload.get('match_id'),
        'action': 'ban',
        'type': 'map',
        'value': payload.get('map'),
        'puuid': client_states[client_id]['puuid']
    })


async def handle_lobby_chat(payload: dict, client_id: int):
    """
    Send lobby chat message.
    """
    lobby_id = client_states[client_id].get('lobby_id')
    if not lobby_id:
        await send_error(client_id, "Not in a lobby")
        return
    
    await valorant_api.send_lobby_message({
        'message': payload.get('message'),
        'lobby_id': lobby_id,
        'userAlias': payload.get('userAlias', 'Anonymous'),
        'timestamp': payload.get('timestamp', datetime.now().isoformat())
    })


async def handle_get_player_data(payload: dict, client_id: int):
    """
    Fetch player data from Django server.
    """
    result = await valorant_api.get_player_model()
    
    await broadcast_to_client(client_id, 'player_data', result.get('data', {}))


# Stub handlers for other events
async def handle_join_lobby(payload: dict, client_id: int): pass
async def handle_leave_lobby(payload: dict, client_id: int): pass
async def handle_invite_to_lobby(payload: dict, client_id: int): pass
async def handle_kick_from_lobby(payload: dict, client_id: int): pass
async def handle_dequeue_lobby(payload: dict, client_id: int): pass
async def handle_decline_match(payload: dict, client_id: int): pass
async def handle_veto_pick_map(payload: dict, client_id: int): pass
async def handle_veto_ban_server(payload: dict, client_id: int): pass
async def handle_veto_pick_server(payload: dict, client_id: int): pass
async def handle_direct_message(payload: dict, client_id: int): pass
async def handle_update_settings(payload: dict, client_id: int): pass


# ============================================================
# Broadcasting Utilities
# ============================================================

async def broadcast_to_client(client_id: int, event: str, payload: dict):
    """
    Send an event to a specific client.
    """
    message = json.dumps({'event': event, 'payload': payload})
    
    for conn in active_connections:
        if id(conn) == client_id:
            try:
                await conn.send(message)
                print(f"Sent to client {client_id}: {event}")
            except Exception as e:
                print(f"Error sending to client {client_id}: {e}")
            break


async def broadcast_to_all(event: str, payload: dict):
    """
    Send an event to all connected clients.
    """
    message = json.dumps({'event': event, 'payload': payload})
    
    for conn in active_connections:
        try:
            await conn.send(message)
        except Exception as e:
            print(f"Error broadcasting: {e}")


async def broadcast_to_frontend(event: str, payload: dict):
    """
    Called by game monitor to push state changes to frontend.
    """
    await broadcast_to_all(event, payload)


async def send_error(client_id: int, message: str):
    """
    Send an error message to a client.
    """
    await broadcast_to_client(client_id, 'error', {'message': message})


# ============================================================
# Application Entry Point
# ============================================================

if __name__ == '__main__':
    try:
        print("Starting Scrim.GG Client Service...")
        app.run(host='0.0.0.0', port=5888, debug=True)
    finally:
        cleanup()

