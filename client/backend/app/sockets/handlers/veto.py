"""
Veto system event handlers.
"""
from quart import current_app
from ..events import on

@on("veto_map")
async def handle_veto_map(payload: dict, client_id: int, ws, mgr):
    """Forward veto_map events from frontend to Django backend."""
    try:
        match_id = payload.get('match_id')
        map_name = payload.get('map_name')
        
        print(f"[VETO_MAP] Forwarding veto request - Match: {match_id}, Map: {map_name}")
        
        valorant_service = current_app.valorant
        
        # Forward to Django backend via ValorantAPI
        if valorant_service and hasattr(valorant_service.api, 'pugsocket') and valorant_service.api.pugsocket:
            await valorant_service.api.pugsocket.send_message('veto_map', payload)
            print(f"[VETO_MAP] Successfully forwarded veto request to Django backend")
        else:
            print(f"[VETO_MAP] ERROR: ValorantAPI or pugsocket not available")
            await mgr.send(ws, 'error', {'message': "Backend connection not available"})
            
    except Exception as e:
        print(f"[VETO_MAP] Error handling veto_map: {e}")
        await mgr.send(ws, 'error', {'message': f"Failed to process veto request: {str(e)}"})


@on("veto_update")
async def handle_veto_update(payload: dict, client_id: int, ws, mgr):
    """Receive veto updates from Django."""
    veto_state = payload.get('veto_state', payload)
    
    print(f"[VETO] Update - {veto_state.get('current_turn', 'unknown')} is {veto_state.get('action', 'unknown')}ing")
    
    await mgr.send(ws, 'veto_update', veto_state)


@on("veto_complete")
async def handle_veto_complete(payload: dict, client_id: int, ws, mgr):
    """Handle veto completion event from Django."""
    try:
        final_map = payload.get('final_map')
        match_id = payload.get('match_id')
        print(f"[VETO_COMPLETE] Veto phase completed - Match: {match_id}, Final map: {final_map}")
        
        await mgr.send(ws, 'veto_complete', payload)
    except Exception as e:
        print(f"[VETO_COMPLETE] Error handling veto_complete: {e}")
        await mgr.send(ws, 'error', {'message': f"Failed to process veto completion: {str(e)}"})


@on("veto_acknowledged")
async def handle_veto_acknowledged(payload: dict, client_id: int, ws, mgr):
    """Handle veto acknowledgment event from Django."""
    try:
        match_id = payload.get('match_id')
        map_name = payload.get('map_name')
        print(f"[VETO_ACKNOWLEDGED] Veto acknowledged - Match: {match_id}, Map: {map_name}")
        
        await mgr.send(ws, 'veto_acknowledged', payload)
    except Exception as e:
        print(f"[VETO_ACKNOWLEDGED] Error handling veto_acknowledged: {e}")
        await mgr.send(ws, 'error', {'message': f"Failed to process veto acknowledgment: {str(e)}"})

