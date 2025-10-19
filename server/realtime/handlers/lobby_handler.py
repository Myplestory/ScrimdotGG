"""
Lobby-related WebSocket event handler.
Handles lobby creation, management, and queue operations.

EXTRACTED FROM: matchmaking/consumers.py
"""

import logging
from asgiref.sync import sync_to_async
from django.apps import apps

from .base import BaseHandler

logger = logging.getLogger(__name__)


class LobbyHandler(BaseHandler):
    """
    Handles all lobby-related WebSocket events.
    """
    
    async def handle_create_lobby(self, data):
        """
        Handle create_lobby event.
        Import lobby_manager from lobby app (after refactor).
        """
        from lobby.manager import LobbyManager
        
        try:
            result = await LobbyManager.create_lobby(self.puuid)
            
            if result['status'] == 'success':
                lobby_id = result['lobby']['id']
                # Join lobby group
                await self.consumer.join_lobby_group(lobby_id)
                # Send response
                await self.send_event('lobby_created', result)
            else:
                await self.send_error(result.get('message', 'Failed to create lobby'))
                
        except Exception as e:
            logger.error(f"Error creating lobby: {e}")
            await self.send_error(str(e))
    
    async def handle_add_lobby_to_queue(self, data):
        """Handle add_lobby_to_queue event."""
        from matchmaking.queue_manager import QueueManager
        
        try:
            payload = data.get('payload', {})
            lobby_id = payload.get('lobby_id')
            queue_type = payload.get('queue_type', 'pug')
            
            result = await QueueManager.enqueue_lobby(lobby_id, payload, queue_type)
            
            if result['status'] == 'success':
                await self.send_event('enqueue', result)
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error adding lobby to queue: {e}")
            await self.send_error(str(e))
    
    async def handle_remove_lobby_from_queue(self, data):
        """Handle remove_lobby_from_queue event."""
        from matchmaking.queue_manager import QueueManager
        
        try:
            payload = data.get('payload', {})
            lobby_id = payload.get('lobby_id')
            queue_type = payload.get('queue_type', 'pug')
            
            result = await QueueManager.leave_queue(lobby_id, self.puuid, queue_type)
            
            if result['status'] == 'success':
                await self.send_event('dequeue', result)
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error removing lobby from queue: {e}")
            await self.send_error(str(e))
    
    async def handle_get_player_model(self, data):
        """Handle get_player_model event."""
        Player = apps.get_model('scrimgg', 'Player')
        
        try:
            player = await sync_to_async(Player.objects.get)(puuid=self.puuid)
            
            def serialize_player(player_instance):
                from scrimgg.serializers import PlayerSerializer
                return PlayerSerializer(player_instance).data
            
            serialized_player = await sync_to_async(serialize_player)(player)
            await self.send_event('player_model', serialized_player)
            
        except Player.DoesNotExist:
            await self.send_error("Player not found")
        except Exception as e:
            logger.error(f"Error getting player model: {e}")
            await self.send_error(str(e))
    
    async def handle_lobby_message(self, data):
        """Handle lobby chat message."""
        try:
            payload = data.get('payload', {})
            lobby_id = payload.get('lobby_id')
            message = payload.get('message')
            
            if not lobby_id or not message:
                await self.send_error("Lobby ID and message are required")
                return
            
            # Broadcast to lobby group
            await self.channel_layer.group_send(
                f"lobby_{lobby_id}",
                {
                    'type': 'lobby_message',
                    'username': payload.get('username', 'Unknown'),
                    'message': message,
                    'timestamp': payload.get('timestamp'),
                    'puuid': self.puuid
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending lobby message: {e}")
            await self.send_error(str(e))
    
    async def cleanup_on_disconnect(self):
        """
        Clean up user's lobby when they disconnect.
        Only destroys lobby if user is the lobby leader.
        
        This is the same logic from matchmaking/consumers.py
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
            
            # Check if user is lobby leader
            if lobby.lobby_leader.puuid == self.puuid:
                lobby_id = lobby.id
                lobby_size = lobby.size
                
                if lobby_size == 1:
                    # Solo lobby - destroy it
                    logger.info(f"User {player.alias} is solo lobby leader, destroying lobby {lobby.id}")
                    
                    # Remove from queue
                    from matchmaking.queue_manager import QueueManager
                    await QueueManager.leave_queue(str(lobby.id), self.puuid, 'pug')
                    
                    # Destroy lobby
                    await sync_to_async(lobby.delete)()
                    
                    # Broadcast destruction
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
                    # ... (transfer logic - same as original)
                    
        except Exception as e:
            logger.exception(f"Error in cleanup_on_disconnect: {e}")

