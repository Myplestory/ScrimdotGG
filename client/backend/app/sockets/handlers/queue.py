"""
Queue and matchmaking event handlers.
"""
from quart import current_app
from ..events import on

@on("join_pug_queue")
async def handle_join_pug_queue(payload: dict, client_id: int, ws, mgr):
    """Player joins PUG queue (solo or with party)."""
    if not mgr.state[client_id]['authenticated']:
        await mgr.send(ws, 'error', {'message': 'Not authenticated'})
        return
    
    try:
        valorant_service = current_app.valorant
        puuid = mgr.state[client_id]['puuid']
        
        # Create a lobby for this player (Django will handle if one already exists)
        print(f"[PUG QUEUE] Creating lobby for player {puuid}")
        create_result = await valorant_service.create_lobby()
        
        print(f"[DEBUG] create_lobby response: {create_result}")
        
        if create_result and create_result.get('status') == 'success':
            lobby_id = create_result['data']['id']
            print(f"[PUG QUEUE] Got lobby {lobby_id}")
        else:
            print(f"[ERROR] Invalid lobby response: {create_result}")
            await mgr.send(ws, 'error', {'message': "Failed to create/get lobby"})
            return
        
        # Get player data for queue
        player_data = {
            'puuid': puuid,
            'lobby_id': lobby_id,
            'queue_type': payload.get('queue_type', 'pug'),  # 'pug' or 'scrim'
            'party_id': payload.get('party_id', None),  # If queuing with friends
            'preferred_maps': payload.get('preferred_maps', []),
            'elo_range': payload.get('elo_range', None),  # For scrims
        }
        
        print(f"[PUG QUEUE] Player {puuid} joining {player_data['queue_type']} queue")
        
        # Update lobby preferences before sending to queue
        if player_data['preferred_maps']:
            print(f"[PUG QUEUE] Updating lobby map preferences: {player_data['preferred_maps']}")
            update_result = await valorant_service.api.pugsocket.send_message('update_lobby_preferences', {
                'lobby_id': lobby_id,
                'requester_puuid': puuid,
                'map_preferences': player_data['preferred_maps'],
                'server_preferences': payload.get('preferred_servers', [])
            })
            print(f"[PUG QUEUE] Lobby preferences update result: {update_result}")
        
        # Send to Django matchmaking service
        django_data = {
            'lobby_id': player_data['lobby_id'],
            'requester_puuid': player_data['puuid'],
            'queue_type': player_data['queue_type']
        }
        await valorant_service.api.pugsocket.send_message('add_lobby_to_queue', django_data)
        
        # Update local state
        mgr.state[client_id]['in_queue'] = True
        mgr.state[client_id]['queue_type'] = player_data['queue_type']
        mgr.state[client_id]['lobby_id'] = player_data['lobby_id']
        
        await mgr.send(ws, 'queue_joined', {
            'queue_type': player_data['queue_type'],
            'estimated_wait': 60  # Django will calculate this
        })
        
    except Exception as e:
        await mgr.send(ws, 'error', {'message': f"Failed to join queue: {str(e)}"})

@on("leave_pug_queue")
async def handle_leave_pug_queue(payload: dict, client_id: int, ws, mgr):
    """Player leaves PUG queue."""
    if not mgr.state[client_id]['authenticated']:
        await mgr.send(ws, 'error', {'message': 'Not authenticated'})
        return
    
    try:
        valorant_service = current_app.valorant
        
        # Get stored lobby_id from client state
        lobby_id = mgr.state[client_id].get('lobby_id')
        
        if not lobby_id:
            await mgr.send(ws, 'error', {'message': "No lobby found to leave"})
            return
        
        # Send to Django matchmaking service
        django_data = {
            'lobby_id': lobby_id,
            'requester_puuid': mgr.state[client_id]['puuid']
        }
        await valorant_service.api.pugsocket.send_message('remove_lobby_from_queue', django_data)
        
        mgr.state[client_id]['in_queue'] = False
        mgr.state[client_id]['queue_type'] = None
        
        await mgr.send(ws, 'queue_left', {})
        print(f"[PUG QUEUE] Player {mgr.state[client_id]['puuid']} left queue")
        
    except Exception as e:
        await mgr.send(ws, 'error', {'message': f"Failed to leave queue: {str(e)}"})

