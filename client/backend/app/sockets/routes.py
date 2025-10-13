"""
WebSocket endpoint - thin routing layer.
"""
from quart import Blueprint, websocket, current_app
from ..models.messages import Envelope
from .events import get_handler

ws_bp = Blueprint("ws", __name__)

@ws_bp.websocket('/ws')
async def ws_endpoint():
    """Main WebSocket endpoint for frontend communication."""
    mgr = current_app.conn_mgr
    ws = websocket._get_current_object()
    client_id = mgr.add(ws)
    
    await mgr.send(ws, 'connected', {'message': 'Connected to Scrim.GG client service'})
    
    try:
        while True:
            message = await ws.receive()
            # Parse and validate message
            try:
                envelope = Envelope.model_validate_json(message)
            except Exception as e:
                await mgr.send(ws, 'error', {'message': f'Invalid message format: {str(e)}'})
                continue
            
            # Route to handler
            handler = get_handler(envelope.event)
            if not handler:
                await mgr.send(ws, 'error', {'message': f'Unknown event: {envelope.event}'})
                continue
            
            try:
                await handler(envelope.payload or {}, client_id, ws, mgr)
            except Exception as e:
                print(f"[ERROR] Handler error for {envelope.event}: {e}")
                import traceback
                traceback.print_exc()
                await mgr.send(ws, 'error', {'message': f'Error handling {envelope.event}: {str(e)}'})
    
    finally:
        await mgr.remove(ws)

