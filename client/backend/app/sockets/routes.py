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
    print(f"[WS] New WebSocket connection attempt")
    mgr = current_app.conn_mgr
    ws = websocket._get_current_object()
    client_id = mgr.add(ws)
    
    print(f"[WS] Client {client_id} added to manager")
    await mgr.send(ws, 'connected', {'message': 'Connected to Scrim.GG client service'})
    print(f"[WS] Sent connected message to client {client_id}")
    
    try:
        while True:
            message = await ws.receive()
            print(f"[WS] Raw message received: {message}")
            # Parse and validate message
            try:
                envelope = Envelope.model_validate_json(message)
                print(f"[WS] Parsed envelope: {envelope.event}")
            except Exception as e:
                print(f"[WS] Parse error: {e}")
                await mgr.send(ws, 'error', {'message': f'Invalid message format: {str(e)}'})
                continue
            
            print(f"[RECV] Received: {envelope.event}")
            
            # Route to handler
            handler = get_handler(envelope.event)
            if not handler:
                print(f"[WS] No handler for event: {envelope.event}")
                await mgr.send(ws, 'error', {'message': f'Unknown event: {envelope.event}'})
                continue
            
            try:
                print(f"[WS] Calling handler for {envelope.event}")
                await handler(envelope.payload or {}, client_id, ws, mgr)
                print(f"[WS] Handler completed for {envelope.event}")
            except Exception as e:
                print(f"[ERROR] Handler error for {envelope.event}: {e}")
                import traceback
                traceback.print_exc()
                await mgr.send(ws, 'error', {'message': f'Error handling {envelope.event}: {str(e)}'})
    
    finally:
        was_in_game = mgr.state.get(client_id, {}).get('in_game', False)
        await mgr.remove(ws)
        print(f"[DISCONNECT] Client {client_id} disconnected")

