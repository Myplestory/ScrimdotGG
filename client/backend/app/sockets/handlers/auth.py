"""
Authentication event handlers.
"""
from quart import current_app
from ..events import on

@on("authenticate")
async def handle_authenticate(payload: dict, client_id: int, ws, mgr):
    """Authenticate with local Valorant client."""
    try:
        print("[AUTH] Authenticating with Valorant client...")
        
        valorant_service = current_app.valorant
        
        # Check if valorant_api is initialized
        if valorant_service.api is None:
            await mgr.send(ws, 'authentication_error', {
                'message': 'Valorant API not initialized. Please restart the client.',
                'timeout': 5
            })
            return
        
        # First check if Valorant is running
        valorant_status = await valorant_service.check_status()
        if valorant_status['status'] != 'running':
            # More specific error messages based on status
            if valorant_status['status'] == 'riot_only':
                await mgr.send(ws, 'authentication_error', {
                    'message': 'Please launch Valorant game (Riot Client is running but game is not)',
                    'timeout': 5
                })
            elif valorant_status['status'] == 'not_running':
                await mgr.send(ws, 'authentication_error', {
                    'message': 'Riot Client is not running. Please start Valorant.',
                    'timeout': 5
                })
            else:
                await mgr.send(ws, 'authentication_error', {
                    'message': valorant_status.get('message', 'Unable to authenticate'),
                    'timeout': 5
                })
            return
        
        # Get region from payload, default to 'na' if not provided
        region = payload.get('region', 'na')
        print(f"[AUTH] Using region: {region}")
        
        result = await valorant_service.login(region)
        
        if result.get('status') == 'success':
            mgr.state[client_id]['authenticated'] = True
            mgr.state[client_id]['puuid'] = valorant_service.api.client.puuid
            mgr.state[client_id]['in_game'] = False  # Track in-game status
            
            # Get player data from Django server
            player_result = await valorant_service.get_player_model()
            
            # NOTE: Heartbeat continues running even after auth
            # It only stops when user enters an active game
            print("[AUTH] User authenticated, heartbeat continues until in-game")
            
            await mgr.send(ws, 'authentication_success', {
                'puuid': valorant_service.api.client.puuid,
                'player_data': player_result.get('data', {})
            })
        else:
            # Check if it's a region mismatch error
            if 'error' in result and 'status_code' in result:
                await mgr.send(ws, 'authentication_error', {
                    'message': f'Region mismatch! You selected {region.upper()}, but your Valorant client is in a different region. Please check your region selection and try again.',
                    'timeout': 10
                })
            else:
                await mgr.send(ws, 'error', {'message': "Valorant authentication failed. Is Valorant running?"})
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'unable to activate' in error_msg or 'valorant running' in error_msg:
            await mgr.send(ws, 'authentication_error', {
                'message': 'Valorant client is not running or not accessible. Please start Valorant and try again.',
                'timeout': 5
            })
        else:
            await mgr.send(ws, 'error', {'message': f"Authentication error: {str(e)}"})


@on("get_initial_state")
async def handle_get_initial_state(payload: dict, client_id: int, ws, mgr):
    """Get current state (after reconnect or refresh)."""
    if not mgr.state[client_id]['authenticated']:
        await mgr.send(ws, 'not_authenticated', {})
        return
    
    valorant_service = current_app.valorant
    # Get player data from Django
    result = await valorant_service.get_player_model()
    
    await mgr.send(ws, 'initial_state', {
        'player_data': result.get('data'),
        'lobby_id': mgr.state[client_id].get('lobby_id'),
        'match_id': mgr.state[client_id].get('match_id'),
    })

