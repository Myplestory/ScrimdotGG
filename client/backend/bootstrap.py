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
        print(f"[WEBSOCKET] Added connection {ws} to active_connections. Total: {len(active_connections)}")
        client_id = id(ws)
        
        client_states[client_id] = {
            'puuid': None,
            'authenticated': False,
            'lobby_id': None,
            'match_id': None,
            'connected': True,
            'websocket': ws,
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
            print(f"[WEBSOCKET] Removed connection {ws} from active_connections. Total: {len(active_connections)}")
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
        
        # Match execution events (Phase 3)
        'match_starting': handle_match_starting,
        'join_custom_game': handle_join_custom_game,
        'match_in_progress': handle_match_in_progress,
        'match_score_update': handle_match_score_update,
        'match_completed': handle_match_completed,
        
        # PUG Match flow events (from Django)
        'match_found': handle_pug_match_found,  # Django sends 'match_found'
        'pug_match_found': handle_pug_match_found,  # Keep for backward compatibility
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
            # Check if any clients are connected (authenticated or not)
            connected_clients = [
                client_id for client_id, state in client_states.items()
                if state.get('connected', False)
            ]
            
            print(f"[HEARTBEAT] Connected clients: {len(connected_clients)}, Total clients: {len(client_states)}")
            
            # Run heartbeat if there are any connected clients
            if connected_clients:
                try:
                    current_status = await check_valorant_status()
                    
                    # Only broadcast if status actually changed
                    if current_status != last_known_status:
                        print(f"[HEARTBEAT] Status changed: {last_known_status} -> {current_status}")
                        last_known_status = current_status
                        
                        # Broadcast to all connected clients with per-client authentication status
                        await broadcast_status_update({
                            'backend_connected': True,
                            'valorant': current_status,
                            'authenticated': None  # Will be set per client in broadcast function
                        })
                    
                except Exception as e:
                    print(f"[HEARTBEAT] Error checking status: {e}")
                
                # Check for pending match notifications
                if valorant_api and hasattr(valorant_api, '_pending_match_data') and valorant_api._pending_match_data:
                    print(f"[HEARTBEAT] Found pending match data, broadcasting...")
                    match_data = valorant_api._pending_match_data
                    valorant_api._pending_match_data = None  # Clear it
                    
                    # Broadcast to all connected clients
                    await broadcast_to_all('pug_match_found', match_data)
                    print(f"[HEARTBEAT] Broadcasted pug_match_found to {len(active_connections)} clients")
            
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
    
    print(f"[BROADCAST] Broadcasting to {len(active_connections)} clients: {status_data}")
    
    disconnected_conns = []
    for ws in list(active_connections):
        try:
            # Get client-specific status data
            client_status = status_data.copy()
            
            # Set authentication status based on client state
            if 'authenticated' in status_data and status_data['authenticated'] is None:
                # Find client ID for this WebSocket connection
                client_id = None
                for cid, state in client_states.items():
                    if state.get('websocket') == ws:
                        client_id = cid
                        break
                
                if client_id is not None:
                    client_status['authenticated'] = client_states[client_id].get('authenticated', False)
                    print(f"[BROADCAST] Found client {client_id}, auth: {client_status['authenticated']}")
                else:
                    client_status['authenticated'] = False
                    print(f"[BROADCAST] No client ID found for WebSocket, defaulting to False")
            
            message = json.dumps({
                'event': 'status_update',
                'payload': client_status
            })
            
            await ws.send(message)
            print(f"[BROADCAST] Successfully sent to client (auth: {client_status.get('authenticated', False)})")
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
        
        # PRIORITY 1: Check if actual VALORANT.exe game process is running FIRST
        # This is the most reliable indicator of whether the game is actually running
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
        
        # Check Riot Client connection regardless of game process status
        print(f"[Status Check] Checking Riot Client connection...")
        from valclient import Client
        temp_client = Client(region='na')
        
        try:
            temp_client.activate()
            print(f"[Status Check] Riot Client connection successful!")
            
            if valorant_process_found:
                # Both Riot Client and game process are working - game is fully running
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
                # Riot Client is accessible but game process not found - only Riot Client running
                print("[Status Check] Riot Client running but VALORANT.exe not found - game not launched")
                return {
                    'status': 'riot_only',
                    'message': 'Valorant not launched',
                    'details': {
                        'region': temp_client.region
                    }
                }
            
        except Exception as client_error:
            # Riot Client connection failed - nothing is running
            print(f"[Status Check] Riot Client connection failed: {client_error}")
            return {
                'status': 'not_running',
                'message': 'Riot Client is not running',
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


# ============================================================
# Match Execution Handlers (Phase 3)
# ============================================================

async def handle_match_starting(payload: dict, client_id: int, ws):
    """
    Django server notifies that match is starting.
    If this client is constructor, create custom game.
    Otherwise, wait for join instruction.
    """
    match_id = payload.get('match_id')
    is_constructor = payload.get('is_constructor', False)
    map_name = payload.get('map')
    server = payload.get('server')
    team = payload.get('team')
    
    print(f"[MATCH START] Match {match_id} starting - Constructor: {is_constructor}")
    
    # Stop heartbeat - user entering game
    client_states[client_id]['in_game'] = True
    await stop_valorant_heartbeat()
    
    # Notify frontend
    await send_event(ws, 'match_starting', {
        'match_id': match_id,
        'is_constructor': is_constructor,
        'map': map_name,
        'server': server,
        'team': team
    })
    
    if is_constructor:
        # This client needs to create the custom game
        print(f"[CONSTRUCTOR] Creating custom game for match {match_id}")
        asyncio.create_task(create_custom_game(match_id, map_name, server, client_id))


async def create_custom_game(match_id: str, map_name: str, server: str, client_id: int):
    """
    Constructor client creates the custom game in Valorant.
    
    Performance: Runs in background task to avoid blocking
    """
    try:
        # Change party to custom mode
        print("[CONSTRUCTOR] Changing to custom game mode...")
        custom_response = valorant_api.client.party_change_to_custom()
        pregame_id = custom_response.get('ID')
        
        if not pregame_id:
            raise ValueError("Failed to get pregame ID from custom game creation")
        
        # Set custom game settings
        print("[CONSTRUCTOR] Configuring game settings...")
        settings = {
            "Map": valorant_api.args['mapPreferences'].get(map_name),
            "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
            "GamePod": valorant_api._get_server_url(server),
            "UseBots": False,
            "GameRules": {
                "AllowGameModifiers": "true",
                "PlayOutAllRounds": "true",
                "SkipMatchHistory": "true",
                "TournamentMode": "false",
                "IsOvertimeWinByTwo": "true",
            },
        }
        
        valorant_api.client.party_set_custom_game_settings(settings)
        
        # Notify Django server via WebSocket
        print(f"[CONSTRUCTOR] Custom game created: {pregame_id}")
        await valorant_api.pugsocket.send_message('custom_game_created', {
            'match_id': match_id,
            'pregame_id': pregame_id,
            'constructor_puuid': valorant_api.client.puuid
        })
        
        # Wait a moment for settings to apply
        await asyncio.sleep(2)
        
        # Start the custom game
        print("[CONSTRUCTOR] Starting custom game...")
        valorant_api.client.party_start_custom_game()
        
        # Get coregame ID after match starts
        await asyncio.sleep(5)  # Wait for game to start
        coregame_data = valorant_api.client.coregame_fetch_player()
        coregame_id = coregame_data.get('MatchID')
        
        if coregame_id:
            # Notify Django that match is live
            await valorant_api.pugsocket.send_message('match_started', {
                'match_id': match_id,
                'coregame_id': coregame_id
            })
            
            # Start monitoring the match (background task)
            asyncio.create_task(valorant_api.monitor_match(match_id, coregame_id))
        
    except Exception as e:
        print(f"[CONSTRUCTOR] Error creating custom game: {str(e)}")
        import traceback
        traceback.print_exc()
        # TODO: Notify Django of failure


async def handle_join_custom_game(payload: dict, client_id: int, ws):
    """
    Django server instructs this client to join the custom game.
    Non-constructor players join the pregame created by constructor.
    """
    match_id = payload.get('match_id')
    pregame_id = payload.get('pregame_id')
    team = payload.get('team')
    
    print(f"[JOIN] Joining custom game: {pregame_id} for match {match_id}")
    
    try:
        # Join the party/pregame
        valorant_api.client.party_join(pregame_id)
        
        # Notify Django that we joined successfully
        await valorant_api.pugsocket.send_message('player_joined_game', {
            'match_id': match_id,
            'player_puuid': valorant_api.client.puuid,
            'team': team
        })
        
        # Notify frontend
        await send_event(ws, 'joined_custom_game', {
            'match_id': match_id,
            'team': team
        })
        
        print(f"[JOIN] Successfully joined match {match_id}")
        
    except Exception as e:
        print(f"[JOIN] Error joining custom game: {str(e)}")
        import traceback
        traceback.print_exc()
        # TODO: Handle join failure


async def handle_match_in_progress(payload: dict, client_id: int, ws):
    """
    Match is now live - all players have loaded in.
    """
    match_id = payload.get('match_id')
    
    print(f"[MATCH LIVE] Match {match_id} is now in progress")
    
    # Notify frontend to transition to in-game state
    await send_event(ws, 'match_in_progress', payload)


async def handle_match_score_update(payload: dict, client_id: int, ws):
    """
    Receive score update from Django (for spectators or match room).
    """
    # Simply forward to frontend
    await send_event(ws, 'match_score_update', payload)


async def handle_match_completed(payload: dict, client_id: int, ws):
    """
    Match completed - show results and restart heartbeat.
    """
    print(f"[MATCH COMPLETE] Match completed")
    
    # Set user as not in-game
    client_states[client_id]['in_game'] = False
    client_states[client_id]['match_id'] = None
    
    # Restart heartbeat
    await start_valorant_heartbeat()
    
    # Notify frontend
    await send_event(ws, 'match_completed', payload)


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
        puuid = client_states[client_id]['puuid']
        
        # Create a lobby for this player (Django will handle if one already exists)
        print(f"[PUG QUEUE] Creating lobby for player {puuid}")
        create_result = await valorant_api.createlobby()
        
        print(f"[DEBUG] create_lobby response: {create_result}")
        
        if create_result and create_result.get('status') == 'success':
            lobby_id = create_result['data']['id']
            print(f"[PUG QUEUE] Got lobby {lobby_id}")
        else:
            print(f"[ERROR] Invalid lobby response: {create_result}")
            await send_error(ws, "Failed to create/get lobby")
            return
        
        # Get player data for queue
        player_data = {
            'puuid': puuid,
            'lobby_id': lobby_id,
            'queue_type': payload.get('queue_type', 'pug'),  # 'pug' or 'scrim'
            'party_id': payload.get('party_id', None),  # If queuing with friends
            'preferred_maps': payload.get('preferred_maps', []),
            'elo_range': payload.get('elo_range', None),  # For scrims
        }
        
        print(f"[PUG QUEUE] Player {puuid} joining {player_data['queue_type']} queue")
        
        # Update lobby preferences before sending to queue
        if player_data['preferred_maps']:
            print(f"[PUG QUEUE] Updating lobby map preferences: {player_data['preferred_maps']}")
            update_result = await valorant_api.pugsocket.send_message('update_lobby_preferences', {
                'lobby_id': lobby_id,
                'requester_puuid': puuid,
                'map_preferences': player_data['preferred_maps'],
                'server_preferences': payload.get('preferred_servers', [])
            })
            print(f"[PUG QUEUE] Lobby preferences update result: {update_result}")
        
        # Send to Django matchmaking service
        # Convert to the format Django expects
        django_data = {
            'lobby_id': player_data['lobby_id'],
            'requester_puuid': player_data['puuid'],
            'queue_type': player_data['queue_type']
        }
        await valorant_api.pugsocket.send_message('add_lobby_to_queue', django_data)
        
        # Update local state
        client_states[client_id]['in_queue'] = True
        client_states[client_id]['queue_type'] = player_data['queue_type']
        client_states[client_id]['lobby_id'] = player_data['lobby_id']
        
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
        # Get stored lobby_id from client state
        lobby_id = client_states[client_id].get('lobby_id')
        
        if not lobby_id:
            await send_error(ws, "No lobby found to leave")
            return
        
        # Send to Django matchmaking service
        django_data = {
            'lobby_id': lobby_id,
            'requester_puuid': client_states[client_id]['puuid']
        }
        await valorant_api.pugsocket.send_message('remove_lobby_from_queue', django_data)
        
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
    Receives: {match_id, match_confirmation_id, timeout_seconds, message}
    """
    # Django sends the data directly in payload, not nested in 'match_data'
    match_id = payload.get('match_id')
    match_confirmation_id = payload.get('match_confirmation_id')
    timeout_seconds = payload.get('timeout_seconds', 30)
    message = payload.get('message', 'Match found! Please accept to continue.')
    
    if not match_id:
        print(f"[ERROR] Match found event missing match_id: {payload}")
        return
    
    # Update state
    client_states[client_id]['pending_match'] = match_id
    client_states[client_id]['in_queue'] = False
    
    print(f"[PUG MATCH] Match found! ID: {match_id}, Timeout: {timeout_seconds}s")
    
    # Notify frontend with the actual data format
    await send_event(ws, 'match_found', {
        'match_id': match_id,
        'match_confirmation_id': match_confirmation_id,
        'timeout_seconds': timeout_seconds,
        'message': message,
        'accept_deadline': timeout_seconds
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
