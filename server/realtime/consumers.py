"""
Main WebSocket Consumer - Routes events to specialized handlers.

REFACTORED FROM: matchmaking/consumers.py (PugSocketConsumer)

This consumer maintains a single WebSocket connection per player but delegates
event handling to specialized handler classes for better code organization.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.apps import apps
import logging

from .handlers import LobbyHandler, MatchHandler, VetoHandler, ExecutionHandler

logger = logging.getLogger(__name__)


class RealtimeConsumer(AsyncWebsocketConsumer):
    """
    Single WebSocket connection that delegates to specialized handlers.
    Maintains backward compatibility with existing client code.
    """
    
    async def connect(self):
        """
        Called when a WebSocket handshake is initiated.
        Subscribe to player-specific channel and initialize handlers.
        """
        self.puuid = self.scope["url_route"]["kwargs"]["puuid"]
        self.player_group_name = f"player_{self.puuid}"
        
        # Subscribe to player's personal channel
        await self.channel_layer.group_add(self.player_group_name, self.channel_name)
        
        # Initialize specialized handlers
        self.lobby_handler = LobbyHandler(self)
        self.match_handler = MatchHandler(self)
        self.veto_handler = VetoHandler(self)
        self.execution_handler = ExecutionHandler(self)
        
        # Get player and auto-join lobby group if in one
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
        Handles WebSocket disconnection.
        Clean up lobby if user is lobby leader, then remove from all groups.
        """
        try:
            if hasattr(self, 'puuid') and self.puuid:
                await self.lobby_handler.cleanup_on_disconnect()
        except Exception as e:
            logger.error(f"Error during lobby cleanup on disconnect: {e}")
        finally:
            # Always remove from WebSocket groups
            await self.channel_layer.group_discard(self.player_group_name, self.channel_name)
            if hasattr(self, 'lobby_group_name') and self.lobby_group_name:
                await self.channel_layer.group_discard(self.lobby_group_name, self.channel_name)
            logger.info(f"WebSocket disconnected: PUUID = {self.puuid[:12]}...")
    
    async def receive(self, text_data):
        """
        Handles incoming WebSocket messages.
        Routes actions to specialized handlers.
        """
        try:
            data = json.loads(text_data)
            action = data.get('event')
            
            # Route to appropriate handler
            handler = self._get_handler_for_action(action)
            if handler:
                await handler.handle_event(action, data)
            else:
                await self.send(text_data=json.dumps({"error": "Invalid action"}))
                logger.warning(f"Unknown action received: {action}")
                
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))
            logger.error(f"Error handling WebSocket message: {str(e)}")
    
    def _get_handler_for_action(self, action):
        """
        Route action to appropriate handler.
        
        Args:
            action: Event name
            
        Returns:
            Handler instance or None
        """
        # Lobby management events
        lobby_actions = {
            'create_lobby', 'invite_to_lobby', 'kick_from_lobby', 'leave_lobby',
            'update_lobby_preferences', 'add_lobby_to_queue', 'remove_lobby_from_queue',
            'get_queue_status', 'check_queue_eligibility', 'get_player_model',
            'lobby_message'
        }
        
        # Match confirmation events
        match_actions = {
            'accept_match', 'decline_match'
        }
        
        # Veto and side selection events
        veto_actions = {
            'get_match_data', 'veto_server', 'veto_map', 'select_side'
        }
        
        # Match execution events
        execution_actions = {
            'custom_game_created', 'player_joined_game', 'player_join_failed',
            'match_started', 'match_score_update', 'match_completed',
            'request_rejoin', 'get_match_statistics'
        }
        
        if action in lobby_actions:
            return self.lobby_handler
        elif action in match_actions:
            return self.match_handler
        elif action in veto_actions:
            return self.veto_handler
        elif action in execution_actions:
            return self.execution_handler
        
        return None
    
    # -------------------- Dynamic Group Management --------------------
    
    async def join_lobby_group(self, lobby_id):
        """Called when player joins/creates a lobby"""
        self.lobby_group_name = f"lobby_{lobby_id}"
        await self.channel_layer.group_add(self.lobby_group_name, self.channel_name)
        logger.debug(f"Player {self.puuid[:8]}... joined lobby group: {lobby_id}")
    
    async def leave_lobby_group(self):
        """Called when player leaves a lobby"""
        if hasattr(self, 'lobby_group_name'):
            await self.channel_layer.group_discard(self.lobby_group_name, self.channel_name)
            logger.debug(f"Player {self.puuid[:8]}... left lobby group")
            delattr(self, 'lobby_group_name')
    
    async def join_match_group(self, match_id):
        """Called when match is confirmed"""
        self.match_group_name = f"match_{match_id}"
        await self.channel_layer.group_add(self.match_group_name, self.channel_name)
        logger.debug(f"Player {self.puuid[:8]}... joined match group: {match_id}")
    
    # -------------------- Server -> Client Event Handlers --------------------
    # These methods are called by channel_layer.group_send()
    
    async def lobby_created(self, event):
        """Handle lobby_created broadcast"""
        await self.send(text_data=json.dumps({'event': 'lobby_created', 'payload': event}))
    
    async def lobby_update(self, event):
        """Handle lobby_update broadcast"""
        await self.send(text_data=json.dumps({'event': 'lobby_update', 'payload': event}))
    
    async def lobby_destroyed(self, event):
        """Handle lobby_destroyed broadcast"""
        await self.send(text_data=json.dumps({'event': 'lobby_destroyed', 'payload': event}))
    
    async def lobby_leader_changed(self, event):
        """Handle lobby_leader_changed broadcast"""
        await self.send(text_data=json.dumps({'event': 'lobby_leader_changed', 'payload': event}))
    
    async def player_left_lobby(self, event):
        """Handle player_left_lobby broadcast"""
        await self.send(text_data=json.dumps({'event': 'player_left_lobby', 'payload': event}))
    
    async def player_joined_lobby(self, event):
        """Handle player_joined_lobby broadcast"""
        await self.send(text_data=json.dumps({'event': 'player_joined_lobby', 'payload': event}))
    
    async def lobby_message(self, event):
        """Handle lobby_message broadcast"""
        await self.send(text_data=json.dumps({'event': 'lobby_message', 'payload': event}))
    
    async def match_found(self, event):
        """Handle match_found broadcast"""
        await self.send(text_data=json.dumps({'event': 'match_found', 'payload': event}))
    
    async def match_confirmed(self, event):
        """Handle match_confirmed broadcast"""
        await self.send(text_data=json.dumps({'event': 'match_confirmed', 'payload': event}))
    
    async def match_timeout(self, event):
        """Handle match_timeout broadcast"""
        await self.send(text_data=json.dumps({'event': 'match_timeout', 'payload': event}))
    
    async def veto_started(self, event):
        """Handle veto_started broadcast"""
        await self.send(text_data=json.dumps({'event': 'veto_started', 'payload': event}))
    
    async def server_veto_update(self, event):
        """Handle server_veto_update broadcast"""
        await self.send(text_data=json.dumps({'event': 'server_veto_update', 'payload': event}))
    
    async def veto_update(self, event):
        """Handle veto_update broadcast"""
        await self.send(text_data=json.dumps({'event': 'veto_update', 'payload': event}))
    
    async def veto_complete(self, event):
        """Handle veto_complete broadcast"""
        await self.send(text_data=json.dumps({'event': 'veto_complete', 'payload': event}))
    
    async def side_selection_started(self, event):
        """Handle side_selection_started broadcast"""
        await self.send(text_data=json.dumps({'event': 'side_selection_started', 'payload': event}))
    
    async def side_selected(self, event):
        """Handle side_selected broadcast"""
        await self.send(text_data=json.dumps({'event': 'side_selected', 'payload': event}))
    
    async def match_ready(self, event):
        """Handle match_ready broadcast"""
        await self.send(text_data=json.dumps({'event': 'match_ready', 'payload': event}))
    
    async def player_accepted(self, event):
        """Handle player_accepted broadcast"""
        await self.send(text_data=json.dumps({'event': 'player_accepted', 'payload': event}))
    
    async def enqueue(self, event):
        """Handle enqueue broadcast"""
        await self.send(text_data=json.dumps({'event': 'enqueue', 'payload': event}))
    
    async def dequeue(self, event):
        """Handle dequeue broadcast"""
        await self.send(text_data=json.dumps({'event': 'dequeue', 'payload': event}))
    
    async def player_model(self, event):
        """Handle player_model response"""
        await self.send(text_data=json.dumps({'event': 'player_model', 'payload': event}))
    
    async def match_data(self, event):
        """Handle match_data response"""
        await self.send(text_data=json.dumps({'event': 'match_data', 'payload': event}))
    
    async def direct_message(self, event):
        """Handle direct_message broadcast"""
        await self.send(text_data=json.dumps({'event': 'direct_message', 'payload': event}))

