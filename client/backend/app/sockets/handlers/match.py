"""
Match lifecycle event handlers.
"""
from quart import current_app
from ..events import on
from ...utils.logger import get_logger

logger = get_logger(__name__)

@on("accept_match")
async def handle_accept_match(payload: dict, client_id: int, ws, mgr):
    """Accept a found match."""
    match_id = payload.get('match_id')
    if not match_id:
        logger.warning(f"[ACCEPT_MATCH] No match ID provided")
        await mgr.send(ws, 'error', {'message': "No match ID provided"})
        return
    
    puuid = mgr.state[client_id].get('puuid')
    logger.info(f"[ACCEPT_MATCH] Player {puuid[:8] if puuid else 'Unknown'}... accepting match {match_id[:8]}...")
    
    valorant_service = current_app.valorant
    # Send acceptance to Django server
    await valorant_service.api.pugsocket.send_message('accept_match', {
        'match_id': match_id,
        'puuid': puuid
    })
    
    mgr.state[client_id]['match_id'] = match_id
    logger.info(f"[ACCEPT_MATCH] Successfully sent acceptance to Django, notifying frontend")
    
    await mgr.send(ws, 'match_accepted', {
        'match_id': match_id
    })


@on("decline_match")
async def handle_decline_match(payload: dict, client_id: int, ws, mgr):
    """Decline a found match."""
    match_id = payload.get('match_id')
    if not match_id:
        logger.warning(f"[DECLINE_MATCH] No match ID provided")
        return
    
    puuid = mgr.state[client_id].get('puuid')
    logger.info(f"[DECLINE_MATCH] Player {puuid[:8] if puuid else 'Unknown'}... declining match {match_id[:8]}...")
    
    valorant_service = current_app.valorant
    await valorant_service.api.pugsocket.send_message('decline_match', {
        'match_id': match_id,
        'puuid': puuid
    })
    
    logger.info(f"[DECLINE_MATCH] Successfully sent decline to Django")


@on("match_started")
async def handle_match_started(payload: dict, client_id: int, ws, mgr):
    """
    Handle match start event from Django server.
    Sets user as in-game and stops heartbeat.
    """
    match_id = payload.get('match_id')
    logger.info(f"[MATCH_STARTED] Match {match_id[:8] if match_id else 'Unknown'}... started for client {client_id}")
    
    mgr.state[client_id]['in_game'] = True
    mgr.state[client_id]['match_id'] = match_id
    
    logger.info(f"[MATCH_STARTED] Client {client_id} now in-game, notifying frontend")
    await mgr.send(ws, 'match_started', payload)


@on("match_ended")
async def handle_match_ended(payload: dict, client_id: int, ws, mgr):
    """
    Handle match end event from Django server or client.
    Sets user as not in-game and restarts heartbeat.
    """
    logger.info(f"Match ended for client {client_id}")
    
    # Reset validation state
    valorant_service = current_app.valorant
    valorant_service.api.reset_pregame_validation()
    
    mgr.state[client_id]['in_game'] = False
    mgr.state[client_id]['match_id'] = None
    
    await mgr.send(ws, 'match_ended', payload)


@on("match_cancelled")
async def handle_match_cancelled(payload: dict, client_id: int, ws, mgr):
    """
    Handle match cancellation due to timeout or other issues.
    """
    match_id = payload.get('match_id')
    reason = payload.get('reason', 'unknown')
    
    logger.warning(f"Match {match_id} cancelled: {reason}")
    
    # Reset validation state
    valorant_service = current_app.valorant
    valorant_service.api.reset_pregame_validation()
    
    # Clear any pending game start data
    if hasattr(valorant_service.api, '_pending_game_start'):
        valorant_service.api._pending_game_start = None
    
    # Set user as not in-game
    mgr.state[client_id]['in_game'] = False
    mgr.state[client_id]['match_id'] = None
    
    # Notify frontend
    await mgr.send(ws, 'match_cancelled', {
        'match_id': match_id,
        'reason': reason,
        'message': f'Match cancelled: {reason}'
    })


