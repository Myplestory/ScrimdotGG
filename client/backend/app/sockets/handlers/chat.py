"""
Chat and messaging event handlers.
"""
from datetime import datetime
from quart import current_app
from ..events import on

@on("lobby_chat")
async def handle_lobby_chat(payload: dict, client_id: int, ws, mgr):
    """Send lobby chat message."""
    lobby_id = payload.get('lobby_id')
    if not lobby_id:
        await mgr.send(ws, 'error', {'message': "Not in a lobby"})
        return
    
    message = payload.get('message')
    if not message:
        return
    
    valorant_service = current_app.valorant
    
    # Get player name for the message
    puuid = mgr.state[client_id].get('puuid')
    
    await valorant_service.api.send_lobby_message({
        'message': message,
        'lobby_id': lobby_id,
        'userAlias': puuid or 'Anonymous',  # TODO: Get actual alias
        'timestamp': payload.get('timestamp', datetime.now().isoformat())
    })
    
    # Echo back to sender (Django will broadcast to others)
    await mgr.send(ws, 'lobby_message', {
        'username': puuid or 'Anonymous',
        'message': message,
        'timestamp': payload.get('timestamp', datetime.now().isoformat())
    })


@on("direct_message")
async def handle_direct_message(payload: dict, client_id: int, ws, mgr):
    """Send direct message to a specific player."""
    # Stub implementation - can be expanded
    pass

