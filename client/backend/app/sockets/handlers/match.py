"""
Match lifecycle event handlers.
"""
import asyncio
from quart import current_app
from ..events import on

@on("accept_match")
async def handle_accept_match(payload: dict, client_id: int, ws, mgr):
    """Accept a found match."""
    match_id = payload.get('match_id')
    if not match_id:
        await mgr.send(ws, 'error', {'message': "No match ID provided"})
        return
    
    print(f"[ACCEPT] Accepting match {match_id}")
    
    valorant_service = current_app.valorant
    # Send acceptance to Django server
    await valorant_service.api.pugsocket.send_message('accept_match', {
        'match_id': match_id,
        'puuid': mgr.state[client_id]['puuid']
    })
    
    mgr.state[client_id]['match_id'] = match_id
    
    await mgr.send(ws, 'match_accepted', {
        'match_id': match_id
    })


@on("decline_match")
async def handle_decline_match(payload: dict, client_id: int, ws, mgr):
    """Decline a found match."""
    match_id = payload.get('match_id')
    if not match_id:
        return
    
    print(f"[DECLINE] Declining match {match_id}")
    
    valorant_service = current_app.valorant
    await valorant_service.api.pugsocket.send_message('decline_match', {
        'match_id': match_id,
        'puuid': mgr.state[client_id]['puuid']
    })


@on("match_started")
async def handle_match_started(payload: dict, client_id: int, ws, mgr):
    """
    Handle match start event from Django server.
    Sets user as in-game and stops heartbeat.
    """
    print(f"[MATCH] Match started for client {client_id}")
    
    mgr.state[client_id]['in_game'] = True
    mgr.state[client_id]['match_id'] = payload.get('match_id')
    
    await mgr.send(ws, 'match_started', payload)


@on("match_ended")
async def handle_match_ended(payload: dict, client_id: int, ws, mgr):
    """
    Handle match end event from Django server or client.
    Sets user as not in-game and restarts heartbeat.
    """
    print(f"[MATCH] Match ended for client {client_id}")
    
    mgr.state[client_id]['in_game'] = False
    mgr.state[client_id]['match_id'] = None
    
    await mgr.send(ws, 'match_ended', payload)


@on("match_starting")
async def handle_match_starting(payload: dict, client_id: int, ws, mgr):
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
    mgr.state[client_id]['in_game'] = True
    
    # Notify frontend
    await mgr.send(ws, 'match_starting', {
        'match_id': match_id,
        'is_constructor': is_constructor,
        'map': map_name,
        'server': server,
        'team': team
    })
    
    if is_constructor:
        # This client needs to create the custom game
        print(f"[CONSTRUCTOR] Creating custom game for match {match_id}")
        valorant_service = current_app.valorant
        asyncio.create_task(create_custom_game(valorant_service, match_id, map_name, server, client_id))


async def create_custom_game(valorant_service, match_id: str, map_name: str, server: str, client_id: int):
    """
    Constructor client creates the custom game in Valorant.
    Performance: Runs in background task to avoid blocking
    """
    try:
        # Change party to custom mode
        print("[CONSTRUCTOR] Changing to custom game mode...")
        custom_response = valorant_service.api.client.party_change_to_custom()
        pregame_id = custom_response.get('ID')
        
        if not pregame_id:
            raise ValueError("Failed to get pregame ID from custom game creation")
        
        # Set custom game settings
        print("[CONSTRUCTOR] Configuring game settings...")
        settings = {
            "Map": valorant_service.api.args['mapPreferences'].get(map_name),
            "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
            "GamePod": valorant_service.api._get_server_url(server),
            "UseBots": False,
            "GameRules": {
                "AllowGameModifiers": "true",
                "PlayOutAllRounds": "true",
                "SkipMatchHistory": "true",
                "TournamentMode": "false",
                "IsOvertimeWinByTwo": "true",
            },
        }
        
        valorant_service.api.client.party_set_custom_game_settings(settings)
        
        # Notify Django server via WebSocket
        print(f"[CONSTRUCTOR] Custom game created: {pregame_id}")
        await valorant_service.api.pugsocket.send_message('custom_game_created', {
            'match_id': match_id,
            'pregame_id': pregame_id,
            'constructor_puuid': valorant_service.api.client.puuid
        })
        
        # Wait a moment for settings to apply
        await asyncio.sleep(2)
        
        # Start the custom game
        print("[CONSTRUCTOR] Starting custom game...")
        valorant_service.api.client.party_start_custom_game()
        
        # Get coregame ID after match starts
        await asyncio.sleep(5)  # Wait for game to start
        coregame_data = valorant_service.api.client.coregame_fetch_player()
        coregame_id = coregame_data.get('MatchID')
        
        if coregame_id:
            # Notify Django that match is live
            await valorant_service.api.pugsocket.send_message('match_started', {
                'match_id': match_id,
                'coregame_id': coregame_id
            })
            
            # Start monitoring the match (background task)
            asyncio.create_task(valorant_service.api.monitor_match(match_id, coregame_id))
        
    except Exception as e:
        print(f"[CONSTRUCTOR] Error creating custom game: {str(e)}")
        import traceback
        traceback.print_exc()


