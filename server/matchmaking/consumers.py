import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async
from django.db.models import Avg
from django.apps import apps
from datetime import datetime
import logging

# UTILITY
from .queue_manager import QueueManager
from .matchmaker import Matchmaker
from .match_confirmation import MatchConfirmationManager
from .match_manager import MatchManager
from .match_state_validator import MatchStateValidator
from .lobby_manager import LobbyManager
from scrimgg.serializers import LobbySerializer, PlayerSerializer
from match_system.phases.execution import ExecutionPhaseManager

logger = logging.getLogger(__name__)


class PugSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Called when a WebSocket handshake is initiated.
        """
        self.puuid = self.scope["url_route"]["kwargs"]["puuid"]
        self.player_group_name = f"player_{self.puuid}"
        await self.channel_layer.group_add(self.player_group_name, self.channel_name)
        Player = apps.get_model('scrimgg', 'Player')
        Lobby = apps.get_model('scrimgg', 'Lobby')
        try:
            player = await sync_to_async(Player.objects.get)(puuid=self.puuid)
            lobby = await sync_to_async(lambda: Lobby.objects.filter(players=player, is_active=True).first())()
            if lobby:
                self.lobby_group_name = f"lobby_{lobby.id}"
                await self.channel_layer.group_add(self.lobby_group_name, self.channel_name)
                logger.info(f"WebSocket added to lobby group: {self.lobby_group_name}")
        except Exception as e:
            logger.error(f"Error during WebSocket connect: {e}")
        await self.accept()
        logger.info(f"WebSocket connected: PUUID = {self.puuid[:12]}...")

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection. Removes the connection from the assigned groups
        and cleans up the user's lobby if they are the lobby leader.
        """
        try:
            # Clean up lobby if user is lobby leader
            if hasattr(self, 'puuid') and self.puuid:
                await self._cleanup_user_lobby()
        except Exception as e:
            logger.error(f"Error during lobby cleanup on disconnect: {e}")
        finally:
            # Always remove from WebSocket groups
            await self.channel_layer.group_discard(self.player_group_name, self.channel_name)
            if hasattr(self, 'lobby_group_name') and self.lobby_group_name:
                await self.channel_layer.group_discard(self.lobby_group_name, self.channel_name)
            logger.info(f"WebSocket disconnected: PUUID = {self.puuid[:12]}...")
    
    async def _cleanup_user_lobby(self):
        """
        Clean up user's lobby when they disconnect.
        Only destroys lobby if user is the lobby leader.
        """
        try:
            Player = apps.get_model('scrimgg', 'Player')
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            def get_player_and_lobby():
                try:
                    player = Player.objects.get(puuid=self.puuid)
                    lobby = Lobby.objects.select_related('lobby_leader').filter(
                        players=player, 
                        is_active=True
                    ).first()
                    return player, lobby
                except Player.DoesNotExist:
                    return None, None
            
            player, lobby = await sync_to_async(get_player_and_lobby)()
            
            if not player or not lobby:
                return
            
            # Only handle lobby if user is the lobby leader
            if lobby.lobby_leader.puuid == self.puuid:
                lobby_id = lobby.id
                lobby_size = lobby.size
                
                # Check if this is a solo lobby or a party
                if lobby_size == 1:
                    # Solo lobby - destroy it
                    logger.info(f"User {player.alias} is solo lobby leader, destroying lobby {lobby.id}")
                    
                    # Remove lobby from queue if it's queued
                    from .queue_manager import QueueManager
                    queue_result = await QueueManager.leave_queue(str(lobby.id), self.puuid, 'pug')
                    if queue_result.get('status') == 'success':
                        logger.info(f"Removed lobby {lobby.id} from queue")
                    
                    # Destroy the lobby
                    await sync_to_async(lobby.delete)()
                    logger.info(f"Destroyed lobby {lobby_id}")
                    
                    # Broadcast lobby destruction
                    await self.channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'lobby_destroyed',
                            'message': 'Lobby was destroyed because the leader disconnected',
                            'reason': 'leader_disconnect'
                        }
                    )
                else:
                    # Party lobby - transfer leadership
                    logger.info(f"User {player.alias} is party leader ({lobby_size} players), transferring leadership")
                    
                    def transfer_leadership():
                        # Get all players except the disconnecting leader
                        remaining_players = list(lobby.players.exclude(puuid=self.puuid))
                        
                        if remaining_players:
                            # Transfer to first remaining player (could be based on other criteria)
                            new_leader = remaining_players[0]
                            lobby.lobby_leader = new_leader
                            lobby.players.remove(player)
                            lobby.size = lobby.players.count()
                            lobby.save()
                            logger.info(f"Leadership transferred to {new_leader.alias}")
                            return new_leader
                        else:
                            # No remaining players, destroy lobby
                            lobby.delete()
                            return None
                    
                    new_leader = await sync_to_async(transfer_leadership)()
                    
                    if new_leader:
                        # Broadcast leadership change
                        await self.channel_layer.group_send(
                            f"lobby_{lobby_id}",
                            {
                                'type': 'lobby_leader_changed',
                                'new_leader': {
                                    'puuid': new_leader.puuid,
                                    'alias': new_leader.alias
                                },
                                'old_leader': {
                                    'puuid': player.puuid,
                                    'alias': player.alias
                                },
                                'message': f'{new_leader.alias} is now the lobby leader'
                            }
                        )
                    else:
                        # Lobby destroyed because no players left
                        await self.channel_layer.group_send(
                            f"lobby_{lobby_id}",
                            {
                                'type': 'lobby_destroyed',
                                'message': 'Lobby was destroyed because no players remain',
                                'reason': 'no_players'
                            }
                        )
            else:
                logger.info(f"User {player.alias} is not lobby leader, leaving lobby {lobby.id}")
                # Just remove player from lobby (don't destroy it)
                def remove_player_from_lobby():
                    lobby.players.remove(player)
                    lobby.size = lobby.players.count()
                    lobby.save()
                
                await sync_to_async(remove_player_from_lobby)()
                
                # Broadcast player left to lobby members
                await self.channel_layer.group_send(
                    f"lobby_{lobby.id}",
                    {
                        'type': 'player_left_lobby',
                        'player': {
                            'puuid': player.puuid,
                            'alias': player.alias
                        },
                        'message': f'{player.alias} left the lobby'
                    }
                )
                
        except Exception as e:
            logger.exception(f"Error in _cleanup_user_lobby: {e}")

    async def receive(self, text_data):
        """
        Handles incoming WebSocket messages. Routes actions to their respective handlers.
        """
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get('event')
            
            # Lobby management events
            if action == 'create_lobby':
                await self.create_lobby(text_data_json)
            elif action == 'invite_to_lobby':
                await self.invite_to_lobby(text_data_json)
            elif action == 'kick_from_lobby':
                await self.kick_from_lobby(text_data_json)
            elif action == 'leave_lobby':
                await self.leave_lobby(text_data_json)
            elif action == 'update_lobby_preferences':
                await self.update_lobby_preferences(text_data_json)
            
            # Queue management events
            elif action == 'add_lobby_to_queue':
                await self.add_lobby_to_queue(text_data_json)
            elif action == 'remove_lobby_from_queue':
                await self.remove_lobby_from_queue(text_data_json)
            
            # Match events
            elif action == 'accept_match':
                await self.accept_match(text_data_json)
            elif action == 'decline_match':
                await self.decline_match(text_data_json)
            
            # Match page events
            elif action == 'get_match_data':
                await self.handle_get_match_data(text_data_json)
            elif action == 'veto_server':
                await self.handle_veto_server(text_data_json)
            elif action == 'veto_map':
                await self.handle_veto_map(text_data_json)
            elif action == 'select_side':
                await self.handle_select_side(text_data_json)
            
            # Match execution events
            elif action == 'custom_game_created':
                await self.handle_custom_game_created(text_data_json)
            elif action == 'player_joined_game':
                await self.handle_player_joined_game(text_data_json)
            elif action == 'player_join_failed':
                await self.handle_player_join_failed(text_data_json)
            elif action == 'match_started':
                await self.handle_match_started(text_data_json)
            elif action == 'match_score_update':
                await self.handle_match_score_update(text_data_json)
            elif action == 'match_completed':
                await self.handle_match_completed(text_data_json)
            elif action == 'request_rejoin':
                await self.handle_request_rejoin(text_data_json)
            elif action == 'get_match_statistics':
                await self.handle_get_match_statistics(text_data_json)
            
            # Queue status events
            elif action == 'get_queue_status':
                await self.get_queue_status(text_data_json)
            elif action == 'check_queue_eligibility':
                await self.check_queue_eligibility(text_data_json)
            
            # Player and chat events
            elif action == 'get_player_model':
                await self.get_player_model(text_data_json)
            elif action == 'lobby_message':
                await self.handle_lobby_message(text_data_json)
            
            else:
                await self.send(text_data=json.dumps({"error": "Invalid action"}))
                logger.warning(f"Unknown action received: {action}")
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))
            logger.error(f"Error handling WebSocket message: {str(e)}")

    # -------------------- WebSocket Event Handlers --------------------
    
    async def get_player_model(self, data):
        """
        Handles fetching the player model based on the provided PUUID.
        """
        Player = apps.get_model('scrimgg', 'Player')
        payload = data.get("payload")
        player_id = payload.get('puuid')
        if not player_id:
            await self.send(text_data=json.dumps({"error": "PUUID is required."}))
            logger.warning("get_player_model called without PUUID")
            return
        try:
            player = await sync_to_async(Player.objects.get)(puuid=player_id)
            logger.debug(f"Fetched Player: PK={player.pk}, PUUID={player.puuid[:12]}...")
            def serialize_player(player_instance):
                from scrimgg.serializers import PlayerSerializer
                return PlayerSerializer(player_instance).data
            serialized_player = await sync_to_async(serialize_player)(player)
            await self.send(text_data=json.dumps({
                "event": "player_model",
                "payload": serialized_player
            }))
        except Player.DoesNotExist:
            await self.send(text_data=json.dumps({"error": "Player not found."}))
            logger.warning(f"Player with PUUID={player_id[:12]}... not found")
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Unexpected error while fetching player: {str(e)}")

    async def create_lobby(self, data):
        """
        Handle lobby creation using LobbyManager.
        """
        payload = data.get("payload")
        player_id = payload.get('puuid')
        
        if not player_id:
            await self.send(text_data=json.dumps({"error": "Player ID is required."}))
            logger.error("Create lobby failed: Player ID is required")
            return
        
        try:
            # Use LobbyManager to create lobby
            result = await LobbyManager.create_lobby(player_id)
            
            if result['status'] == 'success':
                lobby_data = result['lobby']
                lobby_id = lobby_data['id']
                
                # Add WebSocket to lobby group
                self.lobby_group_name = f"lobby_{lobby_id}"
                await self.channel_layer.group_add(self.lobby_group_name, self.channel_name)
                logger.info(f"WebSocket added to lobby group: {self.lobby_group_name}")
                
                # Send lobby data to client
                await self.send(text_data=json.dumps({
                    "event": "lobby_created",
                    "payload": lobby_data
                }))
                
                # Broadcast lobby creation to lobby group
                await self.channel_layer.group_send(
                    self.lobby_group_name,
                    {
                        'type': 'lobby_updated',
                        'lobby': lobby_data
                    }
                )
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to create lobby')
                }))
                logger.error(f"Create lobby failed: {result.get('message')}")
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Unexpected error in create_lobby: {str(e)}")
    
    async def invite_to_lobby(self, data):
        """
        Handle inviting a player to lobby.
        """
        payload = data.get("payload")
        lobby_id = payload.get('lobby_id')
        player_puuid = payload.get('player_puuid')
        inviter_puuid = payload.get('inviter_puuid')
        
        if not all([lobby_id, player_puuid, inviter_puuid]):
            await self.send(text_data=json.dumps({
                "error": "lobby_id, player_puuid, and inviter_puuid are required"
            }))
            return
        
        try:
            result = await LobbyManager.add_player_to_lobby(lobby_id, player_puuid, inviter_puuid)
            
            if result['status'] == 'success':
                lobby_data = result['lobby']
                
                # Broadcast lobby update to all lobby members
                await self.channel_layer.group_send(
                    f"lobby_{lobby_id}",
                    {
                        'type': 'player_joined_lobby',
                        'lobby': lobby_data,
                        'player_puuid': player_puuid
                    }
                )
                
                # Send confirmation to inviter
                await self.send(text_data=json.dumps({
                    "event": "player_invited",
                    "payload": lobby_data
                }))
                
                logger.info(f"Player {player_puuid} invited to lobby {lobby_id}")
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to invite player')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error inviting to lobby: {str(e)}")
    
    async def kick_from_lobby(self, data):
        """
        Handle kicking a player from lobby.
        """
        payload = data.get("payload")
        lobby_id = payload.get('lobby_id')
        player_puuid = payload.get('player_puuid')
        kicker_puuid = payload.get('kicker_puuid')
        
        if not all([lobby_id, player_puuid, kicker_puuid]):
            await self.send(text_data=json.dumps({
                "error": "lobby_id, player_puuid, and kicker_puuid are required"
            }))
            return
        
        try:
            result = await LobbyManager.remove_player_from_lobby(lobby_id, player_puuid, kicker_puuid)
            
            if result['status'] == 'success':
                # Check if lobby was disbanded
                if result.get('lobby_disbanded'):
                    await self.channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'lobby_disbanded',
                            'reason': 'No players remaining'
                        }
                    )
                else:
                    lobby_data = result['lobby']
                    
                    # Notify kicked player
                    await self.channel_layer.group_send(
                        f"player_{player_puuid}",
                        {
                            'type': 'kicked_from_lobby',
                            'lobby_id': lobby_id,
                            'message': 'You were kicked from the lobby'
                        }
                    )
                    
                    # Broadcast lobby update to remaining members
                    await self.channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'player_left_lobby',
                            'lobby': lobby_data,
                            'player_puuid': player_puuid,
                            'reason': 'kicked'
                        }
                    )
                
                await self.send(text_data=json.dumps({
                    "event": "player_kicked",
                    "payload": result
                }))
                
                logger.info(f"Player {player_puuid} kicked from lobby {lobby_id}")
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to kick player')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error kicking from lobby: {str(e)}")
    
    async def leave_lobby(self, data):
        """
        Handle player leaving lobby.
        """
        payload = data.get("payload")
        lobby_id = payload.get('lobby_id')
        player_puuid = payload.get('player_puuid')
        
        if not all([lobby_id, player_puuid]):
            await self.send(text_data=json.dumps({
                "error": "lobby_id and player_puuid are required"
            }))
            return
        
        try:
            result = await LobbyManager.remove_player_from_lobby(lobby_id, player_puuid)
            
            if result['status'] == 'success':
                # Remove from lobby WebSocket group
                await self.channel_layer.group_discard(f"lobby_{lobby_id}", self.channel_name)
                
                # Check if lobby was disbanded
                if result.get('lobby_disbanded'):
                    await self.channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'lobby_disbanded',
                            'reason': 'No players remaining'
                        }
                    )
                else:
                    lobby_data = result['lobby']
                    
                    # Broadcast to remaining lobby members
                    await self.channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'player_left_lobby',
                            'lobby': lobby_data,
                            'player_puuid': player_puuid,
                            'reason': 'left'
                        }
                    )
                
                # Confirm to leaving player
                await self.send(text_data=json.dumps({
                    "event": "left_lobby",
                    "payload": result
                }))
                
                logger.info(f"Player {player_puuid} left lobby {lobby_id}")
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to leave lobby')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error leaving lobby: {str(e)}")
    
    async def update_lobby_preferences(self, data):
        """
        Handle updating lobby matchmaking preferences.
        """
        payload = data.get("payload")
        lobby_id = payload.get('lobby_id')
        requester_puuid = payload.get('requester_puuid')
        map_preferences = payload.get('map_preferences')
        server_preferences = payload.get('server_preferences')
        
        if not lobby_id or not requester_puuid:
            await self.send(text_data=json.dumps({
                "error": "lobby_id and requester_puuid are required"
            }))
            return
        
        try:
            result = await LobbyManager.update_lobby_preferences(
                lobby_id, 
                map_preferences, 
                server_preferences, 
                requester_puuid
            )
            
            if result['status'] == 'success':
                lobby_data = result['lobby']
                
                # Broadcast preferences update to lobby members
                await self.channel_layer.group_send(
                    f"lobby_{lobby_id}",
                    {
                        'type': 'lobby_preferences_updated',
                        'lobby': lobby_data
                    }
                )
                
                await self.send(text_data=json.dumps({
                    "event": "preferences_updated",
                    "payload": lobby_data
                }))
                
                logger.info(f"Lobby {lobby_id} preferences updated")
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to update preferences')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error updating lobby preferences: {str(e)}")

    async def add_lobby_to_queue(self, data):
        """
        Adds a lobby to the matchmaking queue using QueueManager.
        """
        payload = data.get("payload", {})
        lobby_id = payload.get("lobby_id")
        requester_puuid = payload.get("requester_puuid")
        
        if not lobby_id or not requester_puuid:
            await self.send(text_data=json.dumps({
                "error": "lobby_id and requester_puuid are required"
            }))
            return
        
        try:
            # Pre-flight validation check
            validation_result = await MatchStateValidator.can_lobby_queue(lobby_id)
            if not validation_result['can_queue']:
                await self.send(text_data=json.dumps({
                    "event": "queue_blocked",
                    "payload": {
                        "message": "Cannot queue: some players are in active matches",
                        "blocked_players": validation_result['blocked_players'],
                        "reasons": validation_result['reasons'],
                        "active_matches": validation_result['active_matches']
                    }
                }))
                return
            
            result = await QueueManager.join_queue(lobby_id, requester_puuid)
            
            if result['status'] == 'success':
                # Broadcast to lobby members
                await self.channel_layer.group_send(
                    f"lobby_{lobby_id}",
                    {
                        'type': 'lobby_queued',
                        'message': 'Lobby has been added to the matchmaking queue',
                        'queue_position': result.get('queue_position'),
                        'estimated_wait': result.get('estimated_wait')
                    }
                )
                
                await self.send(text_data=json.dumps({
                    "event": "joined_queue",
                    "payload": result
                }))
                
                logger.info(f"Lobby {lobby_id} joined matchmaking queue")
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to join queue')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error joining queue: {str(e)}")
        

    async def remove_lobby_from_queue(self, data):
        """
        Removes a lobby from the matchmaking queue using QueueManager.
        """
        payload = data.get("payload", {})
        lobby_id = payload.get("lobby_id")
        requester_puuid = payload.get("requester_puuid")
        
        if not lobby_id or not requester_puuid:
            await self.send(text_data=json.dumps({
                "error": "lobby_id and requester_puuid are required"
            }))
            return
        
        try:
            result = await QueueManager.leave_queue(lobby_id, requester_puuid)
            
            if result['status'] == 'success':
                # Broadcast to lobby members
                await self.channel_layer.group_send(
                    f"lobby_{lobby_id}",
                    {
                        'type': 'lobby_removed_from_queue',
                        'message': 'Lobby has been removed from the matchmaking queue'
                    }
                )
                
                await self.send(text_data=json.dumps({
                    "event": "left_queue",
                    "payload": result
                }))
                
                logger.info(f"Lobby {lobby_id} left matchmaking queue")
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to leave queue')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error leaving queue: {str(e)}")

    async def accept_match(self, data):
        """
        Handles match acceptance for a player using MatchConfirmationManager.
        """
        payload = data.get("payload", {})
        match_confirmation_id = payload.get("match_id")  # Client sends match_id
        player_puuid = self.puuid  # Use the player's PUUID from WebSocket connection
        
        if not match_confirmation_id:
            await self.send(text_data=json.dumps({
                "error": "match_id is required"
            }))
            return
        
        logger.info(f"Player {player_puuid[:12]}... accepted match {match_confirmation_id[:8]}...")
        
        try:
            result = await MatchConfirmationManager.accept_match(match_confirmation_id, player_puuid)
            
            if result['status'] == 'success':
                if result.get('match_confirmed'):
                    # All players accepted - match is ready
                    logger.info(f"MATCH READY! All players accepted match {result.get('match_id', '')[:8]}...")
                    # Send to ALL lobbies involved in the match
                    match_lobbies = result.get('match_lobbies', [])
                    logger.info(f"   Notifying {len(match_lobbies)} lobbies that match is ready")
                    for lobby_id in match_lobbies:
                        await self.channel_layer.group_send(
                            f"lobby_{lobby_id}",
                            {
                                'type': 'match_ready',
                                'message': 'Match is ready!',
                                'match_id': str(result.get('match_id')) if result.get('match_id') else None
                            }
                        )
                    logger.info(f"   All {len(match_lobbies)} lobbies notified - match starting!")
                else:
                    # Send acceptance update to ALL lobbies in the match, not just the accepting lobby
                    match_lobbies = result.get('match_lobbies', [])
                    accepted_count = result.get('accepted_count')
                    total_players = result.get('total_players')
                    timeout_seconds = result.get('timeout_seconds')
                    
                    if match_lobbies:
                        # Broadcast to all lobbies involved in this match
                        for lobby_id in match_lobbies:
                            await self.channel_layer.group_send(
                                f"lobby_{lobby_id}",
                                {
                                    'type': 'player_accepted',
                                    'accepted_count': accepted_count,
                                    'total_players': total_players,
                                    'timeout_seconds': timeout_seconds
                                }
                            )
                        logger.info(f"Player acceptance update sent to ALL {len(match_lobbies)} lobbies: {accepted_count}/{total_players} accepted")
                    else:
                        logger.warning(f"Could not determine match lobbies for player {player_puuid}")
                
                # Convert any UUID objects to strings for JSON serialization
                safe_result = {
                    'status': result.get('status'),
                    'match_confirmed': result.get('match_confirmed'),
                    'accepted_count': result.get('accepted_count'),
                    'total_players': result.get('total_players'),
                    'timeout_seconds': result.get('timeout_seconds'),
                    'match_id': str(result.get('match_id')) if result.get('match_id') else None,
                    'lobby_id': str(result.get('lobby_id')) if result.get('lobby_id') else None,
                }
                
                await self.send(text_data=json.dumps({
                    "event": "match_accepted",
                    "payload": safe_result
                }))
                
                logger.info(f"Player {player_puuid} accepted match {match_confirmation_id}")
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to accept match')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error accepting match: {str(e)}")
    
    async def decline_match(self, data):
        """
        Handles match decline for a player using MatchConfirmationManager.
        """
        payload = data.get("payload", {})
        match_confirmation_id = payload.get("match_confirmation_id")
        player_puuid = payload.get("player_puuid")
        
        if not match_confirmation_id or not player_puuid:
            await self.send(text_data=json.dumps({
                "error": "match_confirmation_id and player_puuid are required"
            }))
            return
        
        try:
            result = await MatchConfirmationManager.decline_match(match_confirmation_id, player_puuid)
            
            if result['status'] == 'success':
                # Broadcast match declined to all affected lobbies
                for lobby_id in result.get('affected_lobbies', []):
                    await self.channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'match_declined',
                            'message': 'Match was declined by a player',
                            'reason': 'Player declined'
                        }
                    )
                
                await self.send(text_data=json.dumps({
                    "event": "match_declined",
                    "payload": result
                }))
                
                logger.info(f"Player {player_puuid} declined match {match_confirmation_id}")
            else:
                await self.send(text_data=json.dumps({
                    "error": result.get('message', 'Failed to decline match')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error declining match: {str(e)}")
    
    async def get_queue_status(self, data):
        """
        Get current queue status and lobby position.
        """
        payload = data.get("payload", {})
        lobby_id = payload.get("lobby_id")
        
        if not lobby_id:
            await self.send(text_data=json.dumps({
                "error": "lobby_id is required"
            }))
            return
        
        try:
            result = await QueueManager.get_queue_status(lobby_id)
            
            await self.send(text_data=json.dumps({
                "event": "queue_status",
                "payload": result
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error getting queue status: {str(e)}")

    async def check_queue_eligibility(self, data):
        """
        Check if a player or lobby can queue (not in active matches).
        """
        payload = data.get("payload", {})
        lobby_id = payload.get("lobby_id")
        player_puuid = payload.get("player_puuid")
        
        try:
            if lobby_id:
                # Check entire lobby eligibility
                result = await MatchStateValidator.can_lobby_queue(lobby_id)
                
                await self.send(text_data=json.dumps({
                    "event": "queue_eligibility",
                    "payload": {
                        "type": "lobby",
                        "lobby_id": lobby_id,
                        "can_queue": result['can_queue'],
                        "blocked_players": result['blocked_players'],
                        "reasons": result['reasons'],
                        "active_matches": result['active_matches']
                    }
                }))
                
            elif player_puuid:
                # Check individual player eligibility
                result = await MatchStateValidator.can_player_queue(player_puuid)
                
                await self.send(text_data=json.dumps({
                    "event": "queue_eligibility", 
                    "payload": {
                        "type": "player",
                        "player_puuid": player_puuid,
                        "can_queue": result['can_queue'],
                        "reason": result['reason'],
                        "match_id": result['match_id'],
                        "match_state": result['match_state']
                    }
                }))
                
            else:
                await self.send(text_data=json.dumps({
                    "error": "Either lobby_id or player_puuid is required"
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": f"Failed to check queue eligibility: {str(e)}"
            }))
            logger.error(f"Error checking queue eligibility: {str(e)}")

    # -------------------- Outgoing WebSocket Messages --------------------
    
    async def lobby_updated(self, event):
        """
        Broadcast lobby updates to clients.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_updated',
            'payload': event.get('lobby', {})
        }))
    
    async def player_joined_lobby(self, event):
        """
        Notify clients when a player joins the lobby.
        """
        await self.send(text_data=json.dumps({
            'event': 'player_joined_lobby',
            'payload': {
                'lobby': event.get('lobby', {}),
                'player_puuid': event.get('player_puuid')
            }
        }))
    
    async def player_left_lobby(self, event):
        """
        Notify clients when a player leaves the lobby.
        """
        await self.send(text_data=json.dumps({
            'event': 'player_left_lobby',
            'payload': {
                'lobby': event.get('lobby', {}),
                'player_puuid': event.get('player_puuid'),
                'reason': event.get('reason', 'left')
            }
        }))
    
    async def kicked_from_lobby(self, event):
        """
        Notify a player they were kicked from a lobby.
        """
        await self.send(text_data=json.dumps({
            'event': 'kicked_from_lobby',
            'payload': {
                'lobby_id': event.get('lobby_id'),
                'message': event.get('message', 'You were kicked from the lobby')
            }
        }))
    
    async def lobby_disbanded(self, event):
        """
        Notify clients when lobby is disbanded.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_disbanded',
            'payload': {
                'reason': event.get('reason', 'unknown')
            }
        }))
    
    async def lobby_preferences_updated(self, event):
        """
        Notify clients when lobby preferences are updated.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_preferences_updated',
            'payload': event.get('lobby', {})
        }))

    async def match_ready(self, event):
        """
        Sends a notification to the client that a match is ready.
        """
        await self.send(text_data=json.dumps({
            'event': 'match_ready',
            'payload': {
                'match_id': event.get('match_id'),
                'message': event.get('message', 'Match is ready!'),
            }
        }))

    async def player_accepted(self, event):
        """
        Sends a notification to the client about the number of players who have accepted the match.
        """
        await self.send(text_data=json.dumps({
            'event': 'player_accepted',
            'payload': {
                'accepted_count': event.get("accepted_count", 0),
                'total_players': event.get("total_players", 10),
                'timeout_seconds': event.get("timeout_seconds", 30)
            }
        }))

    async def lobby_queued(self, event):
        """
        Sends a notification to the client that a lobby has been queued.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_queued',
            'message': event.get('message', 'Lobby has been queued'),
            'queue_position': event.get('queue_position'),
            'estimated_wait': event.get('estimated_wait')
        }))
    
    async def lobby_removed_from_queue(self, event):
        """
        Sends a notification that lobby was removed from queue.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_removed_from_queue',
            'message': event.get('message', 'Lobby was removed from queue')
        }))
    
    async def match_found(self, event):
        """
        Sends a notification that a match has been found.
        """
        match_id = event.get('match_confirmation_id')
        logger.info(f"MATCH PROPOSED to player {self.puuid[:12]}... - Match ID: {match_id[:8] if match_id else 'Unknown'}...")
        logger.info(f"   Timeout: {event.get('timeout_seconds', 30)}s")
        
        await self.send(text_data=json.dumps({
            'event': 'match_found',
            'payload': {
                'match_id': event.get('match_confirmation_id'),  # Client expects match_id
                'match_confirmation_id': event.get('match_confirmation_id'),
                'opponent_lobby': event.get('opponent_lobby'),
                'timeout_seconds': event.get('timeout_seconds'),
                'message': event.get('message', 'Match found! Please accept to continue.')
            }
        }))
        
        logger.info(f"   Match proposal sent to {self.puuid[:12]}... via WebSocket")
    
    async def match_declined(self, event):
        """
        Sends a notification that a match was declined.
        """
        await self.send(text_data=json.dumps({
            'event': 'match_declined',
            'message': event.get('message', 'Match was declined'),
            'reason': event.get('reason', 'Unknown')
        }))
    
    async def match_timeout(self, event):
        """
        Sends a notification that a match confirmation timed out.
        """
        await self.send(text_data=json.dumps({
            'event': 'match_timeout',
            'message': event.get('message', 'Match confirmation timed out'),
            'reason': event.get('reason', 'timeout')
        }))
    
    async def player_accepted(self, event):
        """
        Sends a notification about player acceptance progress.
        """
        await self.send(text_data=json.dumps({
            'event': 'player_accepted',
            'payload': {
                'accepted_count': event.get('accepted_count', 0),
                'total_players': event.get('total_players', 10),
                'timeout_seconds': event.get('timeout_seconds', 30)
            }
        }))
    
    async def match_ready(self, event):
        """
        Sends a notification that the match is ready (all players accepted).
        """
        await self.send(text_data=json.dumps({
            'event': 'match_ready',
            'payload': {
                'match_id': event.get('match_id'),
                'message': event.get('message', 'Match is ready!')
            }
        }))
    
    # -------------------- Match Page WebSocket Events --------------------
    
    async def match_confirmed(self, event):
        """
        All players accepted - redirect to match page.
        """
        match_id = event.get('match_id')
        await self.send(text_data=json.dumps({
            'event': 'match_confirmed',
            'payload': {
                'match_id': match_id,
                'team': event.get('team'),
                'redirect_url': f"/match/{match_id}" if match_id else None
            }
        }))
    
    async def match_data(self, event):
        """
        # FIX: Match data broadcast - ensures all players get captain/team info.
        """
        # Add player to match group for veto updates
        match_id = event.get('match_id')
        if match_id:
            await self.channel_layer.group_add(
                f"match_{match_id}",
                self.channel_name
            )
            logger.info(f"Added player {self.puuid} to match group match_{match_id}")
        
        await self.send(text_data=json.dumps({
            'event': 'match_data',
            'payload': event.get('payload', {})
        }))
    
    async def veto_started(self, event):
        """
        Veto phase has begun.
        """
        await self.send(text_data=json.dumps({
            'event': 'veto_started',
            'payload': {
                'match_id': event.get('match_id'),
                'current_turn': event.get('current_turn'),
                'available_maps': event.get('available_maps', []),
                'deadline': event.get('deadline')
            }
        }))
    
    async def server_veto_started(self, event):
        """
        Server veto phase has begun.
        """
        await self.send(text_data=json.dumps({
            'event': 'server_veto_started',
            'payload': {
                'match_id': event.get('match_id'),
                'current_turn': event.get('current_turn'),
                'available_servers': event.get('available_servers', []),
                'deadline': event.get('deadline')
            }
        }))
    
    async def server_vetoed(self, event):
        """
        A server was vetoed.
        """
        await self.send(text_data=json.dumps({
            'event': 'server_veto_update',
            'payload': {
                'match_id': event.get('match_id'),
                'server_name': event.get('server_name'),
                'vetoed_by': event.get('vetoed_by'),
                'next_turn': event.get('next_turn'),
                'remaining_servers': event.get('remaining_servers', []),
                'deadline': event.get('deadline')
            }
        }))
    
    async def server_veto_complete(self, event):
        """
        Server veto phase completed - transition to map veto.
        """
        await self.send(text_data=json.dumps({
            'event': 'server_veto_complete',
            'payload': {
                'match_id': event.get('match_id'),
                'final_server': event.get('final_server'),
                'current_turn': event.get('current_turn'),
                'available_maps': event.get('available_maps', []),
                'veto_deadline': event.get('veto_deadline')
            }
        }))
        
        # FIX: If map veto started, also send map_veto_started event
        if event.get('map_veto_started', False):
            await self.send(text_data=json.dumps({
                'event': 'map_veto_started',
                'payload': {
                    'match_id': event.get('match_id'),
                    'current_turn': event.get('current_turn'),
                    'available_maps': event.get('available_maps', []),
                    'deadline': event.get('veto_deadline')
                }
            }))
    
    async def server_veto_timeout(self, event):
        """
        Server veto timeout - a team took too long, auto-veto occurred.
        """
        await self.send(text_data=json.dumps({
            'event': 'server_veto_timeout',
            'payload': {
                'match_id': event.get('match_id'),
                'timed_out_team': event.get('timed_out_team'),
                'auto_vetoed_server': event.get('auto_vetoed_server'),
                'next_turn': event.get('next_turn'),
                'remaining_servers': event.get('remaining_servers', []),
                'deadline': event.get('deadline'),
                'server_veto_complete': event.get('server_veto_complete', False),
                'final_server': event.get('final_server'),
                'map_veto_started': event.get('map_veto_started', False),
                'current_turn': event.get('current_turn'),
                'available_maps': event.get('available_maps', []),
                'veto_deadline': event.get('veto_deadline')
            }
        }))
        
        # FIX: If map veto started, also send map_veto_started event
        if event.get('map_veto_started', False):
            await self.send(text_data=json.dumps({
                'event': 'map_veto_started',
                'payload': {
                    'match_id': event.get('match_id'),
                    'current_turn': event.get('current_turn'),
                    'available_maps': event.get('available_maps'),
                    'deadline': event.get('veto_deadline')
                }
            }))

    async def map_vetoed(self, event):
        """
        A map was vetoed.
        """
        await self.send(text_data=json.dumps({
            'event': 'map_vetoed',
            'payload': {
                'match_id': event.get('match_id'),
                'map': event.get('map_name'),
                'vetoed_by': event.get('vetoed_by'),
                'next_turn': event.get('next_turn'),
                'remaining_maps': event.get('remaining_maps', []),
                'deadline': event.get('deadline')
            }
        }))
    
    async def map_veto_started(self, event):
        """
        # FIX: Map veto phase has begun.
        """
        await self.send(text_data=json.dumps({
            'event': 'map_veto_started',
            'payload': {
                'match_id': event.get('match_id'),
                'current_turn': event.get('current_turn'),
                'available_maps': event.get('available_maps', []),
                'deadline': event.get('deadline')
            }
        }))
    
    async def map_veto_timeout(self, event):
        """
        Veto timeout occurred - auto-veto.
        """
        await self.send(text_data=json.dumps({
            'event': 'map_veto_timeout',
            'payload': {
                'match_id': event.get('match_id'),
                'auto_vetoed_map': event.get('auto_vetoed_map'),
                'veto_complete': event.get('veto_complete', False),
                'final_map': event.get('final_map'),
                'side_selector': event.get('side_selector'),
                'side_selection_deadline': event.get('side_selection_deadline'),
                'next_turn': event.get('next_turn'),
                'remaining_maps': event.get('remaining_maps', []),
                'deadline': event.get('deadline')
            }
        }))
    
    async def side_selection_timeout(self, event):
        """
        Side selection timeout occurred - auto-select side.
        """
        await self.send(text_data=json.dumps({
            'event': 'side_selection_timeout',
            'payload': {
                'match_id': event.get('match_id'),
                'auto_selected_side': event.get('auto_selected_side'),
                'side_selection_complete': event.get('side_selection_complete', False),
                'match_ready': event.get('match_ready', False)
            }
        }))
    
    async def veto_complete(self, event):
        """
        Veto complete - final map selected.
        """
        await self.send(text_data=json.dumps({
            'event': 'veto_complete',
            'payload': {
                'match_id': event.get('match_id'),
                'final_map': event.get('final_map'),
                'side_selector': event.get('side_selector'),
                'side_selection_deadline': event.get('side_selection_deadline')
            }
        }))

    async def side_selection_started(self, event):
        """
        Side selection phase has begun.
        """
        await self.send(text_data=json.dumps({
            'event': 'side_selection_started',
            'payload': {
                'match_id': event.get('match_id'),
                'side_selector': event.get('side_selector'),
                'deadline': event.get('deadline')
            }
        }))
    
    # -------------------- Match Page Event Handlers (Incoming) --------------------
    
    async def handle_get_match_data(self, data):
        """
        Client requests match data.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        
        if not match_id:
            await self.send(text_data=json.dumps({
                'error': 'match_id is required'
            }))
            return
        
        try:
            # Get match data
            match_data = await MatchManager.get_match_data(match_id)
            
            if match_data:
                # Add player to match group
                await self.channel_layer.group_add(
                    f"match_{match_id}",
                    self.channel_name
                )
                
                await self.send(text_data=json.dumps({
                    'event': 'match_data',
                    'payload': match_data
                }))
            else:
                await self.send(text_data=json.dumps({
                    'error': 'Match not found'
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to get match data: {str(e)}'
            }))
            logger.error(f"Error getting match data: {str(e)}")
    
    async def handle_veto_server(self, data):
        """
        Captain vetoes a server.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        server_name = payload.get('server_name')
        
        if not match_id or not server_name:
            await self.send(text_data=json.dumps({
                'error': 'match_id and server_name are required'
            }))
            return
        
        try:
            # Get match (use sync_to_async for compatibility)
            from match_system.models import Match
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            
            # Determine which team this player is on
            team = match.get_player_team(self.puuid)
            if not team:
                await self.send(text_data=json.dumps({
                    'error': 'Player not found in match'
                }))
                return
            
            # Process server veto
            result = await MatchManager.process_server_veto(match, server_name, team, self.puuid)
            
            if result['status'] == 'success':
                # Broadcast server veto update to all players in match
                await self.channel_layer.group_send(
                    f"match_{match.id}",
                    {
                        'type': 'server_vetoed',
                        'match_id': str(match.id),
                        'server_name': server_name,
                        'vetoed_by': team,
                        'next_turn': result.get('next_turn'),
                        'remaining_servers': result.get('remaining_servers', []),
                        'deadline': result.get('deadline')
                    }
                )
                
                # If server veto is complete, transition to map veto
                if result.get('server_veto_complete'):
                    await self.channel_layer.group_send(
                        f"match_{match.id}",
                        {
                            'type': 'server_veto_complete',
                            'match_id': str(match.id),
                            'final_server': result.get('final_server'),
                            'current_turn': result.get('current_turn'),
                            'available_maps': result.get('available_maps', []),
                            'veto_deadline': result.get('veto_deadline')
                        }
                    )
                
                await self.send(text_data=json.dumps({
                    'event': 'server_veto_acknowledged',
                    'payload': result
                }))
                
                logger.info(f"Server {server_name} vetoed by {team} captain {self.puuid[:12]}... in match {match.id}")
            else:
                await self.send(text_data=json.dumps({
                    'error': result.get('message')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to veto server: {str(e)}'
            }))
            logger.error(f"Error vetoing server: {str(e)}")

    async def handle_veto_map(self, data):
        """
        Captain vetoes a map.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        map_name = payload.get('map') or payload.get('map_name')  # Support both field names
        
        if not match_id or not map_name:
            await self.send(text_data=json.dumps({
                'error': 'match_id and map are required'
            }))
            return
        
        try:
            # Get match (use sync_to_async for compatibility)
            from match_system.models import Match
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            
            # Determine which team this player is on
            team = match.get_player_team(self.puuid)
            
            if not team:
                await self.send(text_data=json.dumps({
                    'error': 'You are not in this match'
                }))
                return
            
            # Process veto
            result = await MatchManager.process_map_veto(match, map_name, team, self.puuid)
            
            if result['status'] == 'success':
                # Broadcast veto to all players in match
                event_data = {
                    'match_id': str(match.id),
                    'map_name': map_name,
                    'vetoed_by': team,
                }
                
                if result.get('veto_complete'):
                    # Veto phase complete
                    await self.channel_layer.group_send(
                        f"match_{match.id}",
                        {
                            'type': 'veto_complete',
                            'match_id': str(match.id),
                            'final_map': result['final_map'],
                            'side_selector': result.get('side_selector'),
                            'side_selection_deadline': result.get('side_selection_deadline')
                        }
                    )
                    
                    await self.channel_layer.group_send(
                        f"match_{match.id}",
                        {
                            'type': 'side_selection_started',
                            'match_id': str(match.id),
                            'side_selector': result.get('side_selector'),
                            'deadline': result.get('side_selection_deadline')
                        }
                    )
                else:
                    # Veto continues
                    event_data['next_turn'] = result['next_turn']
                    event_data['remaining_maps'] = result['remaining_maps']
                    event_data['deadline'] = result['deadline']
                    
                    await self.channel_layer.group_send(
                        f"match_{match.id}",
                        {
                            'type': 'map_vetoed',
                            **event_data
                        }
                    )
                
                await self.send(text_data=json.dumps({
                    'event': 'veto_acknowledged',
                    'payload': result
                }))
                
                logger.info(f"Map {map_name} vetoed by {team} in match {match.id}")
            else:
                await self.send(text_data=json.dumps({
                    'error': result.get('message')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to veto map: {str(e)}'
            }))
            logger.error(f"Error vetoing map: {str(e)}")

    async def handle_select_side(self, data):
        """
        Captain selects a side (attack/defend).
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        side = payload.get('side')
        
        if not match_id or not side:
            await self.send(text_data=json.dumps({
                'error': 'match_id and side are required'
            }))
            return
        
        try:
            # Get match (use sync_to_async for compatibility)
            from match_system.models import Match
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            
            # Determine which team this player is on
            team = match.get_player_team(self.puuid)
            
            if not team:
                await self.send(text_data=json.dumps({
                    'error': 'You are not in this match'
                }))
                return
            
            result = await MatchManager.select_side(match_id, self.puuid, side)

            if result['status'] == 'success':
                await self.send(
                    text_data=json.dumps(
                        {
                            'event': 'side_acknowledged',
                            'payload': result,
                        }
                    )
                )
                logger.info(f"Side {side} selected by {team} in match {match.id}")
            else:
                await self.send(
                    text_data=json.dumps({'error': result.get('message')})
                )

        except Exception as e:
            logger.error(f"Error processing side selection for {match_id}: {str(e)}")
            await self.send(
                text_data=json.dumps(
                    {'error': f"Failed to process side selection: {str(e)}"}
                )
            )
        
    # -------------------- Lobby Chat WebSocket Messages --------------------        
        
    async def lobby_message(self, event):
        """
        Send lobby chat messages to the frontend.
        """
        logger.debug(f"Broadcasting lobby message from {event.get('username', 'Unknown')}")
        await self.send(text_data=json.dumps({
            'event': 'lobby_message',
            'username': event.get('username', 'Unknown'),
            'message': event.get('message', ''),
            'timestamp': event.get('timestamp'),
        }))
    
    # Handler for incoming lobby chat message events
    async def handle_lobby_message(self, data):
        payload = data.get('payload', {})
        logger.debug(f"Received lobby message: {payload.get('message', '')[:50]}...")
        message = payload.get('message')
        lobby_id = payload.get('lobby_id')
        username = payload.get('userAlias', 'Anonymous')
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        if not message or not lobby_id:
            await self.send(text_data=json.dumps({"error": "Lobby message or lobby ID missing"}))
            return
        self.lobby_group_name = self.get_lobby_group_name(lobby_id)
        await self.channel_layer.group_send(
            self.lobby_group_name,
            {
                'type': 'lobby_message',
                'username': username,
                'message': message,
                'timestamp': timestamp,
            }
        )

    # -------------------- Direct Chat WebSocket Messages --------------------   
    
    async def direct_message(self, event):
        """
        Send private messages to the recipient.
        """
        await self.send(text_data=json.dumps({
            'event': 'direct_message',
            'username': event.get('username', 'Unknown'),
            'message': event.get('message', ''),
            'timestamp': event.get('timestamp'),
        }))
        
    async def handle_direct_message(self, data):
        """
        Handle private messages sent between players.
        """
        payload = data.get('payload', {})
        message = payload.get('message')
        recipient_puuid = payload.get('recipient_puuid')
        username = payload.get('username', 'Anonymous')
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        if not message or not recipient_puuid:
            await self.send(text_data=json.dumps({"error": "Direct message or recipient missing"}))
            return

        # Send message to the recipient's player group
        recipient_group_name = f"player_{recipient_puuid}"
        await self.channel_layer.group_send(
            recipient_group_name,
            {
                'type': 'direct_message',
                'username': username,
                'message': message,
                'timestamp': timestamp,
            }
        )

    # -------------------- Match Execution Event Handlers --------------------
    
    async def handle_custom_game_created(self, data):
        """
        Constructor client reports custom game creation.
        Notifies other players to join.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        pregame_id = payload.get('pregame_id')
        constructor_puuid = payload.get('constructor_puuid')
        
        if not all([match_id, pregame_id, constructor_puuid]):
            await self.send(text_data=json.dumps({
                'error': 'match_id, pregame_id, and constructor_puuid are required'
            }))
            return
        
        try:
            result = await ExecutionPhaseManager.handle_custom_game_created(
                match_id, pregame_id, constructor_puuid
            )
            
            if result['status'] == 'success':
                await self.send(text_data=json.dumps({
                    'event': 'custom_game_created_ack',
                    'payload': result
                }))
                logger.info(f"Custom game created: {pregame_id} for match {match_id}")
            else:
                await self.send(text_data=json.dumps({
                    'event': 'error',
                    'payload': {'message': result.get('message')}
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to handle custom game creation: {str(e)}'
            }))
            logger.error(f"Error handling custom_game_created: {str(e)}")
    
    
    async def handle_player_joined_game(self, data):
        """
        Player client reports successful join to custom game.
        Track which players have joined and start match when all players ready.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        player_puuid = payload.get('player_puuid')
        team = payload.get('team')
        
        if not all([match_id, player_puuid]):
            return
        
        logger.info(f"Player {player_puuid} joined match {match_id} (Team: {team})")
        
        try:
            result = await ExecutionPhaseManager.handle_player_joined(match_id, player_puuid)

            if result.get('status') == 'success':
                await self.send(text_data=json.dumps({
                    'event': 'player_joined_ack',
                    'payload': {
                        'match_id': match_id,
                        'player_puuid': player_puuid,
                        'joined_count': result.get('joined_count'),
                        'total_expected': result.get('total_players'),
                    }
                }))
            else:
                await self.send(text_data=json.dumps({
                    'event': 'player_joined_ack',
                    'payload': {
                        'match_id': match_id,
                        'player_puuid': player_puuid,
                        'error': result.get('message', 'join failed'),
                    }
                }))
                logger.error(f"Failed to record player join for match {match_id}: {result.get('message')}")

        except Exception as e:
            logger.error(f"Error handling player join: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Still acknowledge to prevent client hanging
            await self.send(text_data=json.dumps({
                'event': 'player_joined_ack',
                'payload': {'match_id': match_id, 'player_puuid': player_puuid, 'error': str(e)}
            }))
    
    
    async def handle_player_join_failed(self, data):
        """
        Handle when a player fails to join the custom game.
        This could lead to match cancellation if critical players fail.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        player_puuid = payload.get('player_puuid')
        team = payload.get('team')
        error = payload.get('error', 'Unknown error')
        
        logger.warning(f"Player {player_puuid} failed to join match {match_id}: {error}")
        
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            def check_match():
                try:
                    match = Match.objects.get(id=match_id)
                    return match
                except Match.DoesNotExist:
                    return None
            
            match = await sync_to_async(check_match)()
            
            if not match:
                logger.error(f"Match {match_id} not found for join failure")
                return
            
            # For now, we'll be lenient and allow matches to continue with fewer players
            # In a production system, you might want to cancel if too many critical players fail
            
            logger.info(f"Match {match_id} continuing despite join failure from {player_puuid}")
            
            # Acknowledge the failure
            await self.send(text_data=json.dumps({
                'event': 'player_join_failed_ack',
                'payload': {
                    'match_id': match_id,
                    'player_puuid': player_puuid,
                    'error': error
                }
            }))
            
        except Exception as e:
            logger.error(f"Error handling player join failure: {str(e)}")
            import traceback
            traceback.print_exc()
    
    
    async def all_players_joined(self, event):
        """
        WebSocket event handler for when all players have joined.
        This is called when the channel layer sends the event to the constructor.
        """
        match_id = event.get('match_id')
        is_constructor = event.get('is_constructor', False)
        
        logger.info(f"All players joined event received for match {match_id}")
        
        # Forward to constructor client
        await self.send(text_data=json.dumps({
            'event': 'all_players_joined',
            'payload': {
                'match_id': match_id,
                'is_constructor': is_constructor
            }
        }))
    
    
    async def match_cancelled(self, event):
        """
        WebSocket event handler for when a match is cancelled.
        """
        match_id = event.get('match_id')
        reason = event.get('reason', 'unknown')
        
        logger.info(f"Match {match_id} cancelled: {reason}")
        
        # Forward to client
        await self.send(text_data=json.dumps({
            'event': 'match_cancelled',
            'payload': {
                'match_id': match_id,
                'reason': reason
            }
        }))
    
    
    async def handle_match_started(self, data):
        """
        Match has started - all players loaded in.
        Transition match to in_progress state.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        coregame_id = payload.get('coregame_id')
        
        if not all([match_id, coregame_id]):
            await self.send(text_data=json.dumps({
                'error': 'match_id and coregame_id are required'
            }))
            return
        
        try:
            result = await ExecutionPhaseManager.handle_match_started(
                match_id, coregame_id
            )
            
            if result['status'] == 'success':
                logger.info(f"Match {match_id} started: {coregame_id}")
            else:
                logger.error(f"Failed to start match {match_id}: {result.get('message')}")
                
        except Exception as e:
            logger.error(f"Error handling match_started: {str(e)}")
    
    
    async def handle_match_score_update(self, data):
        """
        Receive score updates from constructor client.
        Broadcast to spectators.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        team_a_score = payload.get('team_a_score')
        team_b_score = payload.get('team_b_score')
        current_round = payload.get('current_round')
        
        if not all([match_id is not None, team_a_score is not None, 
                    team_b_score is not None, current_round is not None]):
            return
        
        try:
            from match_system.monitor import MatchMonitor
            
            await MatchMonitor.update_match_score(
                match_id, team_a_score, team_b_score, current_round
            )
            
        except Exception as e:
            logger.error(f"Error handling match_score_update: {str(e)}")
    
    
    async def handle_match_completed(self, data):
        """
        Match has completed - process final results.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        final_data = payload.get('final_data', {})
        
        if not match_id:
            return
        
        try:
            await ExecutionPhaseManager.handle_match_completion(
                match_id, final_data
            )
            
            logger.info(f"Match {match_id} completed")
            
        except Exception as e:
            logger.error(f"Error handling match_completed: {str(e)}")
    
    
    async def handle_request_rejoin(self, data):
        """
        Player requests to rejoin match after disconnect.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        player_puuid = payload.get('player_puuid')
        
        if not all([match_id, player_puuid]):
            await self.send(text_data=json.dumps({
                'error': 'match_id and player_puuid are required'
            }))
            return
        
        try:
            token = await ExecutionPhaseManager.generate_rejoin_token(
                match_id, player_puuid
            )
            
            await self.send(text_data=json.dumps({
                'event': 'rejoin_token',
                'payload': {'token': token, 'match_id': match_id}
            }))
            
            logger.info(f"Generated rejoin token for {player_puuid} in match {match_id}")
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to generate rejoin token: {str(e)}'
            }))
            logger.error(f"Error generating rejoin token: {str(e)}")
    
    
    async def handle_get_match_statistics(self, data):
        """
        Get current match statistics for spectators.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        
        if not match_id:
            await self.send(text_data=json.dumps({
                'error': 'match_id is required'
            }))
            return
        
        try:
            from match_system.monitor import MatchMonitor
            
            result = await MatchMonitor.get_match_statistics(match_id)
            
            if result['status'] == 'success':
                await self.send(text_data=json.dumps({
                    'event': 'match_statistics',
                    'payload': result['data']
                }))
            else:
                await self.send(text_data=json.dumps({
                    'error': result.get('message', 'Failed to get match statistics')
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to get match statistics: {str(e)}'
            }))
            logger.error(f"Error getting match statistics: {str(e)}")
    
    
    # -------------------- Outgoing WebSocket Handlers (called by channel layer) --------------------
    
    async def match_construction_started(self, event):
        """Send match_construction_started event to client"""
        await self.send(text_data=json.dumps({
            'event': 'match_construction_started',
            'payload': {
                'match_id': event.get('match_id'),
                'constructor_puuid': event.get('constructor_puuid'),
                'is_constructor': event.get('is_constructor', False),
                'map': event.get('map'),
                'server': event.get('server'),
                'team': event.get('team')
            }
        }))
    
    
    async def join_custom_game(self, event):
        """Send join_custom_game event to client"""
        await self.send(text_data=json.dumps({
            'event': 'join_custom_game',
            'payload': {
                'match_id': event.get('match_id'),
                'pregame_id': event.get('pregame_id'),
                'team': event.get('team')
            }
        }))
    
    
    async def match_in_progress(self, event):
        """Send match_in_progress event to client"""
        await self.send(text_data=json.dumps({
            'event': 'match_in_progress',
            'payload': {
                'match_id': event.get('match_id'),
                'coregame_id': event.get('coregame_id'),
                'map': event.get('map'),
                'server': event.get('server')
            }
        }))
    
    
    async def match_score_update(self, event):
        """Send score update to spectators"""
        await self.send(text_data=json.dumps({
            'event': 'match_score_update',
            'payload': {
                'match_id': event.get('match_id'),
                'team_a_score': event.get('team_a_score'),
                'team_b_score': event.get('team_b_score'),
                'current_round': event.get('current_round')
            }
        }))
    
    
    async def match_completed(self, event):
        """Send match completion event"""
        await self.send(text_data=json.dumps({
            'event': 'match_completed',
            'payload': {
                'match_id': event.get('match_id'),
                'team_a_score': event.get('team_a_score'),
                'team_b_score': event.get('team_b_score'),
                'winner': event.get('winner'),
                'final_data': event.get('final_data', {})
            }
        }))
    
    async def lobby_destroyed(self, event):
        """Send lobby destroyed event to client"""
        await self.send(text_data=json.dumps({
            'event': 'lobby_destroyed',
            'payload': {
                'message': event.get('message', 'Lobby was destroyed'),
                'reason': event.get('reason', 'unknown')
            }
        }))
    
    async def player_left_lobby(self, event):
        """Send player left lobby event to client"""
        await self.send(text_data=json.dumps({
            'event': 'player_left_lobby',
            'payload': {
                'player': event.get('player', {}),
                'message': event.get('message', 'Player left the lobby')
            }
        }))
    
    async def lobby_leader_changed(self, event):
        """Send lobby leader changed event to client"""
        await self.send(text_data=json.dumps({
            'event': 'lobby_leader_changed',
            'payload': {
                'new_leader': event.get('new_leader', {}),
                'old_leader': event.get('old_leader', {}),
                'message': event.get('message', 'Lobby leader changed')
            }
        }))
    
    async def map_vetoed(self, event):
        """
        Handle map vetoed event - broadcast to all players in match.
        """
        logger.info(f"Map vetoed event received: {event}")
        
        await self.send(text_data=json.dumps({
            'event': 'map_vetoed',
            'payload': {
                'match_id': event.get('match_id'),
                'map_name': event.get('map_name'),
                'vetoed_by': event.get('vetoed_by'),
                'next_turn': event.get('next_turn'),
                'remaining_maps': event.get('remaining_maps', []),
                'deadline': event.get('deadline')
            }
        }))
    
    async def veto_complete(self, event):
        """
        Handle veto complete event - broadcast to all players in match.
        """
        logger.info(f"Veto complete event received: {event}")
        
        await self.send(text_data=json.dumps({
            'event': 'veto_complete',
            'payload': {
                'match_id': event.get('match_id'),
                'final_map': event.get('final_map'),
                'side_selector': event.get('side_selector')
            }
        }))
    
    async def side_selected(self, event):
        """
        Handle side selected event - broadcast to all players in match.
        """
        logger.info(f"Side selected event received: {event}")
        
        await self.send(text_data=json.dumps({
            'event': 'side_selected',
            'payload': {
                'match_id': event.get('match_id'),
                'side': event.get('side'),
                'selected_by': event.get('selected_by'),
                'side_complete': event.get('side_complete', False)
            }
        }))
    
    
    ### Validate ###
    
    def get_lobby_group_name(self, lobby_id):
        if not lobby_id:
            raise ValueError("Lobby ID is required.")
        return f"lobby_{lobby_id}"