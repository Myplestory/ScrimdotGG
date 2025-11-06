"""
Status and connection event handlers.
"""
from quart import current_app
from ..events import on

@on("connected")
async def handle_connected(payload: dict, client_id: int, ws, mgr):
    """Handle client connection - send initial status."""
    # Send initial status immediately when client connects
    await handle_get_status(payload, client_id, ws, mgr)

@on("get_status")
async def handle_get_status(payload: dict, client_id: int, ws, mgr):
    """Get current system status (backend + Valorant)."""
    try:
        valorant_service = current_app.valorant
        valorant_status = await valorant_service.check_status()
        status = {
            'backend_connected': True,
            'valorant': valorant_status,
            'authenticated': mgr.state[client_id].get('authenticated', False)
        }
        await mgr.send(ws, 'status_update', status)
    except Exception as e:
        print(f"[STATUS] Error getting status: {e}")
        import traceback
        traceback.print_exc()
        await mgr.send(ws, 'error', {'message': f"Error getting status: {str(e)}"})

