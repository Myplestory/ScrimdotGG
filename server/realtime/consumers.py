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
        """Send lobby destroyed event to client"""
        await self.send(text_data=json.dumps({
            'event': 'lobby_destroyed',
            'payload': {
                'message': event.get('message', 'Lobby was destroyed'),
                'reason': event.get('reason', 'unknown')
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
    
    async def player_left_lobby(self, event):
        """Notify clients when a player leaves the lobby."""
        await self.send(text_data=json.dumps({
            'event': 'player_left_lobby',
            'payload': {
                'lobby': event.get('lobby', {}),
                'player_puuid': event.get('player_puuid'),
                'reason': event.get('reason', 'left')
            }
        }))
    
    async def player_joined_lobby(self, event):
        """Notify clients when a player joins the lobby."""
        await self.send(text_data=json.dumps({
            'event': 'player_joined_lobby',
            'payload': {
                'lobby': event.get('lobby', {}),
                'player_puuid': event.get('player_puuid')
            }
        }))
    
    async def kicked_from_lobby(self, event):
        """Notify a player they were kicked from a lobby."""
        await self.send(text_data=json.dumps({
            'event': 'kicked_from_lobby',
            'payload': {
                'lobby_id': event.get('lobby_id'),
                'message': event.get('message', 'You were kicked from the lobby')
            }
        }))
    
    async def lobby_disbanded(self, event):
        """Notify clients when lobby is disbanded."""
        await self.send(text_data=json.dumps({
            'event': 'lobby_disbanded',
            'payload': {
                'reason': event.get('reason', 'unknown')
            }
        }))
    
    async def lobby_preferences_updated(self, event):
        """Notify clients when lobby preferences are updated."""
        await self.send(text_data=json.dumps({
            'event': 'lobby_preferences_updated',
            'payload': event.get('lobby', {})
        }))
    
    async def lobby_message(self, event):
        """Send lobby chat messages to the frontend."""
        await self.send(text_data=json.dumps({
            'event': 'lobby_message',
            'username': event.get('username', 'Unknown'),
            'message': event.get('message', ''),
            'timestamp': event.get('timestamp'),
        }))
    
    async def match_found(self, event):
        """Sends a notification that a match has been found."""
        match_id = event.get('match_confirmation_id')
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
    
    async def match_confirmed(self, event):
        """All players accepted - redirect to match page."""
        match_id = event.get('match_id')
        
        # CRITICAL FIX: Join match group for future match events (veto updates)
        if match_id:
            await self.join_match_group(match_id)
        
        await self.send(text_data=json.dumps({
            'event': 'match_confirmed',
            'payload': {
                'match_id': match_id,
                'team': event.get('team'),
                'redirect_url': f"/match/{match_id}" if match_id else None
            }
        }))
    
    async def match_timeout(self, event):
        """Sends a notification that a match confirmation timed out."""
        await self.send(text_data=json.dumps({
            'event': 'match_timeout',
            'message': event.get('message', 'Match confirmation timed out'),
            'reason': event.get('reason', 'timeout')
        }))
    
    
    async def veto_complete(self, event):
        """Veto complete - final map selected."""
        await self.send(text_data=json.dumps({
            'event': 'veto_complete',
            'payload': {
                'match_id': event.get('match_id'),
                'final_map': event.get('final_map'),
                'side_selector': event.get('side_selector')
            }
        }))
    
    async def side_selection_started(self, event):
        """Handle side_selection_started broadcast"""
        await self.send(text_data=json.dumps({'event': 'side_selection_started', 'payload': event}))
    
    async def side_selected(self, event):
        """Handle side selected event - broadcast to all players in match."""
        await self.send(text_data=json.dumps({
            'event': 'side_selected',
            'payload': {
                'match_id': event.get('match_id'),
                'side': event.get('side'),
                'selected_by': event.get('selected_by'),
                'side_complete': event.get('side_complete', False)
            }
        }))
    
    async def match_ready(self, event):
        """Sends a notification that the match is ready (all players accepted)."""
        await self.send(text_data=json.dumps({
            'event': 'match_ready',
            'payload': {
                'match_id': event.get('match_id'),
                'message': event.get('message', 'Match is ready!')
            }
        }))
    
    async def player_accepted(self, event):
        """Sends a notification about player acceptance progress."""
        await self.send(text_data=json.dumps({
            'event': 'player_accepted',
            'payload': {
                'accepted_count': event.get('accepted_count', 0),
                'total_players': event.get('total_players', 10),
                'timeout_seconds': event.get('timeout_seconds', 30)
            }
        }))
    
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
        """
        Match data broadcast - ensures all players get captain/team info.
        CRITICAL: Adds player to match group for veto updates.
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
    
    async def match_state_update(self, event):
        """Handle unified match state snapshot broadcasts."""
        await self.send(text_data=json.dumps({
            'event': 'match_state_update',
            'payload': event.get('payload', {})
        }))
    
    async def direct_message(self, event):
        """Handle direct_message broadcast"""
        await self.send(text_data=json.dumps({'event': 'direct_message', 'payload': event}))
    
    # -------------------- Veto Broadcast Handlers --------------------
    # These receive from channel_layer and forward to WebSocket client
    
    async def server_veto_started(self, event):
        """Server veto phase has begun."""
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
        """A server was vetoed."""
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
        """Server veto phase completed - transition to map veto."""
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
        
        # Also send map_veto_started if applicable
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
        """Server veto timeout - auto-veto occurred."""
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
    
    async def map_vetoed(self, event):
        """A map was vetoed."""
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
        """Map veto phase has begun."""
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
        """Map veto timeout - auto-veto occurred."""
        await self.send(text_data=json.dumps({
            'event': 'map_veto_timeout',
            'payload': {
                'match_id': event.get('match_id'),
                'auto_vetoed_map': event.get('auto_vetoed_map'),
                'veto_complete': event.get('veto_complete', False),
                'next_turn': event.get('next_turn'),
                'remaining_maps': event.get('remaining_maps', []),
                'deadline': event.get('deadline'),
                'final_map': event.get('final_map')
            }
        }))
    
    async def side_selection_timeout(self, event):
        """Side selection timeout - auto-select occurred."""
        await self.send(text_data=json.dumps({
            'event': 'side_selection_timeout',
            'payload': {
                'match_id': event.get('match_id'),
                'auto_selected_side': event.get('auto_selected_side'),
                'side_selection_complete': event.get('side_selection_complete', False),
                'match_ready': event.get('match_ready', False)
            }
        }))