@on("join_custom_game")
async def handle_join_custom_game(payload: dict, client_id: int, ws, mgr):
    """
    Django server instructs this client to join the custom game.
    Non-constructor players join the pregame created by constructor.
    """
    match_id = payload.get('match_id')
    pregame_id = payload.get('pregame_id')
    team = payload.get('team')
    
    logger.info(f"Joining custom game: {pregame_id} for match {match_id}")
    
    valorant_service = current_app.valorant
    
    # VALIDATION: Validate pregame_id before attempting to join
    if not valorant_service.api._validate_pregame_id(pregame_id, 'join_custom_game', match_id):
        error_msg = (
            f"[VALIDATION] CRITICAL: Received mismatched pregame_id in join_custom_game. "
            f"Expected: {valorant_service.api.expected_pregame_id[:8] if valorant_service.api.expected_pregame_id else 'None'}, "
            f"Received: {pregame_id[:8] if pregame_id else 'None'}. "
            "Aborting join attempt."
        )
        logger.error(error_msg)
        
        # Notify server of validation failure
        await valorant_service.api.pugsocket.send_message('player_join_failed', {
            'match_id': match_id,
            'player_puuid': valorant_service.api.client.puuid,
            'team': team,
            'error': f'Pregame ID validation failed: {error_msg}'
        })
        
        # Notify frontend of error
        await mgr.send(ws, 'join_custom_game_failed', {
            'match_id': match_id,
            'team': team,
            'error': 'Pregame ID mismatch detected'
        })
        return  # Don't proceed with join
    
    try:
        # Join the party/pregame with timeout
        logger.info(f"Attempting to join pregame {pregame_id}...")
        join_result = valorant_service.api.client.party_join(pregame_id)
        
        if join_result:
            logger.info(f"Successfully joined pregame {pregame_id}")
            
            # VALIDATION: Before notifying server of successful join, validate again
            if not valorant_service.api._validate_pregame_id(pregame_id, 'player_joined_game', match_id):
                logger.warning(
                    f"[VALIDATION] Validation warning after join, but proceeding with notification"
                )
            
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
            
            logger.info(f"Successfully joined match {match_id}")
        else:
            raise Exception("Failed to join pregame - no response from Valorant")
        
    except Exception as e:
        logger.error(f"Error joining custom game: {str(e)}")
        
        # Notify server of join failure
        try:
            await valorant_service.api.pugsocket.send_message('player_join_failed', {
                'match_id': match_id,
                'player_puuid': valorant_service.api.client.puuid,
                'team': team,
                'error': str(e)
            })
        except Exception as notify_error:
            logger.error(f"Failed to notify server of join error: {notify_error}")
        
        # Notify frontend of join failure
        await mgr.send(ws, 'join_custom_game_failed', {
            'match_id': match_id,
            'team': team,
            'error': str(e),
            'message': 'Failed to join custom game'
        })


@on("match_in_progress")
async def handle_match_in_progress(payload: dict, client_id: int, ws, mgr):
    """Match is now live - all players have loaded in."""
    match_id = payload.get('match_id')
    
    logger.info(f"Match {match_id} is now in progress")
    
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
    logger.info("Match completed")
    
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
        logger.error(f"Match found event missing match_id: {payload}")
        return
    
    # Update state
    mgr.state[client_id]['pending_match'] = match_id
    mgr.state[client_id]['in_queue'] = False
    
    logger.info(f"Match found! ID: {match_id}, Timeout: {timeout_seconds}s")
    
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
    
    logger.info(f"Teams assigned - Player is on {payload.get('my_team', 'unknown')}, captain: {payload.get('is_captain', False)}")
    
    await mgr.send(ws, 'teams_assigned', team_data)


@on("map_selected")
async def handle_map_selected(payload: dict, client_id: int, ws, mgr):
    """Final map has been selected after veto."""
    selected_map = payload['map']
    
    logger.info(f"Map selected: {selected_map}")
    
    await mgr.send(ws, 'map_selected', {
        'map': selected_map,
        'message': f'Map: {selected_map}'
    })


@on("side_selected")
async def handle_side_selected(payload: dict, client_id: int, ws, mgr):
    """Handle side selection event from Django server."""
    match_id = payload.get('match_id')
    side = payload.get('side')
    selected_by = payload.get('selected_by')
    side_complete = payload.get('side_complete', False)
    
    logger.info(f"Side selected: {side} by {selected_by} for match {match_id[:8] if match_id else 'Unknown'}")
    
    # Notify frontend
    await mgr.send(ws, 'side_selected', {
        'match_id': match_id,
        'side': side,
        'selected_by': selected_by,
        'side_complete': side_complete,
        'message': f'Side selected: {side}'
    })

@on("match_state_update")
async def handle_match_state_update(payload: dict, client_id: int, ws, mgr):
    """Forward unified match state updates to frontend clients."""
    logger.debug(f"[MATCH STATE UPDATE] Forwarding snapshot for match {payload.get('match_id')}")
    await mgr.send(ws, 'match_state_update', payload)

@on("side_acknowledged")
async def handle_side_acknowledged(payload: dict, client_id: int, ws, mgr):
    """Handle side selection acknowledgment from Django server."""
    status = payload.get('status')
    side = payload.get('side')
    selected_by = payload.get('selected_by')
    side_complete = payload.get('side_complete', False)
    match_ready = payload.get('match_ready', False)
    
    logger.info(f"Side acknowledged: {side} by {selected_by}, complete: {side_complete}, ready: {match_ready}")
    
    # Notify frontend
    await mgr.send(ws, 'side_acknowledged', {
        'status': status,
        'side': side,
        'selected_by': selected_by,
        'side_complete': side_complete,
        'match_ready': match_ready,
        'message': f'Side {side} acknowledged'
    })

