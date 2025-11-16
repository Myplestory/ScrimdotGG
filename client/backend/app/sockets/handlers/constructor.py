"""
Constructor-specific event handlers.
Handles custom game creation, starting, and execution for constructor clients.
"""
from quart import current_app
from ..events import on
from ...utils.logger import get_logger

logger = get_logger(__name__)


@on("match_construction_started")
async def handle_match_construction_started(payload: dict, client_id: int, ws, mgr):
    """
    Django server notifies that construction/lobby creation is starting.
    If this client is constructor, create custom game.
    Otherwise, wait for join instruction.
    """
    match_id = payload.get('match_id')
    is_constructor = payload.get('is_constructor', False)
    map_name = payload.get('map')
    server = payload.get('server')
    team = payload.get('team')
    
    logger.info(f"[MATCH_CONSTRUCTION] Match {match_id[:8] if match_id else 'Unknown'} entering construction phase")
    logger.info(f"[MATCH_CONSTRUCTION] Constructor: {is_constructor}, Map: {map_name}, Server: {server}, Team: {team}")
    
    # Stop heartbeat - user entering game
    mgr.state[client_id]['in_game'] = True
    
    # Notify frontend
    await mgr.send(ws, 'match_construction_started', {
        'match_id': match_id,
        'is_constructor': is_constructor,
        'map': map_name,
        'server': server,
        'team': team
    })
    
    # Handle constructor game creation via service
    if is_constructor:
        valorant_service = current_app.valorant
        await valorant_service.create_custom_game(match_id, map_name, server, team)


@on("all_players_joined")
async def handle_all_players_joined(payload: dict, client_id: int, ws, mgr):
    """
    Server confirms all 10 players have joined.
    Constructor can now start the game.
    """
    match_id = payload.get('match_id')
    is_constructor = payload.get('is_constructor', False)
    
    logger.info(f"All players joined match {match_id}")
    
    # Handle constructor game start via service
    if is_constructor:
        valorant_service = current_app.valorant
        await valorant_service.start_custom_game(match_id)
    
    # Notify frontend
    await mgr.send(ws, 'all_players_joined', {
        'match_id': match_id,
        'is_constructor': is_constructor
    })

