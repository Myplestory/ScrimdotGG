"""
Base handler class for WebSocket event handlers.
"""

import json
import logging

logger = logging.getLogger(__name__)


class BaseHandler:
    """
    Base class for all WebSocket event handlers.
    Provides common functionality for sending messages and managing state.
    """
    
    def __init__(self, consumer):
        """
        Initialize handler with reference to consumer.
        
        Args:
            consumer: RealtimeConsumer instance
        """
        self.consumer = consumer
        self.channel_layer = consumer.channel_layer
        self.puuid = consumer.puuid
    
    async def handle_event(self, action, data):
        """
        Route event to appropriate handler method.
        
        Args:
            action: Event name
            data: Event data
        """
        # Convert action to method name (e.g., 'create_lobby' -> 'handle_create_lobby')
        method_name = f"handle_{action}"
        method = getattr(self, method_name, None)
        
        if method and callable(method):
            await method(data)
        else:
            logger.warning(f"No handler method found for action: {action}")
            await self.send_error(f"Unhandled action: {action}")
    
    async def send_event(self, event_name, payload):
        """
        Send an event to the client.
        
        Args:
            event_name: Event name
            payload: Event payload
        """
        await self.consumer.send(text_data=json.dumps({
            'event': event_name,
            'payload': payload
        }))
    
    async def send_error(self, message):
        """
        Send an error message to the client.
        
        Args:
            message: Error message
        """
        await self.consumer.send(text_data=json.dumps({
            'error': message
        }))
    
    async def send_success(self, message, data=None):
        """
        Send a success message to the client.
        
        Args:
            message: Success message
            data: Optional additional data
        """
        response = {
            'status': 'success',
            'message': message
        }
        if data:
            response.update(data)
        
        await self.consumer.send(text_data=json.dumps(response))

