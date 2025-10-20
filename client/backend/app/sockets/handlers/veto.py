"""
Veto system event handlers.
"""
from quart import current_app
from ..events import on

@on("veto_server")
async def handle_veto_server(payload: dict, client_id: int, ws, mgr):
    """Forward veto_server events from frontend to Django backend."""
    try:
        match_id = payload.get('match_id')
        server_name = payload.get('server_name')
        
        print(f"[VETO_SERVER] Forwarding server veto request - Match: {match_id}, Server: {server_name}")
        
        valorant_service = current_app.valorant
        
        # Forward to Django backend via ValorantAPI
        if valorant_service and hasattr(valorant_service.api, 'pugsocket') and valorant_service.api.pugsocket:
            await valorant_service.api.pugsocket.send_message('veto_server', payload)
            print(f"[VETO_SERVER] Successfully forwarded server veto to Django backend")
        else:
            print(f"[VETO_SERVER] ERROR: ValorantAPI or pugsocket not available")
            await mgr.send(ws, 'error', {'message': "Backend connection not available"})
            
    except Exception as e:
        print(f"[VETO_SERVER] Error handling veto_server: {e}")
        await mgr.send(ws, 'error', {'message': f"Failed to process server veto: {str(e)}"})


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


@on("server_veto_started")
async def handle_server_veto_started(payload: dict, client_id: int, ws, mgr):
    """Receive server veto started event from Django."""
    try:
        match_id = payload.get('match_id')
        current_turn = payload.get('current_turn')
        print(f"[SERVER_VETO_STARTED] Server veto started - Match: {match_id}, Turn: {current_turn}")
        
        await mgr.send(ws, 'server_veto_started', payload)
    except Exception as e:
        print(f"[SERVER_VETO_STARTED] Error handling server_veto_started: {e}")


@on("server_veto_update")
async def handle_server_veto_update(payload: dict, client_id: int, ws, mgr):
    """Receive server veto updates from Django."""
    try:
        server_name = payload.get('server_name')
        next_turn = payload.get('next_turn')
        print(f"[SERVER_VETO_UPDATE] Server {server_name} vetoed, next turn: {next_turn}")
        
        await mgr.send(ws, 'server_veto_update', payload)
    except Exception as e:
        print(f"[SERVER_VETO_UPDATE] Error handling server_veto_update: {e}")


@on("server_vetoed")
async def handle_server_vetoed(payload: dict, client_id: int, ws, mgr):
    """Receive server vetoed event from Django."""
    try:
        server_name = payload.get('server_name')
        vetoed_by = payload.get('vetoed_by')
        print(f"[SERVER_VETOED] Server {server_name} vetoed by {vetoed_by}")
        
        await mgr.send(ws, 'server_vetoed', payload)
    except Exception as e:
        print(f"[SERVER_VETOED] Error handling server_vetoed: {e}")


@on("server_veto_complete")
async def handle_server_veto_complete(payload: dict, client_id: int, ws, mgr):
    """Handle server veto completion event from Django."""
    try:
        final_server = payload.get('final_server')
        match_id = payload.get('match_id')
        print(f"[SERVER_VETO_COMPLETE] Server veto completed - Match: {match_id}, Final server: {final_server}")
        
        await mgr.send(ws, 'server_veto_complete', payload)
    except Exception as e:
        print(f"[SERVER_VETO_COMPLETE] Error handling server_veto_complete: {e}")


@on("server_veto_acknowledged")
async def handle_server_veto_acknowledged(payload: dict, client_id: int, ws, mgr):
    """Handle server veto acknowledgment event from Django."""
    try:
        match_id = payload.get('match_id')
        server_name = payload.get('server_name')
        print(f"[SERVER_VETO_ACKNOWLEDGED] Server veto acknowledged - Match: {match_id}, Server: {server_name}")
        
        await mgr.send(ws, 'server_veto_acknowledged', payload)
    except Exception as e:
        print(f"[SERVER_VETO_ACKNOWLEDGED] Error handling server_veto_acknowledged: {e}")


@on("server_veto_timeout")
async def handle_server_veto_timeout(payload: dict, client_id: int, ws, mgr):
    """Handle server veto timeout event from Django."""
    try:
        match_id = payload.get('match_id')
        timed_out_team = payload.get('timed_out_team')
        auto_vetoed_server = payload.get('auto_vetoed_server')
        print(f"[SERVER_VETO_TIMEOUT] Team {timed_out_team} timed out - Auto-vetoed: {auto_vetoed_server}")
        
        await mgr.send(ws, 'server_veto_timeout', payload)
    except Exception as e:
        print(f"[SERVER_VETO_TIMEOUT] Error handling server_veto_timeout: {e}")


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


@on("map_vetoed")
async def handle_map_vetoed(payload: dict, client_id: int, ws, mgr):
    """Handle map vetoed event from Django."""
    try:
        match_id = payload.get('match_id')
        map_name = payload.get('map_name')
        vetoed_by = payload.get('vetoed_by')
        next_turn = payload.get('next_turn')
        remaining_maps = payload.get('remaining_maps', [])
        
        print(f"[MAP_VETOED] Map {map_name} vetoed by {vetoed_by} - Match: {match_id}")
        print(f"[MAP_VETOED] Next turn: {next_turn}, Remaining maps: {remaining_maps}")
        
        await mgr.send(ws, 'map_vetoed', payload)
    except Exception as e:
        print(f"[MAP_VETOED] Error handling map_vetoed: {e}")
        await mgr.send(ws, 'error', {'message': f"Failed to process map vetoed event: {str(e)}"})


@on("select_side")
async def handle_select_side(payload: dict, client_id: int, ws, mgr):
    """Forward select_side events from frontend to Django backend."""
    try:
        match_id = payload.get('match_id')
        side = payload.get('side')
        
        print(f"[SELECT_SIDE] Forwarding side selection - Match: {match_id}, Side: {side}")
        
        valorant_service = current_app.valorant
        
        # Forward to Django backend via ValorantAPI
        if valorant_service and hasattr(valorant_service.api, 'pugsocket') and valorant_service.api.pugsocket:
            await valorant_service.api.pugsocket.send_message('select_side', payload)
            print(f"[SELECT_SIDE] Successfully forwarded side selection to Django backend")
        else:
            print(f"[SELECT_SIDE] ERROR: ValorantAPI or pugsocket not available")
            await mgr.send(ws, 'error', {'message': "Backend connection not available"})
            
    except Exception as e:
        print(f"[SELECT_SIDE] Error handling select_side: {e}")
        await mgr.send(ws, 'error', {'message': f"Failed to process side selection: {str(e)}"})