@on("join_custom_game")
async def handle_join_custom_game(payload: dict, client_id: int, ws, mgr):
    """
    Django server instructs this client to join the custom game.
    Non-constructor players join the pregame created by constructor.
    """
    match_id = payload.get('match_id')
    pregame_id = payload.get('pregame_id')
    team = payload.get('team')
    
    print(f"[JOIN] Joining custom game: {pregame_id} for match {match_id}")
    
    try:
        valorant_service = current_app.valorant
        
        # Join the party/pregame
        valorant_service.api.client.party_join(pregame_id)
        
        # Notify Django that we joined successfully
        await valorant_service.api.pugsocket.send_message('player_joined_game', {
            'match_id': match_id,
            'player_puuid': valorant_service.api.client.puuid,
            'team': team
        })
        
        # Notify frontend
        await mgr.send(ws, 'joined_custom_game', {
            'match_id': match_id,
            'team': team
        })
        
        print(f"[JOIN] Successfully joined match {match_id}")
        
    except Exception as e:
        print(f"[JOIN] Error joining custom game: {str(e)}")
        import traceback
        traceback.print_exc()


@on("match_in_progress")
async def handle_match_in_progress(payload: dict, client_id: int, ws, mgr):
    """Match is now live - all players have loaded in."""
    match_id = payload.get('match_id')
    
    print(f"[MATCH LIVE] Match {match_id} is now in progress")
    
    # Notify frontend to transition to in-game state
    await mgr.send(ws, 'match_in_progress', payload)


@on("match_score_update")
async def handle_match_score_update(payload: dict, client_id: int, ws, mgr):
    """Receive score update from Django (for spectators or match room)."""
    # Simply forward to frontend
    await mgr.send(ws, 'match_score_update', payload)


@on("match_completed")
async def handle_match_completed(payload: dict, client_id: int, ws, mgr):
    """Match completed - show results and restart heartbeat."""
    print(f"[MATCH COMPLETE] Match completed")
    
    # Set user as not in-game
    mgr.state[client_id]['in_game'] = False
    mgr.state[client_id]['match_id'] = None
    
    # Notify frontend
    await mgr.send(ws, 'match_completed', payload)


@on("pug_match_found")
async def handle_pug_match_found(payload: dict, client_id: int, ws, mgr):
    """
    Django found a PUG match - 10 players of similar ELO.
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
    mgr.state[client_id]['pending_match'] = match_id
    mgr.state[client_id]['in_queue'] = False
    
    print(f"[PUG MATCH] Match found! ID: {match_id}, Timeout: {timeout_seconds}s")
    
    # Notify frontend with the actual data format
    await mgr.send(ws, 'match_found', {
        'match_id': match_id,
        'match_confirmation_id': match_confirmation_id,
        'timeout_seconds': timeout_seconds,
        'message': message,
        'accept_deadline': timeout_seconds
    })


@on("match_found")
async def handle_match_found(payload: dict, client_id: int, ws, mgr):
    """Alias for pug_match_found for backward compatibility."""
    await handle_pug_match_found(payload, client_id, ws, mgr)


@on("teams_assigned")
async def handle_teams_assigned(payload: dict, client_id: int, ws, mgr):
    """Django has balanced teams and selected captains."""
    team_data = payload['team_data']
    
    mgr.state[client_id]['team'] = payload.get('my_team')  # 'team_a' or 'team_b'
    mgr.state[client_id]['is_captain'] = payload.get('is_captain', False)
    
    print(f"[PUG TEAMS] Teams assigned - Player is on {payload.get('my_team', 'unknown')}, captain: {payload.get('is_captain', False)}")
    
    await mgr.send(ws, 'teams_assigned', team_data)


@on("map_selected")
async def handle_map_selected(payload: dict, client_id: int, ws, mgr):
    """Final map has been selected after veto."""
    selected_map = payload['map']
    
    print(f"[VETO] Map selected: {selected_map}")
    
    await mgr.send(ws, 'map_selected', {
        'map': selected_map,
        'message': f'Map: {selected_map}'
    })

