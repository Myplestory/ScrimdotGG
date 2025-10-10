# Scrim.GG Client Backend - WebSocket-Based (Performance Optimized)
# Runs alongside Valorant - minimal resource usage

import os
import signal
import atexit
import asyncio
import json
from datetime import datetime
from typing import Set, Dict

from quart import Quart, websocket, jsonify
from quart_cors import cors

from clientapi import ValorantAPI

# File paths
folder_name = 'data'
file_name = 'data.json'
file_path = os.path.join(os.path.dirname(__file__), folder_name, file_name)

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
    
    # Stop heartbeat if running
    global heartbeat_task
    if heartbeat_task and not heartbeat_task.done():
        print("[HEARTBEAT] Stopping heartbeat for shutdown...")
        heartbeat_task.cancel()

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

# Heartbeat system for Valorant status monitoring
heartbeat_task = None
last_known_status = None


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
            was_in_game = client_states[client_id].get('in_game', False)
            del client_states[client_id]
            
            # If this client was in-game, check if we should restart heartbeat
            # Heartbeat should run if any client is NOT in-game
            if was_in_game:
                clients_not_in_game = sum(
                    1 for state in client_states.values() 
                    if not state.get('in_game', False)
                )
                if clients_not_in_game > 0:
                    await start_valorant_heartbeat()
        
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
        
        # PUG Queue operations (new)
        'join_pug_queue': handle_join_pug_queue,
        'leave_pug_queue': handle_leave_pug_queue,
        
        # Match operations
        'accept_match': handle_accept_match,
        'decline_match': handle_decline_match,
        'match_started': handle_match_started,
        'match_ended': handle_match_ended,
        
        # PUG Match flow events (from Django)
        'pug_match_found': handle_pug_match_found,
        'teams_assigned': handle_teams_assigned,
        'veto_update': handle_veto_update,
        'map_selected': handle_map_selected,
        
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
# Heartbeat System
# ============================================================

async def start_valorant_heartbeat():
    """
    Start the Valorant status heartbeat monitor.
    Runs when users are not in an active game (includes login, lobby, queue).
    """
    global heartbeat_task
    
    if heartbeat_task is None or heartbeat_task.done():
        print("[HEARTBEAT] Starting Valorant status monitor...")
        heartbeat_task = asyncio.create_task(valorant_heartbeat_loop())
    else:
        print("[HEARTBEAT] Heartbeat already running")

async def stop_valorant_heartbeat():
    """
    Stop the Valorant status heartbeat monitor.
    Called when user enters an active game match.
    """
    global heartbeat_task
    
    if heartbeat_task and not heartbeat_task.done():
        print("[HEARTBEAT] Stopping Valorant status monitor (user in-game)...")
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        heartbeat_task = None
    else:
        print("[HEARTBEAT] No heartbeat running to stop")

async def valorant_heartbeat_loop():
    """
    Main heartbeat loop - checks Valorant status every 3 seconds.
    Only broadcasts updates when status actually changes.
    """
    global last_known_status
    
    print("[HEARTBEAT] Valorant status monitor started")
    
    try:
        while True:
            # Check if any clients are still connected and not authenticated
            unauthenticated_clients = [
                client_id for client_id, state in client_states.items()
                if not state.get('authenticated', False)
            ]
            
            # Only run heartbeat if there are unauthenticated clients
            if unauthenticated_clients:
                try:
                    current_status = await check_valorant_status()
                    
                    # Only broadcast if status actually changed
                    if current_status != last_known_status:
                        print(f"[HEARTBEAT] Status changed: {last_known_status} -> {current_status}")
                        last_known_status = current_status
                        
                        # Broadcast to all connected clients
                        await broadcast_status_update({
                            'backend_connected': True,
                            'valorant': current_status,
                            'authenticated': False  # This will be updated per client
                        })
                    
                except Exception as e:
                    print(f"[HEARTBEAT] Error checking status: {e}")
            
            # Wait 3 seconds before next check
            await asyncio.sleep(3)
            
    except asyncio.CancelledError:
        print("[HEARTBEAT] Valorant status monitor stopped")
        raise
    except Exception as e:
        print(f"[HEARTBEAT] Unexpected error: {e}")

