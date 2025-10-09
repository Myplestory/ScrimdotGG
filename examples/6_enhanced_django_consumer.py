# ScrimGG/scrimgg/server/scrimgg/matchmaking/consumers_enhanced.py
# Enhanced Django Channels Consumer with full match flow

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async
from django.db.models import Avg
from django.apps import apps
from datetime import datetime

# Import our new systems
from .veto_system import VetoSystem
from .match_coordinator import MatchCoordinator, MatchState
from .matchmaking import add_lobby_to_queue, remove_lobby_from_queue
from scrimgg.serializers import LobbySerializer, PlayerSerializer


class PugSocketConsumer(AsyncWebsocketConsumer):
    """
    Enhanced WebSocket consumer with full FACEIT-like match flow:
    1. Lobby creation/management
    2. Queue system
    3. Match found
    4. Veto phase
    5. Match acceptance
    6. Custom game creation
    7. Player verification
    8. Match monitoring
    9. Result collection
    """
    
    async def connect(self):
        """
        Called when a WebSocket handshake is initiated.
        """
        self.puuid = self.scope["url_route"]["kwargs"]["puuid"]
        self.player_group_name = f"player_{self.puuid}"
        self.lobby_id = None
        self.match_id = None
        
        # Add to player-specific group (always)
        await self.channel_layer.group_add(self.player_group_name, self.channel_name)
        
        # Check if player is in an active lobby and add to lobby group
        Player = apps.get_model('scrimgg', 'Player')
        Lobby = apps.get_model('scrimgg', 'Lobby')
        
        try:
            player = await sync_to_async(Player.objects.get)(puuid=self.puuid)
            lobby = await sync_to_async(Lobby.objects.filter(players=player, is_active=True).first)()
            
            if lobby:
                self.lobby_id = str(lobby.id)
                self.lobby_group_name = f"lobby_{lobby.id}"
                await self.channel_layer.group_add(self.lobby_group_name, self.channel_name)
                print(f"WebSocket reconnected to lobby: {self.lobby_group_name}")
        except Exception as e:
            print(f"Error during WebSocket connect: {e}")
        
        await self.accept()
        print(f"WebSocket connected: PUUID = {self.puuid}")

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.
        """
        await self.channel_layer.group_discard(self.player_group_name, self.channel_name)
        
        if hasattr(self, 'lobby_group_name') and self.lobby_group_name:
            await self.channel_layer.group_discard(self.lobby_group_name, self.channel_name)
        
        if self.match_id:
            await self.channel_layer.group_discard(f"match_{self.match_id}", self.channel_name)
        
        print(f"WebSocket disconnected: PUUID = {self.puuid}")

    async def receive(self, text_data):
        """
        Handles incoming WebSocket messages. Routes actions to their respective handlers.
        """
        try:
            data = json.loads(text_data)
            action = data.get('event')
            payload = data.get('payload', {})
            
            print(f"Received event: {action} from {self.puuid}")
            
            # Route to handlers
            handlers = {
                # Lobby operations
                'create_lobby': self.create_lobby,
                'join_lobby': self.join_lobby,
                'leave_lobby': self.leave_lobby,
                'get_player_model': self.get_player_model,
                
                # Queue operations
                'add_lobby_to_queue': self.add_lobby_to_queue,
                'remove_lobby_from_queue': self.remove_lobby_from_queue,
                
                # Veto operations
                'veto_action': self.handle_veto_action,
                
                # Match operations
                'accept_match': self.accept_match,
                'decline_match': self.decline_match,
                'pregame_created': self.pregame_created,
                'player_joined_game': self.player_joined_game,
                'match_results': self.handle_match_results,
                
                # Chat
                'lobby_message': self.handle_lobby_message,
                'direct_message': self.handle_direct_message,
            }
            
            handler = handlers.get(action)
            if handler:
                await handler(payload)
            else:
                await self.send(text_data=json.dumps({"error": f"Unknown action: {action}"}))
                
        except Exception as e:
            print(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({"error": str(e)}))

    # ==================== LOBBY OPERATIONS ====================
    
    async def create_lobby(self, payload):
        """Create a new lobby."""
        Player = apps.get_model('scrimgg', 'Player')
        Lobby = apps.get_model('scrimgg', 'Lobby')
        
        player_id = payload.get('puuid', self.puuid)
        
        try:
            player = await sync_to_async(Player.objects.get)(puuid=player_id)
            
            # Check if player already in active lobby
            existing_lobby = await sync_to_async(
                Lobby.objects.filter(players=player, is_active=True).first
            )()
            
            if existing_lobby:
                # Return existing lobby
                lobby = existing_lobby
            else:
                # Create new lobby
                lobby = await sync_to_async(Lobby.objects.create)(lobby_leader=player)
                await sync_to_async(lobby.players.add)(player)
                lobby.size = 1
                lobby.average_elo = player.elo
                await sync_to_async(lobby.save)()
            
            # Join lobby group
            self.lobby_id = str(lobby.id)
            self.lobby_group_name = f"lobby_{lobby.id}"
            await self.channel_layer.group_add(self.lobby_group_name, self.channel_name)
            
            # Send lobby data
            serializer_data = await sync_to_async(lambda: LobbySerializer(lobby).data)()
            await self.send(text_data=json.dumps({
                "event": "lobby_created",
                "data": serializer_data
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Create lobby error: {str(e)}"}))

    async def join_lobby(self, payload):
        """Join an existing lobby."""
        # Implementation similar to create_lobby
        pass

    async def leave_lobby(self, payload):
        """Leave current lobby."""
        # Remove player from lobby, update lobby state
        pass

    async def get_player_model(self, payload):
        """Fetch player model data."""
        Player = apps.get_model('scrimgg', 'Player')
        player_id = payload.get('puuid', self.puuid)
        
        try:
            player = await sync_to_async(Player.objects.get)(puuid=player_id)
            serialized_player = await sync_to_async(lambda: PlayerSerializer(player).data)()
            
            await self.send(text_data=json.dumps({
                "event": "player_model",
                "data": serialized_player
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Player not found: {str(e)}"}))

    # ==================== QUEUE OPERATIONS ====================
    
    async def add_lobby_to_queue(self, payload):
        """
        Add lobby to matchmaking queue.
        """
        if not self.lobby_id:
            await self.send(text_data=json.dumps({"error": "Not in a lobby"}))
            return
        
        Lobby = apps.get_model('scrimgg', 'Lobby')
        lobby = await sync_to_async(Lobby.objects.get)(id=self.lobby_id)
        
        # Validate lobby is ready (has enough players, etc.)
        if lobby.size < 1:  # Adjust minimum as needed
            await self.send(text_data=json.dumps({"error": "Lobby too small"}))
            return
        
        # Add to queue
        map_preferences = payload.get('map_preferences', [])
        server_preferences = payload.get('server_preferences', [])
        
        await add_lobby_to_queue(
            self.lobby_id,
            lobby.average_elo,
            map_preferences,
            server_preferences
        )
        
        # Mark lobby as in queue
        lobby.in_queue = True
        await sync_to_async(lobby.save)()
        
        # Notify lobby
        await self.channel_layer.group_send(
            self.lobby_group_name,
            {
                'type': 'lobby_queued',
                'message': 'Lobby is now in queue',
            }
        )

    async def remove_lobby_from_queue(self, payload):
        """Remove lobby from queue."""
        if not self.lobby_id:
            return
        
        await remove_lobby_from_queue(self.lobby_id)
        
        Lobby = apps.get_model('scrimgg', 'Lobby')
        lobby = await sync_to_async(Lobby.objects.get)(id=self.lobby_id)
        lobby.in_queue = False
        await sync_to_async(lobby.save)()
        
        await self.channel_layer.group_send(
            self.lobby_group_name,
            {
                'type': 'lobby_removed_from_queue',
                'message': 'Lobby removed from queue',
            }
        )

    # ==================== VETO PHASE ====================
    
    async def handle_veto_action(self, payload):
        """
        Handle a veto action (ban/pick map or server).
        """
        match_id = payload.get('match_id')
        action = payload.get('action')  # "ban" or "pick"
        veto_type = payload.get('type')  # "map" or "server"
        value = payload.get('value')  # e.g., "Ascent"
        
        if not match_id or not self.lobby_id:
            await self.send(text_data=json.dumps({"error": "Invalid veto request"}))
            return
        
        try:
            veto_system = VetoSystem(match_id)
            
            # Execute veto action
            updated_state = veto_system.execute_veto_action(
                lobby_id=self.lobby_id,
                action=action,
                veto_type=veto_type,
                value=value
            )
            
            # Broadcast update to all match participants
            await self.channel_layer.group_send(
                f"match_{match_id}",
                {
                    'type': 'veto_updated',
                    'state': veto_system.get_veto_summary()
                }
            )
            
            # If veto complete, proceed to acceptance
            if updated_state['completed']:
                coordinator = MatchCoordinator(match_id)
                await coordinator.complete_veto(
                    updated_state['final_map'],
                    updated_state['final_server']
                )
            
        except ValueError as e:
            await self.send(text_data=json.dumps({
                'event': 'veto_error',
                'message': str(e)
            }))

    # ==================== MATCH ACCEPTANCE ====================
    
    async def accept_match(self, payload):
        """
        Player accepts the match.
        """
        match_id = payload.get('match_id')
        
        if not match_id:
            await self.send(text_data=json.dumps({"error": "No match ID"}))
            return
        
        # Join match group
        self.match_id = match_id
        await self.channel_layer.group_add(f"match_{match_id}", self.channel_name)
        
        # Record acceptance
        coordinator = MatchCoordinator(match_id)
        all_accepted = await coordinator.player_accept(self.puuid)
        
        if all_accepted:
            print(f"All players accepted match {match_id}")

    async def decline_match(self, payload):
        """
        Player declines the match.
        """
        match_id = payload.get('match_id')
        
        if not match_id:
            return
        
        # Cancel the match
        coordinator = MatchCoordinator(match_id)
        await coordinator.player_decline(self.puuid)

    # ==================== CUSTOM GAME CREATION ====================
    
    async def pregame_created(self, payload):
        """
        Constructor reports that custom game has been created.
        """
        match_id = payload.get('match_id')
        pregame_id = payload.get('pregame_id')
        
        if not match_id or not pregame_id:
            await self.send(text_data=json.dumps({"error": "Invalid pregame data"}))
            return
        
        # Update match coordinator
        coordinator = MatchCoordinator(match_id)
        await coordinator.set_pregame_id(pregame_id)

    async def player_joined_game(self, payload):
        """
        Player reports they have joined the custom game.
        """
        match_id = payload.get('match_id')
        
        if not match_id:
            return
        
        coordinator = MatchCoordinator(match_id)
        all_joined = await coordinator.player_joined_game(self.puuid)
        
        if all_joined:
            print(f"All players joined match {match_id}")

    # ==================== MATCH COMPLETION ====================
    
    async def handle_match_results(self, payload):
        """
        Receive match results from a client.
        """
        match_id = payload.get('match_id')
        results = payload.get('results')
        
        if not match_id or not results:
            return
        
        coordinator = MatchCoordinator(match_id)
        await coordinator.match_ended(results)

    # ==================== CHAT ====================
    
    async def handle_lobby_message(self, payload):
        """Handle lobby chat messages."""
        message = payload.get('message')
        lobby_id = payload.get('lobby_id', self.lobby_id)
        username = payload.get('userAlias', 'Anonymous')
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        
        if not message or not lobby_id:
            await self.send(text_data=json.dumps({"error": "Invalid chat message"}))
            return
        
        # Broadcast to lobby
        await self.channel_layer.group_send(
            f"lobby_{lobby_id}",
            {
                'type': 'lobby_message',
                'username': username,
                'message': message,
                'timestamp': timestamp,
            }
        )

    async def handle_direct_message(self, payload):
        """Handle direct messages between players."""
        message = payload.get('message')
        recipient_puuid = payload.get('recipient_puuid')
        username = payload.get('username', 'Anonymous')
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        
        if not message or not recipient_puuid:
            return
        
        # Send to recipient
        await self.channel_layer.group_send(
            f"player_{recipient_puuid}",
            {
                'type': 'direct_message',
                'username': username,
                'message': message,
                'timestamp': timestamp,
            }
        )

    # ==================== OUTGOING EVENT HANDLERS ====================
    
    async def lobby_queued(self, event):
        """Lobby has been queued."""
        await self.send(text_data=json.dumps({
            'event': 'lobby_queued',
            'message': event['message'],
        }))

    async def lobby_removed_from_queue(self, event):
        """Lobby removed from queue."""
        await self.send(text_data=json.dumps({
            'event': 'lobby_dequeued',
            'message': event['message'],
        }))

    async def match_event(self, event):
        """Generic match event broadcaster."""
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'payload': event['payload'],
        }))

    async def player_event(self, event):
        """Generic player event broadcaster."""
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'payload': event['payload'],
        }))

    async def veto_updated(self, event):
        """Veto state has been updated."""
        await self.send(text_data=json.dumps({
            'event': 'veto_updated',
            'state': event['state'],
        }))

    async def lobby_message(self, event):
        """Lobby chat message."""
        await self.send(text_data=json.dumps({
            'event': 'lobby_message',
            'username': event['username'],
            'message': event['message'],
            'timestamp': event['timestamp'],
        }))

    async def direct_message(self, event):
        """Direct message."""
        await self.send(text_data=json.dumps({
            'event': 'direct_message',
            'username': event['username'],
            'message': event['message'],
            'timestamp': event['timestamp'],
        }))

