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
from .lobby_manager import LobbyManager
from scrimgg.serializers import LobbySerializer, PlayerSerializer

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
                print(f"WebSocket added to lobby group: {self.lobby_group_name}")
        except Exception as e:
            print(f"Error during WebSocket connect: {e}")
        await self.accept()
        print(f"WebSocket connected: PUUID = {self.puuid}")

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection. Removes the connection from the assigned groups.
        """
        await self.channel_layer.group_discard(self.player_group_name, self.channel_name)
        if hasattr(self, 'lobby_group_name') and self.lobby_group_name:
            await self.channel_layer.group_discard(self.lobby_group_name, self.channel_name)
        print(f"WebSocket disconnected: PUUID = {self.puuid}")

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
            
            # Match execution events
            elif action == 'custom_game_created':
                await self.handle_custom_game_created(text_data_json)
            elif action == 'player_joined_game':
                await self.handle_player_joined_game(text_data_json)
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
            print("Error: PUUID is required.")
            return
        try:
            player = await sync_to_async(Player.objects.get)(puuid=player_id)
            print(f"Fetched Player: PK={player.pk}, PUUID={player.puuid}")
            def serialize_player(player_instance):
                from scrimgg.serializers import PlayerSerializer
                return PlayerSerializer(player_instance).data
            serialized_player = await sync_to_async(serialize_player)(player)
            await self.send(text_data=json.dumps({
                "event": "player_model",
                "data": serialized_player
            }))
        except Player.DoesNotExist:
            await self.send(text_data=json.dumps({"error": "Player not found."}))
            print(f"Error: Player with PUUID={player_id} not found.")
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            print(f"Unexpected error while fetching player: {str(e)}")

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
                    "data": lobby_data
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
                    "data": lobby_data
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
                    "data": result
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
                    "data": result
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
                    "data": lobby_data
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
                    "data": result
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
                    "data": result
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
        match_confirmation_id = payload.get("match_confirmation_id")
        player_puuid = payload.get("player_puuid")
        
        if not match_confirmation_id or not player_puuid:
            await self.send(text_data=json.dumps({
                "error": "match_confirmation_id and player_puuid are required"
            }))
            return
        
        try:
            result = await MatchConfirmationManager.accept_match(match_confirmation_id, player_puuid)
            
            if result['status'] == 'success':
                if result.get('match_confirmed'):
                    # All players accepted - match is ready
                    await self.channel_layer.group_send(
                        f"lobby_{result.get('lobby_id')}",
                        {
                            'type': 'match_ready',
                            'message': 'Match is ready!',
                            'match_id': result.get('match_id')
                        }
                    )
                else:
                    # Some players still need to accept
                    await self.channel_layer.group_send(
                        f"lobby_{result.get('lobby_id')}",
                        {
                            'type': 'player_accepted',
                            'accepted_count': result.get('accepted_count'),
                            'total_players': result.get('total_players'),
                            'timeout_seconds': result.get('timeout_seconds')
                        }
                    )
                
                await self.send(text_data=json.dumps({
                    "event": "match_accepted",
                    "data": result
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
                    "data": result
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
                "data": result
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            logger.error(f"Error getting queue status: {str(e)}")

    # -------------------- Outgoing WebSocket Messages --------------------
    
    async def lobby_updated(self, event):
        """
        Broadcast lobby updates to clients.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_updated',
            'data': event['lobby']
        }))
    
    async def player_joined_lobby(self, event):
        """
        Notify clients when a player joins the lobby.
        """
        await self.send(text_data=json.dumps({
            'event': 'player_joined_lobby',
            'data': {
                'lobby': event['lobby'],
                'player_puuid': event['player_puuid']
            }
        }))
    
    async def player_left_lobby(self, event):
        """
        Notify clients when a player leaves the lobby.
        """
        await self.send(text_data=json.dumps({
            'event': 'player_left_lobby',
            'data': {
                'lobby': event['lobby'],
                'player_puuid': event['player_puuid'],
                'reason': event.get('reason', 'left')
            }
        }))
    
    async def kicked_from_lobby(self, event):
        """
        Notify a player they were kicked from a lobby.
        """
        await self.send(text_data=json.dumps({
            'event': 'kicked_from_lobby',
            'data': {
                'lobby_id': event['lobby_id'],
                'message': event['message']
            }
        }))
    
    async def lobby_disbanded(self, event):
        """
        Notify clients when lobby is disbanded.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_disbanded',
            'data': {
                'reason': event['reason']
            }
        }))
    
    async def lobby_preferences_updated(self, event):
        """
        Notify clients when lobby preferences are updated.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_preferences_updated',
            'data': event['lobby']
        }))

    async def match_ready(self, event):
        """
        Sends a notification to the client that a match is ready.
        """
        await self.send(text_data=json.dumps({
            'action': 'match_ready',
            'message': event['message'],
        }))

    async def player_accepted(self, event):
        """
        Sends a notification to the client about the number of players who have accepted the match.
        """
        await self.send(text_data=json.dumps({
            'action': 'player_accepted',
            'accepted_count': event["accepted_count"],
        }))

    async def lobby_queued(self, event):
        """
        Sends a notification to the client that a lobby has been queued.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_queued',
            'message': event['message'],
            'queue_position': event.get('queue_position'),
            'estimated_wait': event.get('estimated_wait')
        }))
    
    async def lobby_removed_from_queue(self, event):
        """
        Sends a notification that lobby was removed from queue.
        """
        await self.send(text_data=json.dumps({
            'event': 'lobby_removed_from_queue',
            'message': event['message']
        }))
    
    async def match_found(self, event):
        """
        Sends a notification that a match has been found.
        """
        await self.send(text_data=json.dumps({
            'event': 'match_found',
            'match_confirmation_id': event['match_confirmation_id'],
            'opponent_lobby': event.get('opponent_lobby'),
            'timeout_seconds': event.get('timeout_seconds'),
            'message': event.get('message', 'Match found! Please accept to continue.')
        }))
    
    async def match_declined(self, event):
        """
        Sends a notification that a match was declined.
        """
        await self.send(text_data=json.dumps({
            'event': 'match_declined',
            'message': event['message'],
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
        
    # -------------------- Lobby Chat WebSocket Messages --------------------        
        
    async def lobby_message(self, event):
        """
        Send lobby chat messages to the frontend.
        """
        print(f"Broadcasting message: {event}")
        await self.send(text_data=json.dumps({
            'event': 'lobby_message',
            'username': event['username'],
            'message': event['message'],
            'timestamp': event['timestamp'],
        }))
    
    # Handler for incoming lobby chat message events
    async def handle_lobby_message(self, data):
        payload = data.get('payload', {})
        print(payload)
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
            'username': event['username'],
            'message': event['message'],
            'timestamp': event['timestamp'],
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
            from .match_execution import MatchExecutionManager
            
            result = await MatchExecutionManager.handle_custom_game_created(
                match_id, pregame_id, constructor_puuid
            )
            
            if result['status'] == 'success':
                await self.send(text_data=json.dumps({
                    'event': 'custom_game_created_ack',
                    'data': result
                }))
                logger.info(f"Custom game created: {pregame_id} for match {match_id}")
            else:
                await self.send(text_data=json.dumps({
                    'event': 'error',
                    'data': {'message': result.get('message')}
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to handle custom game creation: {str(e)}'
            }))
            logger.error(f"Error handling custom_game_created: {str(e)}")
    
    
    async def handle_player_joined_game(self, data):
        """
        Player client reports successful join to custom game.
        Track which players have joined.
        """
        payload = data.get('payload', {})
        match_id = payload.get('match_id')
        player_puuid = payload.get('player_puuid')
        team = payload.get('team')
        
        if not all([match_id, player_puuid]):
            return
        
        logger.info(f"Player {player_puuid} joined match {match_id} (Team: {team})")
        
        # TODO: Track join status, start match when all 10 players joined
        # For now, just acknowledge
        await self.send(text_data=json.dumps({
            'event': 'player_joined_ack',
            'data': {'match_id': match_id, 'player_puuid': player_puuid}
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
            from .match_execution import MatchExecutionManager
            
            result = await MatchExecutionManager.handle_match_started(
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
            from .match_monitor import MatchMonitor
            
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
            from .match_execution import MatchExecutionManager
            
            await MatchExecutionManager.handle_match_completion(
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
            from .match_execution import MatchExecutionManager
            
            token = await MatchExecutionManager.generate_rejoin_token(
                match_id, player_puuid
            )
            
            await self.send(text_data=json.dumps({
                'event': 'rejoin_token',
                'data': {'token': token, 'match_id': match_id}
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
            from .match_monitor import MatchMonitor
            
            result = await MatchMonitor.get_match_statistics(match_id)
            
            if result['status'] == 'success':
                await self.send(text_data=json.dumps({
                    'event': 'match_statistics',
                    'data': result['data']
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
    
    async def match_starting(self, event):
        """Send match_starting event to client"""
        await self.send(text_data=json.dumps({
            'event': 'match_starting',
            'data': {
                'match_id': event['match_id'],
                'constructor_puuid': event['constructor_puuid'],
                'is_constructor': event['is_constructor'],
                'map': event['map'],
                'server': event['server'],
                'team': event['team']
            }
        }))
    
    
    async def join_custom_game(self, event):
        """Send join_custom_game event to client"""
        await self.send(text_data=json.dumps({
            'event': 'join_custom_game',
            'data': {
                'match_id': event['match_id'],
                'pregame_id': event['pregame_id'],
                'team': event['team']
            }
        }))
    
    
    async def match_in_progress(self, event):
        """Send match_in_progress event to client"""
        await self.send(text_data=json.dumps({
            'event': 'match_in_progress',
            'data': {
                'match_id': event['match_id'],
                'coregame_id': event['coregame_id'],
                'map': event['map'],
                'server': event['server']
            }
        }))
    
    
    async def match_score_update(self, event):
        """Send score update to spectators"""
        await self.send(text_data=json.dumps({
            'event': 'match_score_update',
            'data': {
                'match_id': event['match_id'],
                'team_a_score': event['team_a_score'],
                'team_b_score': event['team_b_score'],
                'current_round': event['current_round']
            }
        }))
    
    
    async def match_completed(self, event):
        """Send match completion event"""
        await self.send(text_data=json.dumps({
            'event': 'match_completed',
            'data': {
                'match_id': event['match_id'],
                'team_a_score': event['team_a_score'],
                'team_b_score': event['team_b_score'],
                'winner': event.get('winner'),
                'final_data': event.get('final_data', {})
            }
        }))
    
    
    ### Validate ###
    
    def get_lobby_group_name(self, lobby_id):
        if not lobby_id:
            raise ValueError("Lobby ID is required.")
        return f"lobby_{lobby_id}"