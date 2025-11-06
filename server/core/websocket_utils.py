"""
WebSocket utility functions for channel layer operations.
Provides helper functions for common WebSocket broadcast patterns.
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


class WebSocketBroadcaster:
    """
    Utility class for broadcasting messages via Django Channels.
    """
    
    @staticmethod
    def get_channel_layer():
        """Get the default channel layer."""
        return get_channel_layer()
    
    @staticmethod
    def broadcast_to_group(group_name: str, event_type: str, data: dict) -> bool:
        """
        Broadcast a message to a channel group (SYNC version for Celery tasks).
        
        Args:
            group_name: Channel group name (e.g., "lobby_{lobby_id}")
            event_type: Event type (maps to consumer method, e.g., "lobby_update")
            data: Event data dictionary
            
        Returns:
            bool: True if successful
        """
        try:
            channel_layer = WebSocketBroadcaster.get_channel_layer()
            
            if not channel_layer:
                logger.error("Channel layer is None")
                return False
            
            # Add type to data
            message = {'type': event_type, **data}
            
            # Use async_to_sync for Celery tasks
            async_to_sync(channel_layer.group_send)(group_name, message)
            
            logger.debug(f"Broadcast '{event_type}' to group '{group_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast to group {group_name}: {e}")
            return False
    
    @staticmethod
    async def async_broadcast_to_group(group_name: str, event_type: str, data: dict) -> bool:
        """
        Broadcast a message to a channel group (ASYNC version for consumers).
        
        Args:
            group_name: Channel group name
            event_type: Event type
            data: Event data dictionary
            
        Returns:
            bool: True if successful
        """
        try:
            channel_layer = WebSocketBroadcaster.get_channel_layer()
            
            if not channel_layer:
                logger.error("Channel layer is None")
                return False
            
            # Add type to data
            message = {'type': event_type, **data}
            
            # Use await for async contexts
            await channel_layer.group_send(group_name, message)
            
            logger.debug(f"Async broadcast '{event_type}' to group '{group_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to async broadcast to group {group_name}: {e}")
            return False
    
    @staticmethod
    def broadcast_to_player(puuid: str, event_type: str, data: dict) -> bool:
        """
        Send a message to a specific player.
        
        Args:
            puuid: Player PUUID
            event_type: Event type
            data: Event data
            
        Returns:
            bool: True if successful
        """
        group_name = f"player_{puuid}"
        return WebSocketBroadcaster.broadcast_to_group(group_name, event_type, data)
    
    @staticmethod
    def broadcast_to_lobby(lobby_id: str, event_type: str, data: dict) -> bool:
        """
        Send a message to all players in a lobby.
        
        Args:
            lobby_id: Lobby ID
            event_type: Event type
            data: Event data
            
        Returns:
            bool: True if successful
        """
        group_name = f"lobby_{lobby_id}"
        return WebSocketBroadcaster.broadcast_to_group(group_name, event_type, data)
    
    @staticmethod
    def broadcast_to_match(match_id: str, event_type: str, data: dict) -> bool:
        """
        Send a message to all players in a match.
        
        Args:
            match_id: Match ID
            event_type: Event type
            data: Event data
            
        Returns:
            bool: True if successful
        """
        group_name = f"match_{match_id}"
        return WebSocketBroadcaster.broadcast_to_group(group_name, event_type, data)

