"""
Status and connection event handlers.
"""
from quart import current_app
from ..events import on

@on("connected")
async def handle_connected(payload: dict, client_id: int, ws, mgr):
    """Handle client connection - send initial status."""
    print(f"[CONNECT] Client {client_id} connected")
    
    # Send initial status immediately when client connects
    print(f"[CONNECT] Sending initial status to client {client_id}")
    await handle_get_status(payload, client_id, ws, mgr)
    print(f"[CONNECT] Initial status sent to client {client_id}")

@on("get_status")
async def handle_get_status(payload: dict, client_id: int, ws, mgr):
    """Get current system status (backend + Valorant)."""
    try:
        print(f"[STATUS] Getting status for client {client_id}")
        valorant_service = current_app.valorant
        valorant_status = await valorant_service.check_status()
        status = {
            'backend_connected': True,
            'valorant': valorant_status,
            'authenticated': mgr.state[client_id].get('authenticated', False)
        }
        print(f"[STATUS] Sending status to client {client_id}: {status}")
        await mgr.send(ws, 'status_update', status)
        print(f"[STATUS] Status sent successfully to client {client_id}")
    except Exception as e:
        print(f"[STATUS] Error getting status: {e}")
        import traceback
        traceback.print_exc()
        await mgr.send(ws, 'error', {'message': f"Error getting status: {str(e)}"})

