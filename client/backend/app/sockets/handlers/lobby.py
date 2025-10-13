"""
Lobby operations event handlers.
"""
from quart import current_app
from ..events import on

@on("create_lobby")
async def handle_create_lobby(payload: dict, client_id: int, ws, mgr):
    """Create a new lobby on the Django server."""
    if not mgr.state[client_id]['authenticated']:
        await mgr.send(ws, 'error', {'message': "Not authenticated"})
        return
    
    print("🏠 Creating lobby...")
    
    valorant_service = current_app.valorant
    result = await valorant_service.create_lobby()
    
    if result.get('status') == 'success':
        lobby_id = result['data']['id']
        mgr.state[client_id]['lobby_id'] = lobby_id
        
        await mgr.send(ws, 'lobby_created', result['data'])
    else:
        await mgr.send(ws, 'error', {'message': "Failed to create lobby"})


@on("join_lobby")
async def handle_join_lobby(payload: dict, client_id: int, ws, mgr):
    """Join an existing lobby."""
    # Stub implementation
    pass


@on("leave_lobby")
async def handle_leave_lobby(payload: dict, client_id: int, ws, mgr):
    """Leave current lobby."""
    # Stub implementation
    pass


@on("queue_lobby")
async def handle_queue_lobby(payload: dict, client_id: int, ws, mgr):
    """Queue the lobby for matchmaking."""
    lobby_id = mgr.state[client_id].get('lobby_id')
    if not lobby_id:
        await mgr.send(ws, 'error', {'message': "Not in a lobby"})
        return
    
    valorant_service = current_app.valorant
    map_preferences = payload.get('map_preferences', [])
    server_preferences = payload.get('server_preferences', [])
    
    print(f"[QUEUE] Queueing lobby {lobby_id} with preferences:", map_preferences, server_preferences)
    
    # Send queue request to Django server via WebSocket
    await valorant_service.api.pugsocket.send_message('add_lobby_to_queue', {
        'lobby_id': lobby_id,
        'lobby_rating': 1000,  # TODO: Get from lobby data
        'map_preferences': map_preferences,
        'server_preferences': server_preferences,
    })
    
    await mgr.send(ws, 'queue_status', {
        'in_queue': True,
        'estimated_wait': 60
    })


@on("dequeue_lobby")
async def handle_dequeue_lobby(payload: dict, client_id: int, ws, mgr):
    """Remove lobby from queue."""
    # Stub implementation
    pass


@on("get_player_data")
async def handle_get_player_data(payload: dict, client_id: int, ws, mgr):
    """Fetch player data from Django server."""
    valorant_service = current_app.valorant
    result = await valorant_service.get_player_model()
    
    await mgr.send(ws, 'player_data', result.get('data', {}))


@on("get_match_data")
async def handle_get_match_data(payload: dict, client_id: int, ws, mgr):
    """Fetch match data from Django server and forward to frontend."""
    match_id = payload.get('match_id')
    
    if not match_id:
        await mgr.send(ws, 'error', {'message': 'match_id is required'})
        return
    
    try:
        valorant_service = current_app.valorant
        
        # Forward request to Django PugAPI WebSocket
        await valorant_service.api.pugsocket.send_message('get_match_data', {
            'match_id': match_id
        })
        
        # Response will be received via PugAPI message handler and forwarded to frontend
        print(f"[GET_MATCH_DATA] Forwarded request for match {match_id} to Django")
        
    except Exception as e:
        print(f"[ERROR] Failed to get match data: {str(e)}")
        await mgr.send(ws, 'error', {'message': f'Failed to get match data: {str(e)}'})