async def broadcast_status_update(status_data):
    """
    Broadcast status update to all connected WebSocket clients.
    """
    if not active_connections:
        print("[BROADCAST] No active connections to broadcast to")
        return
    
    message = json.dumps({
        'event': 'status_update',
        'payload': status_data
    })
    
    print(f"[BROADCAST] Broadcasting to {len(active_connections)} clients: {status_data}")
    
    disconnected_conns = []
    for ws in list(active_connections):
        try:
            await ws.send(message)
            print(f"[BROADCAST] Successfully sent to client")
        except Exception as e:
            print(f"[BROADCAST] Error sending to client: {e}")
            disconnected_conns.append(ws)
    
    # Clean up disconnected clients
    for ws in disconnected_conns:
        active_connections.discard(ws)

# ============================================================
# Event Handlers
# ============================================================

async def check_valorant_status():
    """
    Check if Valorant game is actually running (not just Riot Client)
    Uses process detection to verify VALORANT.exe is running.
    Returns:
        - 'running': Valorant game is launched and ready
        - 'riot_only': Only Riot Client is running, game not launched
        - 'not_running': Neither Riot Client nor game is running
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
        
        # CRITICAL: Call activate() to actually test if Riot Client is running
        # This is what throws the exception when Riot Client is not running
        print(f"[Status Check] Attempting to activate Valorant client...")
        temp_client.activate()
        print(f"[Status Check] Riot Client connection successful!")
        
        # Now check if actual VALORANT.exe game process is running
        # This is more reliable than API checks since Riot updated their API
        print("[Status Check] Checking for VALORANT.exe process...")
        import psutil
        
        valorant_process_found = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'VALORANT' in proc.info['name'].upper():
                    valorant_process_found = True
                    print(f"[Status Check] Found process: {proc.info['name']}")
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if valorant_process_found:
            print("[Status Check] Valorant game is running and ready")
            
            is_authenticated = (valorant_api.client is not None and 
                              hasattr(valorant_api.client, 'puuid') and 
                              valorant_api.client.puuid is not None)
            
            return {
                'status': 'running',
                'message': 'Valorant game is running and ready',
                'details': {
                    'region': temp_client.region,
                    'is_authenticated': is_authenticated
                }
            }
        else:
            # activate() worked but no VALORANT.exe process = only Riot Client running
            print(f"[Status Check] Game not launched (Riot Client only)")
            return {
                'status': 'riot_only',
                'message': 'Valorant game not launched (Riot Client only)',
                'details': None
            }
            
    except Exception as e:
        # If we can't create a client or activate it, Riot Client is probably not running
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
                'status': 'error',
                'message': f'Error checking status: {str(e)}',
                'details': None
            }

async def handle_connected(payload: dict, client_id: int, ws):
    """
    Handle client connection - send initial status and start heartbeat if needed.
    """
    try:
        print(f"[CONNECT] Client {client_id} connected")
        # Send initial status immediately when client connects
        await handle_get_status(payload, client_id, ws)
        
        # Start heartbeat if not already running and client is not in-game
        # Heartbeat runs during login, lobby, and queue - stops only when in active match
        if not client_states[client_id].get('in_game', False):
            await start_valorant_heartbeat()
            
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
            # More specific error messages based on status
            if valorant_status['status'] == 'riot_only':
                await send_message(ws, 'authentication_error', {
                    'message': 'Please launch Valorant game (Riot Client is running but game is not)',
                    'timeout': 5
                })
            elif valorant_status['status'] == 'not_running':
                await send_message(ws, 'authentication_error', {
                    'message': 'Riot Client is not running. Please start Valorant.',
                    'timeout': 5
                })
            else:
                await send_message(ws, 'authentication_error', {
                    'message': valorant_status.get('message', 'Unable to authenticate'),
                    'timeout': 5
                })
            return
        
        # Get region from payload, default to 'na' if not provided
        region = payload.get('region', 'na')
        print(f"[AUTH] Using region: {region}")
        
        result = await valorant_api.login(region)
        
        if result.get('status') == 'success':
            client_states[client_id]['authenticated'] = True
            client_states[client_id]['puuid'] = valorant_api.client.puuid
            client_states[client_id]['in_game'] = False  # Track in-game status
            
            # Get player data from Django server
            player_result = await valorant_api.get_player_model()
            
            # NOTE: Heartbeat continues running even after auth
            # It only stops when user enters an active game
            print("[AUTH] User authenticated, heartbeat continues until in-game")
            
            await send_event(ws, 'authentication_success', {
                'puuid': valorant_api.client.puuid,
                'player_data': player_result.get('data', {})
            })
        else:
            # Check if it's a region mismatch error
            if 'error' in result and 'status_code' in result:
                await send_message(ws, 'authentication_error', {
                    'message': f'Region mismatch! You selected {region.upper()}, but your Valorant client is in a different region. Please check your region selection and try again.',
                    'timeout': 10
                })
            else:
                await send_error(ws, "Valorant authentication failed. Is Valorant running?")
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'unable to activate' in error_msg or 'valorant running' in error_msg:
            await send_message(ws, 'authentication_error', {
                'message': 'Valorant client is not running or not accessible. Please start Valorant and try again.',
                'timeout': 5
            })
        else:
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
    When match fully starts (all accept), user enters in-game state.
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
    
    # TODO: Set in_game=True when match actually starts (after all players accept)
    # For now, we'll keep heartbeat running through the accept phase
    # The Django server should send a 'match_started' event when ready
    
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


async def handle_match_started(payload: dict, client_id: int, ws):
    """
    Handle match start event from Django server.
    Sets user as in-game and stops heartbeat.
    """
    print(f"[MATCH] Match started for client {client_id}")
    
    client_states[client_id]['in_game'] = True
    client_states[client_id]['match_id'] = payload.get('match_id')
    
    # Check if all clients are now in-game, stop heartbeat if so
    all_in_game = all(
        state.get('in_game', False) 
        for state in client_states.values()
    )
    if all_in_game:
        await stop_valorant_heartbeat()
    
    await send_event(ws, 'match_started', payload)


async def handle_match_ended(payload: dict, client_id: int, ws):
    """
    Handle match end event from Django server or client.
    Sets user as not in-game and restarts heartbeat.
    """
    print(f"[MATCH] Match ended for client {client_id}")
    
    client_states[client_id]['in_game'] = False
    client_states[client_id]['match_id'] = None
    
    # Restart heartbeat since user is back to lobby
    await start_valorant_heartbeat()
    
    await send_event(ws, 'match_ended', payload)


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

async def handle_join_pug_queue(payload: dict, client_id: int, ws):
    """
    Player joins PUG queue (solo or with party)
    """
    if not client_states[client_id]['authenticated']:
        await send_error(ws, "Not authenticated")
        return
    
    try:
        # Get player data for queue
        player_data = {
            'puuid': client_states[client_id]['puuid'],
            'queue_type': payload.get('queue_type', 'pug'),  # 'pug' or 'scrim'
            'party_id': payload.get('party_id', None),  # If queuing with friends
            'preferred_maps': payload.get('preferred_maps', []),
            'elo_range': payload.get('elo_range', None),  # For scrims
        }
        
        print(f"[PUG QUEUE] Player {client_states[client_id]['puuid']} joining {player_data['queue_type']} queue")
        
        # Send to Django matchmaking service
        await valorant_api.pugsocket.send_message('join_pug_queue', player_data)
        
        # Update local state
        client_states[client_id]['in_queue'] = True
        client_states[client_id]['queue_type'] = player_data['queue_type']
        
        await send_event(ws, 'queue_joined', {
            'queue_type': player_data['queue_type'],
            'estimated_wait': 60  # Django will calculate this
        })
        
    except Exception as e:
        await send_error(ws, f"Failed to join queue: {str(e)}")

async def handle_leave_pug_queue(payload: dict, client_id: int, ws):
    """
    Player leaves PUG queue
    """
    if not client_states[client_id]['authenticated']:
        await send_error(ws, "Not authenticated")
        return
    
    try:
        await valorant_api.pugsocket.send_message('leave_pug_queue', {
            'puuid': client_states[client_id]['puuid']
        })
        
        client_states[client_id]['in_queue'] = False
        client_states[client_id]['queue_type'] = None
        
        await send_event(ws, 'queue_left', {})
        print(f"[PUG QUEUE] Player {client_states[client_id]['puuid']} left queue")
        
    except Exception as e:
        await send_error(ws, f"Failed to leave queue: {str(e)}")

async def handle_direct_message(payload: dict, client_id: int, ws): pass


# ============================================================
# PUG Match Flow Handlers
# ============================================================

async def handle_pug_match_found(payload: dict, client_id: int, ws):
    """
    Django found a PUG match - 10 players of similar ELO
    """
    match_data = payload['match_data']
    # {
    #   'match_id': 'abc123',
    #   'players': [10 players with ELO],
    #   'average_elo': 1500,
    #   'elo_range': [1450, 1550],
    #   'accept_timeout': 30
    # }
    
    # Update state
    client_states[client_id]['pending_match'] = match_data['match_id']
    client_states[client_id]['in_queue'] = False
    
    print(f"[PUG MATCH] Match found for {len(match_data['players'])} players, avg ELO: {match_data['average_elo']}")
    
    # Notify frontend
    await send_event(ws, 'pug_match_found', {
        'match_id': match_data['match_id'],
        'players': match_data['players'],
        'average_elo': match_data['average_elo'],
        'elo_range': match_data['elo_range'],
        'accept_deadline': match_data.get('accept_deadline', 30)
    })

async def handle_teams_assigned(payload: dict, client_id: int, ws):
    """
    Django has balanced teams and selected captains
    """
    team_data = payload['team_data']
    # {
    #   'team_a': {
    #     'captain': {'puuid': '...', 'elo': 1600},
    #     'players': [5 players],
    #     'average_elo': 1520
    #   },
    #   'team_b': {
    #     'captain': {'puuid': '...', 'elo': 1580},
    #     'players': [5 players],
    #     'average_elo': 1518
    #   },
    #   'elo_difference': 2
    # }
    
    client_states[client_id]['team'] = payload.get('my_team')  # 'team_a' or 'team_b'
    client_states[client_id]['is_captain'] = payload.get('is_captain', False)
    
    print(f"[PUG TEAMS] Teams assigned - Player is on {payload.get('my_team', 'unknown')}, captain: {payload.get('is_captain', False)}")
    
    await send_event(ws, 'teams_assigned', team_data)

async def handle_veto_update(payload: dict, client_id: int, ws):
    """
    Receive veto updates from Django
    """
    veto_state = payload['veto_state']
    # {
    #   'banned': ['Breeze', 'Fracture', 'Pearl'],
    #   'remaining': ['Ascent', 'Bind', 'Haven'],
    #   'current_turn': 'team_a',
    #   'action': 'pick',  // Next action
    #   'time_left': 25
    # }
    
    print(f"[VETO] Update - {veto_state['current_turn']} is {veto_state['action']}ing")
    
    await send_event(ws, 'veto_update', veto_state)

async def handle_map_selected(payload: dict, client_id: int, ws):
    """
    Final map has been selected after veto
    """
    selected_map = payload['map']
    
    print(f"[VETO] Map selected: {selected_map}")
    
    await send_event(ws, 'map_selected', {
        'map': selected_map,
        'message': f'Map: {selected_map}'
    })


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
