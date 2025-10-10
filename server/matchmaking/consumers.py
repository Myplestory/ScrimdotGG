import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async
from django.db.models import Avg
from django.apps import apps
from datetime import datetime

# UTILITY
from .matchconfirm import mark_acceptance, check_all_accepted, finalize_match
from .matchmaking import add_lobby_to_queue, remove_lobby_from_queue
from scrimgg.serializers import LobbySerializer, PlayerSerializer


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
            if action == 'add_lobby_to_queue':
                await self.add_lobby_to_queue(text_data_json)
            elif action == 'remove_lobby_from_queue':
                await self.remove_lobby_from_queue(text_data_json)
            elif action == 'accept_match':
                await self.accept_match(text_data_json)
            elif action == 'create_lobby':
                await self.create_lobby(text_data_json)
            elif action == 'get_player_model':
                await self.get_player_model(text_data_json)
            elif action == 'lobby_message':
                await self.handle_lobby_message(text_data_json)
            else:
                await self.send(text_data=json.dumps({"error": "Invalid action"}))
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

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
        Player = apps.get_model('scrimgg', 'Player')
        Lobby = apps.get_model('scrimgg', 'Lobby')
        payload = data.get("payload")
        player_id = payload.get('puuid')
        if not player_id:
            await self.send(text_data=json.dumps({"error": "Player ID is required."}))
            print("Error: Player ID is required.")
            return
        try:
            player = await sync_to_async(Player.objects.get)(puuid=player_id)
            print(f"Fetched Player: PK={player.pk}, PUUID={player.puuid}")
            lobby = await sync_to_async(
                Lobby.objects.filter(lobby_leader=player, is_active=True).first
            )()
            if lobby:
                player_in_lobby = await sync_to_async(lambda: lobby.players.filter(pk=player.pk).exists())()
                if not player_in_lobby:
                    await sync_to_async(lobby.players.add)(player)
                    print(f"Added Player PK={player.pk} to Lobby ID={lobby.pk}")
                    lobby.size += 1
                    lobby.average_elo = await sync_to_async(
                        lambda: lobby.players.aggregate(Avg('elo'))['elo__avg'] or 0
                    )()
                    await sync_to_async(lobby.save)()
                    print(f"Updated Lobby ID={lobby.pk}: size={lobby.size}, average_elo={lobby.average_elo}")
                else:
                    print("Player already in the lobby")
            else:
                lobby = await sync_to_async(Lobby.objects.create)(lobby_leader=player)
                print(f"Created new Lobby: ID={lobby.pk}, Leader PK={player.pk}")
                await sync_to_async(lobby.players.add)(player)
                lobby.size = 1
                lobby.average_elo = player.elo
                await sync_to_async(lobby.save)()
                print(f"Updated new Lobby ID={lobby.pk}: size={lobby.size}, average_elo={lobby.average_elo}")
            self.lobby_group_name = f"lobby_{lobby.id}"
            await self.channel_layer.group_add(self.lobby_group_name, self.channel_name)
            print(f"WebSocket added to group: {self.lobby_group_name}")
            serializer_data = await sync_to_async(lambda: LobbySerializer(lobby).data)()
            await self.send(text_data=json.dumps({
                "event": "lobby_created",
                "data": serializer_data
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({"error": f"Unexpected error: {str(e)}"}))
            print(f"Unexpected error in create_lobby: {str(e)}")

    async def add_lobby_to_queue(self, data):
        """
        Adds a lobby to the matchmaking queue.
        """
        lobby_id = data.get("lobby_id")
        lobby_rating = data.get("lobby_rating")
        if not lobby_id or not lobby_rating:
            await self.send(text_data=json.dumps({"error": "Invalid lobby data."}))
            return

        await add_lobby_to_queue(lobby_id, lobby_rating)
        await self.channel_layer.group_send(
            self.lobby_group_name,
            {
                'type': 'lobby_queued',
                'message': 'Lobby has been added to the matchmaking queue',
            }
        )
        

    async def remove_lobby_from_queue(self, data):
        """
        Removes a lobby from the matchmaking queue.
        """
        lobby_id = data.get("lobby_id")
        if not lobby_id:
            await self.send(text_data=json.dumps({"error": "Lobby ID is required."}))
            return

        await remove_lobby_from_queue(lobby_id)
        await self.channel_layer.group_send(
            self.lobby_group_name,
            {
                'type': 'lobby_removed_from_queue',
                'message': 'Lobby has been removed from the matchmaking queue',
            }
        )

    async def accept_match(self, data):
        """
        Handles match acceptance for a player. Finalizes match when all players accept.
        """
        match_confirmation_id = data.get("match_confirmation_id")
        if not match_confirmation_id:
            await self.send(text_data=json.dumps({"error": "Match confirmation ID is required."}))
            return

        Player = apps.get_model('scrimgg', 'Player')
        player_id = self.player_id  # Use the player_id from scope
        mark_acceptance(player_id, match_confirmation_id)

        if check_all_accepted(match_confirmation_id):
            finalize_match(match_confirmation_id)
            await self.channel_layer.group_send(
                self.lobby_group_name,
                {
                    'type': 'match_ready',
                    'message': 'Match is ready!',
                }
            )
        else:
            accepted_count = cache.scard(f"match:{match_confirmation_id}:accepted")
            await self.channel_layer.group_send(
                self.lobby_group_name,
                {
                    'type': 'player_accepted',
                    'accepted_count': accepted_count,
                }
            )
    

    # -------------------- Outgoing WebSocket Messages --------------------

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
            'action': 'lobby_queued',
            'message': event['message'],
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

    ### Validate ###
    
    def get_lobby_group_name(self, lobby_id):
        if not lobby_id:
            raise ValueError("Lobby ID is required.")
        return f"lobby_{lobby_id}"