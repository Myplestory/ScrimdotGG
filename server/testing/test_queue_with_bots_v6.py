"""
Queue Test with Bot Players V5 - Complete Game Flow Simulation
Creates 9 bot players with proper UUIDs that connect via WebSocket consumers.
Tests complete user flow including match acceptance, veto functionality, and game constructor logic.

This tests:
1. 9 bots with UUIDs connecting via WebSocket (ALL 9 will accept)
2. You join queue via client (10th player)
3. Matchmaker finds match
4. ALL 9 bots auto-accept via WebSocket
5. YOU accept
6. Match confirmed → redirect to match page
7. Veto phase starts and completes
8. Game constructor phase starts
9. Bots simulate joining custom game lobby
10. Constructor bot starts game when all players joined
11. Complete game flow simulation

Key improvements over V4:
- Added game constructor logic simulation
- Bots can act as constructor and start games
- Simulates custom game join process
- Hybrid execution flow driven by unified match_state_update snapshots
- Tests the new join tracking system
- Complete end-to-end game flow testing
- Realistic delays and error handling
- Added server veto phase handling with common server selection
- Uses assorted map preferences with 5 common maps (Ascent, Bind, Breeze, Fracture, Haven)
"""
import os
import sys
import asyncio
import django
import uuid
import json
import websockets
import logging
from typing import Dict, List, Optional

# Add server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
from matchmaking.lobby_manager import LobbyManager
from matchmaking.trueskill_manager import mmr_to_trueskill_mu
from asgiref.sync import sync_to_async
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotWebSocketClient:
    """
    WebSocket client that simulates a real user connecting to the Django consumer.
    """
    
    def __init__(self, bot_puuid: str, bot_alias: str):
        self.bot_puuid = bot_puuid
        self.bot_alias = bot_alias
        logger.info(f"[INIT] Bot {bot_alias} initialized with PUUID: '{bot_puuid}' (type: {type(bot_puuid)})")
        self.websocket = None
        self.lobby_id = None
        self.connected = False
        self.in_queue = False
        self.match_found = False
        self.match_confirmed = False
        self.veto_complete = False
        
        # Veto-related state
        self.current_match_id = None
        self.is_captain = False
        self.my_team = None
        self.available_maps = []
        self.vetoed_maps = []
        self.current_turn = None
        self.veto_deadline = None
        self.side_selection_active = False
        self.side_selection_pending = False
        self.side_selection_deadline = None
        
        # Game constructor state
        self.is_constructor = False
        self.pregame_id = None
        self.game_started = False
        self.joined_custom_game = False
        
        # Snapshot tracking / duplicate suppression
        self.latest_snapshot = None
        self.latest_snapshot_version = None
        self.last_processed_server_state = None
        self.last_processed_map_state = None

        # Server veto state
        self.available_servers = []
        self.vetoed_servers = []
        self.server_veto_turn = None
        self.server_veto_deadline = None
        # Map veto strategy (choose once per match)
        self.veto_strategy = random.choice(['random', 'aggressive', 'strategic'])
 
        # Snapshot tracking / duplicate suppression
        self.latest_snapshot = None
        self.latest_snapshot_version = None
        self.last_processed_server_state = None
        self.last_processed_map_state = None

        # Hybrid execution simulation state
        self.custom_game_created = False
        self.custom_game_acknowledged = False
        self.simulated_pregame_id = None
        self.join_instruction_received = False
        self.join_reported = False
        self.match_started_reported = False
        self.ready_to_start = False
        self.total_expected_players = 0
        self._pending_creation_task = None
        self._pending_join_task = None
        self._pending_start_task = None

    def _reset_match_flow_state(self):
        """Reset execution-phase state and cancel any pending background tasks."""
        for attr in ('_pending_creation_task', '_pending_join_task', '_pending_start_task'):
            task = getattr(self, attr, None)
            if task and not task.done():
                task.cancel()
            setattr(self, attr, None)

        self.custom_game_created = False
        self.custom_game_acknowledged = False
        self.simulated_pregame_id = None
        self.join_instruction_received = False
        self.join_reported = False
        self.match_started_reported = False
        self.ready_to_start = False
        self.joined_custom_game = False
        self.game_started = False
        self.pregame_id = None
        
    async def _handle_side_selection_started(self, payload: dict):
        """Handle side selection phase start."""
        self.side_selection_active = True
        self.side_selection_deadline = payload.get('deadline')
        side_selector = payload.get('side_selector')

        logger.info(f"Bot {self.bot_alias} side selection started")
        logger.info(f"   Side selector: {side_selector}")
        logger.info(f"   Deadline: {self.side_selection_deadline}")
        logger.info(f"   Is captain: {self.is_captain}, My team: {self.my_team}")

        if self.is_captain and side_selector == self.my_team and not self.side_selection_pending:
            self.side_selection_pending = True
            await self._select_match_side()
        else:
            self.side_selection_pending = False

    async def _handle_side_selected(self, payload: dict):
        """Handle side selected event."""
        self.side_selection_active = False
        self.side_selection_pending = False
        self.side_selection_deadline = None

        logger.info(f"Bot {self.bot_alias} received side selected event")
        logger.info(f"   Side: {payload.get('side')}")
        logger.info(f"   Selected by: {payload.get('selected_by')}")
        logger.info(f"   Side complete: {payload.get('side_complete')}")

    async def _handle_side_selection_timeout(self, payload: dict):
        """Handle side selection timeout (server auto-selected)."""
        self.side_selection_active = False
        self.side_selection_pending = False
        self.side_selection_deadline = None

        logger.info(f"Bot {self.bot_alias} side selection timeout occurred")
        logger.info(f"   Auto-selected side: {payload.get('auto_selected_side')}")
        logger.info(f"   Match ready: {payload.get('match_ready')}")

    async def _select_match_side(self):
        """Select a side when this bot is the active captain."""
        if not self.current_match_id:
            logger.warning(f"Bot {self.bot_alias} cannot select side without match ID")
            return

        chosen_side = random.choice(['attack', 'defend'])
        delay = random.uniform(1.0, 3.0)
        logger.info(f"Bot {self.bot_alias} selecting side '{chosen_side}' after {delay:.2f}s delay")

        await asyncio.sleep(delay)

        await self._send_message('select_side', {
            'match_id': self.current_match_id,
            'side': chosen_side
        })
        self.side_selection_pending = False
        self.veto_strategy = random.choice(['random', 'aggressive', 'strategic'])
        
        # Game constructor state
        self.is_constructor = False
        self.pregame_id = None
        self.game_started = False
        self.joined_custom_game = False
        self.side_selection_active = False
        self.side_selection_pending = False
        self.side_selection_deadline = None
 
        # Snapshot tracking / duplicate suppression
        self.latest_snapshot = None
        self.latest_snapshot_version = None
        self.last_processed_server_state = None
        self.last_processed_map_state = None
        
    async def connect(self):
        """Connect to the Django WebSocket consumer"""
        ws_url = f"ws://localhost:8000/ws/matchmaking/{self.bot_puuid}/"
        
        try:
            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.connected = True
            logger.info(f"Bot {self.bot_alias} connected to WebSocket")
            
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            logger.error(f"Bot {self.bot_alias} failed to connect: {e}")
            raise
    
    async def _listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                await self._handle_message(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f" Bot {self.bot_alias} WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Bot {self.bot_alias} message handling error: {e}")
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket messages"""
        event = data.get('event')
        payload = data.get('payload', {})
        error = data.get('error')
        
        # Log all messages for debugging
        logger.debug(f" Bot {self.bot_alias} received: {payload}")
        
        if error:
            logger.error(f"Bot {self.bot_alias} WebSocket error: {error}")
            
        elif event == 'lobby_created':
            logger.info(f" Bot {self.bot_alias} lobby created successfully")
            
        elif event == 'joined_queue':
            self.in_queue = True
            logger.info(f" Bot {self.bot_alias} joined queue successfully")
            
        elif event == 'queue_blocked':
            logger.error(f" Bot {self.bot_alias} queue blocked: {payload.get('message')}")
            
        elif event == 'match_found' or event == 'pug_match_found':
            self.match_found = True
            match_id = payload.get('match_id')
            logger.info(f" Bot {self.bot_alias} found match {match_id[:8] if match_id else 'Unknown'}, auto-accepting...")
            
            # Auto-accept the match (consumer expects match_id in payload)
            await self._send_message('accept_match', {
                'match_id': match_id,
                'player_puuid': self.bot_puuid
            })
            
        elif event == 'match_confirmed':
            self.match_confirmed = True
            self.current_match_id = payload.get('match_id')
            logger.info(f" Bot {self.bot_alias} match confirmed! Match ID: {self.current_match_id[:8] if self.current_match_id else 'Unknown'}")
            logger.info(f" Bot {self.bot_alias} waiting for automatic match_state_update broadcast...")

        elif event == 'match_state_update':
            await self._handle_match_state_update(payload)
        
        elif event == 'match_construction_started':
            # Handle constructor assignment
            await self._handle_construction_started(payload)
            
        elif event == 'join_custom_game':
            # Handle join custom game instruction
            await self._handle_join_custom_game(payload)
            
        elif event == 'all_players_joined':
            # Handle all players joined (constructor can start game)
            await self._handle_all_players_joined(payload)
            
        elif event == 'match_cancelled':
            # Handle match cancellation
            await self._handle_match_cancelled(payload)
            
        elif event == 'joined_custom_game':
            # Handle successful join confirmation
            await self._handle_joined_custom_game(payload)
            
        elif event == 'join_custom_game_failed':
            # Handle join failure
            await self._handle_join_custom_game_failed(payload)
            
        elif event == 'match_timeout':
            # Handle match timeout
            await self._handle_match_timeout(payload)
            
        elif event == 'error':
            logger.error(f"Bot {self.bot_alias} error: {payload}")
            
        else:
            # Log unhandled events for debugging
            logger.debug(f"Bot {self.bot_alias} unhandled event '{event}': {payload}")
 
    async def _handle_match_state_update(self, snapshot: dict):
        """Consume unified match state snapshots from the server."""
        self.latest_snapshot = snapshot

        state = snapshot.get('state')
        match_id = snapshot.get('match_id')
        last_event = snapshot.get('last_event')
        draft = snapshot.get('draft', {})

        meta = snapshot.get('meta') or {}
        version = meta.get('version') or meta.get('timestamp')
        if version is None:
            version = json.dumps({
                'state': state,
                'last_event': last_event,
                'servers': draft.get('servers'),
                'maps': draft.get('maps'),
                'side': draft.get('side'),
            }, sort_keys=True)

        if version == self.latest_snapshot_version:
            logger.debug(f" Bot {self.bot_alias} ignoring duplicate snapshot (version={version})")
            return

        self.latest_snapshot_version = version

        logger.info(f" Bot {self.bot_alias} processing match_state_update: state={state}, last_event={last_event}, version={version}")

        if match_id:
            self.current_match_id = match_id

        team_a_players = snapshot.get('team_a_players', [])
        team_b_players = snapshot.get('team_b_players', [])
        self._update_team_and_captain(team_a_players, team_b_players)

        total_players = len(team_a_players) + len(team_b_players)
        if total_players == 0:
            total_players = 10
        self.total_expected_players = total_players

        execution_info = snapshot.get('execution') or {}
        await self._drive_execution_state(snapshot, execution_info, total_players)

        if state == 'SERVER_VETO':
            await self._sync_server_veto(draft.get('servers', {}), last_event)
        elif state == 'MAP_VETO':
            await self._sync_map_veto(draft.get('maps', {}), last_event)
        elif state == 'SIDE_SELECTION':
            await self._sync_side_selection(draft.get('side', {}), last_event)
        elif state in ('CREATING', 'READY', 'IN_PROGRESS'):
            await self._sync_post_match(snapshot)

    def _update_team_and_captain(self, team_a_players: list, team_b_players: list):
        """Derive this bot's team/captain status from the snapshot."""
        self.is_captain = False
        self.my_team = None

        for player in team_a_players:
            if player.get('puuid') == self.bot_puuid:
                self.my_team = 'team_a'
                self.is_captain = player.get('is_captain', False)
                return

        for player in team_b_players:
            if player.get('puuid') == self.bot_puuid:
                self.my_team = 'team_b'
                self.is_captain = player.get('is_captain', False)
                return

    async def _drive_execution_state(self, snapshot: dict, execution: dict, total_players: int):
        """Hybrid simulation of the execution phase driven by the unified snapshot."""
        if not snapshot:
            return

        match_id = snapshot.get('match_id')
        if match_id:
            self.current_match_id = match_id

        exec_state = execution.get('state')
        pregame_id = execution.get('pregame_id')
        joined_players = execution.get('joined_players') or []
        constructor_puuid = execution.get('constructor')

        if constructor_puuid:
            self.is_constructor = constructor_puuid == self.bot_puuid

        if exec_state == 'IN_PROGRESS':
            self.game_started = True
            self.match_started_reported = True

        if pregame_id:
            self.pregame_id = pregame_id

        if self.bot_puuid in joined_players:
            self.joined_custom_game = True
            self.join_reported = True

        if self.is_constructor:
            if exec_state == 'CREATING' and not self.custom_game_created and not self._pending_creation_task:
                async def creation_wrapper():
                    try:
                        await self._simulate_custom_game_creation()
                    finally:
                        self._pending_creation_task = None

                self._pending_creation_task = asyncio.create_task(creation_wrapper())

            if self.simulated_pregame_id and pregame_id == self.simulated_pregame_id and not self.custom_game_acknowledged:
                logger.info(f"Bot {self.bot_alias} detected server acknowledgement for pregame {pregame_id}")
                self.custom_game_acknowledged = True

            all_joined = total_players > 0 and len(joined_players) >= total_players
            if all_joined:
                self.ready_to_start = True

            if (
                self.custom_game_acknowledged
                and all_joined
                and not self.match_started_reported
                and not self._pending_start_task
            ):
                async def start_wrapper():
                    try:
                        await self._simulate_match_start(execution, total_players)
                    finally:
                        self._pending_start_task = None

                self._pending_start_task = asyncio.create_task(start_wrapper())

        else:
            should_join = (
                exec_state == 'READY'
                and pregame_id
                and self.join_instruction_received
                and not self.join_reported
                and self.bot_puuid not in joined_players
                and not self._pending_join_task
            )
            if should_join:
                team = self.my_team or 'team_a'

                async def join_wrapper():
                    try:
                        await self._simulate_join_custom_game(pregame_id, team)
                    finally:
                        self._pending_join_task = None

                self._pending_join_task = asyncio.create_task(join_wrapper())


    async def _sync_server_veto(self, servers_info: dict, last_event: str):
        self.server_veto_turn = servers_info.get('turn')
        self.available_servers = servers_info.get('remaining') or servers_info.get('pool') or []
        self.vetoed_servers = servers_info.get('vetoed', [])
        self.server_veto_deadline = servers_info.get('deadline')
        history = servers_info.get('history', [])

        logger.info(
            f" Bot {self.bot_alias} server veto snapshot: turn={self.server_veto_turn}, "
            f"available={self.available_servers}, vetoed={self.vetoed_servers}"
        )

        if history:
            logger.info(f"   Server veto history (latest): {history[-1]}")

        state_key = (self.server_veto_turn, tuple(self.vetoed_servers))
        if self.is_captain and self.my_team and self.server_veto_turn == self.my_team:
            if self.last_processed_server_state != state_key:
                self.last_processed_server_state = state_key
                await self._handle_server_veto_action()
        else:
            self.last_processed_server_state = state_key

    async def _sync_map_veto(self, maps_info: dict, last_event: str):
        self.current_turn = maps_info.get('turn')
        self.available_maps = (
            maps_info.get('remaining')
            or maps_info.get('pool')
            or []
        )
        self.vetoed_maps = maps_info.get('vetoed', [])
        self.veto_deadline = maps_info.get('deadline')
        history = maps_info.get('history', [])

        logger.info(
            f" Bot {self.bot_alias} map veto snapshot: turn={self.current_turn}, "
            f"available={self.available_maps}, vetoed={self.vetoed_maps}"
        )

        if history:
            logger.info(f"   Map veto history (latest): {history[-1]}")

        state_key = (self.current_turn, tuple(self.vetoed_maps))
        if self.is_captain and self.my_team and self.current_turn == self.my_team:
            if self.last_processed_map_state != state_key:
                self.last_processed_map_state = state_key
                await self._make_map_veto_decision()
        else:
            self.last_processed_map_state = state_key

    async def _simulate_custom_game_creation(self):
        """Simulate the constructor creating a custom game lobby in Valorant."""
        if not self.current_match_id:
            logger.warning(f"Bot {self.bot_alias} has no match ID for custom game creation")
            return

        await asyncio.sleep(random.uniform(1.0, 2.5))

        self.simulated_pregame_id = f"pregame_{uuid.uuid4().hex[:8]}"
        self.pregame_id = self.simulated_pregame_id
        payload = {
            'match_id': self.current_match_id,
            'pregame_id': self.simulated_pregame_id,
            'constructor_puuid': self.bot_puuid,
        }

        logger.info(
            f"Bot {self.bot_alias} (constructor) reporting custom game creation: {self.simulated_pregame_id}"
        )
        await self._send_message('custom_game_created', payload)
        self.custom_game_created = True
        self.custom_game_acknowledged = False

    async def _simulate_join_custom_game(self, pregame_id: str, team: str):
        """Simulate a player joining the custom game lobby."""
        if not self.current_match_id:
            logger.warning(f"Bot {self.bot_alias} has no match ID when attempting to join custom game")
            return

        await asyncio.sleep(random.uniform(2.0, 5.0))

        logger.info(
            f"Bot {self.bot_alias} joining custom game {pregame_id[:8]}... as team {team}"
        )
        await self._send_message('player_joined_game', {
            'match_id': self.current_match_id,
            'player_puuid': self.bot_puuid,
            'team': team,
        })
        self.join_reported = True
        self.join_instruction_received = False

    async def _simulate_match_start(self, execution: dict, total_players: int):
        """Simulate the constructor starting the game once everyone has joined."""
        if not self.current_match_id:
            logger.warning(f"Bot {self.bot_alias} has no match ID when attempting to start the game")
            return

        if not await self._validate_custom_game_lobby(execution, total_players):
            logger.warning(f"Bot {self.bot_alias} validation failed; skipping match start simulation")
            return

        await asyncio.sleep(random.uniform(1.0, 2.5))

        simulated_coregame_id = f"coregame_{uuid.uuid4().hex[:8]}"
        logger.info(
            f"Bot {self.bot_alias} (constructor) starting simulated game with coregame {simulated_coregame_id}"
        )
        await self._send_message('match_started', {
            'match_id': self.current_match_id,
            'coregame_id': simulated_coregame_id,
        })
        self.match_started_reported = True
        self.game_started = True
        self.ready_to_start = False

    async def _validate_custom_game_lobby(self, execution: dict, total_players: int) -> bool:
        """
        Stubbed validation that would normally check Valorant lobby membership.
        Always returns True for automated tests.
        """
        joined_players = execution.get('joined_players') or []
        logger.info(
            f"Bot {self.bot_alias} validating custom game lobby (simulated): "
            f"{len(joined_players)}/{total_players} players joined"
        )
        await asyncio.sleep(random.uniform(0.2, 0.5))
        # In a full integration, the constructor would call valclient.pregame_fetch_match here.
        return True

    async def _sync_side_selection(self, side_info: dict, last_event: str):
        selector = side_info.get('selector')
        selected = side_info.get('selected')
        deadline = side_info.get('deadline')
        auto_side = side_info.get('auto_selected_side')

        self.side_selection_deadline = deadline
        self.side_selection_active = selected is None

        if auto_side:
            logger.info(f" Bot {self.bot_alias} noticed auto-selected side: {auto_side}")

        if selected:
            logger.info(f" Bot {self.bot_alias} side already selected: {selected}")
            self.side_selection_active = False
            self.side_selection_pending = False
            return

        if self.is_captain and selector == self.my_team and self.side_selection_active and not self.side_selection_pending:
            self.side_selection_pending = True
            await self._select_match_side()

    async def _sync_post_match(self, snapshot: dict):
        state = snapshot.get('state')
        constructor = snapshot.get('constructor_puuid')
        pregame_id = snapshot.get('pregame_id')

        if constructor == self.bot_puuid:
            self.is_constructor = True
            self.pregame_id = pregame_id
            logger.info(f" Bot {self.bot_alias} is constructor in state {state}, pregame_id={pregame_id}")
        else:
            self.is_constructor = False

        if state == 'READY':
            logger.info(f" Bot {self.bot_alias} match ready. Awaiting join instructions...")
    
    async def _send_message(self, event: str, payload: dict):
        """Send a message to the WebSocket"""
        if not self.connected or not self.websocket:
            logger.error(f" Bot {self.bot_alias} not connected, cannot send {event}")
            return
        
        message = json.dumps({
            "event": event,
            "payload": payload
        })
        
        try:
            await self.websocket.send(message)
            logger.debug(f"Bot {self.bot_alias} sent: {event}")
        except Exception as e:
            logger.error(f" Bot {self.bot_alias} failed to send {event}: {e}")
    
    async def create_lobby_and_queue(self):
        """Create lobby and join queue (simulating real user flow)"""
        try:
            # Step 1: Create lobby via WebSocket (like real users)
            await self._send_message('create_lobby', {
                'puuid': self.bot_puuid
            })
            
            # Wait a moment for lobby creation
            await asyncio.sleep(0.5)
            
            # Step 2: Get lobby ID from database (bots need to know their lobby)
            lobby = await self._get_bot_lobby()
            if not lobby:
                logger.error(f" Bot {self.bot_alias} failed to get lobby")
                return False
            
            self.lobby_id = str(lobby.id)
            logger.info(f" Bot {self.bot_alias} got lobby: {self.lobby_id}")
            
            # Step 3: Set lobby preferences
            # Generate assorted map preferences with 5 common maps
            common_maps = ['Ascent', 'Bind', 'Breeze', 'Fracture', 'Haven']
            all_maps = ['Ascent', 'Bind', 'Breeze', 'Fracture', 'Haven', 'Icebox', 'Lotus', 'Pearl', 'Split', 'Sunset']
            additional_maps = [map for map in all_maps if map not in common_maps]
            
            # Each bot gets the 5 common maps plus 2-4 random additional maps
            num_additional = random.randint(2, 4)
            selected_additional = random.sample(additional_maps, num_additional)
            map_preferences = common_maps + selected_additional
            
            await self._send_message('update_lobby_preferences', {
                'lobby_id': self.lobby_id,
                'requester_puuid': self.bot_puuid,
                'map_preferences': map_preferences,
                'server_preferences': ['Virginia', 'Illinois', 'Georgia', 'California', 'Dallas', 'Oregon']
            })
            
            # Wait a moment for preferences update
            await asyncio.sleep(0.5)
            
            # Step 4: Join queue via WebSocket (like real users)
            await self._send_message('add_lobby_to_queue', {
                'lobby_id': self.lobby_id,
                'requester_puuid': self.bot_puuid
            })
            
            logger.info(f" Bot {self.bot_alias} requested to join queue")
            return True
            
        except Exception as e:
            logger.error(f" Bot {self.bot_alias} failed to create lobby and queue: {e}")
            return False
    
    async def _get_bot_lobby(self):
        """Get the bot's lobby from database"""
        def get_lobby():
            try:
                player = Player.objects.get(puuid=self.bot_puuid)
                return Lobby.objects.filter(players=player, is_active=True).first()
            except Player.DoesNotExist:
                return None
        
        return await sync_to_async(get_lobby)()
    
    async def _handle_match_data(self, payload: dict):
        """Handle match data (veto phase initialization)"""
        logger.info(f" Bot {self.bot_alias} received match data (legacy event)")

        snapshot = {
            'state': payload.get('state'),
            'match_id': payload.get('match_id') or self.current_match_id,
            'team_a_players': payload.get('team_a_players', []),
            'team_b_players': payload.get('team_b_players', []),
            'draft': {
                'servers': {
                    'turn': payload.get('server_veto_turn'),
                    'remaining': payload.get('server_pool'),
                    'vetoed': payload.get('vetoed_servers'),
                    'deadline': payload.get('server_veto_deadline'),
                },
                'maps': {
                    'turn': payload.get('veto_turn'),
                    'remaining': payload.get('remaining_maps') or payload.get('map_pool'),
                    'vetoed': payload.get('vetoed_maps'),
                    'deadline': payload.get('veto_deadline'),
                    'history': payload.get('veto_history'),
                },
                'side': {
                    'selector': payload.get('side_selector'),
                    'selected': payload.get('selected_side'),
                    'deadline': payload.get('side_selection_deadline'),
                    'auto_selected_side': payload.get('auto_selected_side'),
                }
            },
            'meta': {
                'version': json.dumps({
                    'state': payload.get('state'),
                    'servers': payload.get('vetoed_servers'),
                    'maps': payload.get('vetoed_maps'),
                    'side': payload.get('selected_side')
                }, sort_keys=True)
            },
            'last_event': payload.get('last_event')
        }

        await self._handle_match_state_update(snapshot)
    
    async def _handle_veto_timeout(self, payload: dict):
        """Handle veto timeout (auto-veto occurred)"""
        auto_vetoed_map = payload.get('auto_vetoed_map')
        veto_complete = payload.get('veto_complete', False)
        next_turn = payload.get('next_turn')
        remaining_maps = payload.get('remaining_maps', [])
        final_map = payload.get('final_map')
        
        logger.info(f"Bot {self.bot_alias} received veto timeout")
        logger.info(f"   Auto-vetoed map: {auto_vetoed_map}")
        logger.info(f"   Veto complete: {veto_complete}")
        logger.info(f"   Next turn: {next_turn}")
        logger.info(f"   Remaining maps: {remaining_maps}")
        
        if veto_complete:
            # Veto phase is complete
            self.veto_complete = True
            logger.info(f"   Final map: {final_map}")
            # FIX: Don't reset captain/team info - preserve it for side selection
            # Reset only veto-specific state
            self.available_maps = []
            self.vetoed_maps = []
            self.current_turn = None
            self.veto_deadline = None
        else:
            # Continue veto phase - update state
            self.current_turn = next_turn
            self.available_maps = remaining_maps
            
            # If it's my turn and I'm captain, make a veto decision
            if self.is_captain and self.current_turn == self.my_team:
                logger.info(f"Bot {self.bot_alias} - IT'S MY TURN! Making veto decision...")
                await self._make_map_veto_decision()
            else:
                logger.info(f"   Not my turn (is_captain={self.is_captain}, current_turn={self.current_turn}, my_team={self.my_team})")
    
    async def _handle_map_vetoed(self, payload: dict):
        """Handle map vetoed event"""
        vetoed_map = payload.get('map') or payload.get('map_name')
        vetoed_by = payload.get('vetoed_by') or payload.get('team')
        next_turn = payload.get('next_turn')
        remaining_maps = payload.get('remaining_maps', [])
        
        logger.info(f"Bot {self.bot_alias} received map vetoed event")
        logger.info(f"   Vetoed map: {vetoed_map}")
        logger.info(f"   Vetoed by: {vetoed_by}")
        logger.info(f"   Next turn: {next_turn}")
        logger.info(f"   Remaining maps: {remaining_maps}")
        
        # Update state
        self.current_turn = next_turn
        self.available_maps = remaining_maps
        
        # If it's my turn and I'm captain, make a veto decision
        if self.is_captain and self.current_turn == self.my_team:
            logger.info(f"Bot {self.bot_alias} - IT'S MY TURN! Making veto decision...")
            await self._make_map_veto_decision()
        else:
            logger.info(f"   Not my turn (is_captain={self.is_captain}, current_turn={self.current_turn}, my_team={self.my_team})")
    
    async def _handle_veto_complete(self, payload: dict):
        """Handle veto phase completion"""
        self.veto_complete = True
        logger.info(f"Bot {self.bot_alias} veto phase completed!")
        logger.info(f"   Final map: {payload.get('final_map')}")
        
        self.available_maps = []
        self.vetoed_maps = []
        self.current_turn = None
        self.veto_deadline = None
    
    async def _handle_server_veto_started(self, payload: dict):
        """Handle server veto phase started"""
        match_id = payload.get('match_id')
        current_turn = payload.get('current_turn')
        available_servers = payload.get('available_servers', [])
        
        logger.info(f"Bot {self.bot_alias} server veto phase started")
        logger.info(f"Bot payload: {payload}")
        logger.info(f"   Match ID: {match_id[:8] if match_id else 'Unknown'}")
        logger.info(f"   Current turn: {current_turn}")
        logger.info(f"   Available servers: {available_servers}")
        
        # Update server veto state
        self.available_servers = available_servers
        self.server_veto_turn = current_turn
        
        # If it's my turn and I'm captain, make a server veto decision
        if self.is_captain and self.server_veto_turn == self.my_team:
            logger.info(f"Bot {self.bot_alias} - IT'S MY TURN! Making server veto decision...")
            await self._handle_server_veto_action()
        else:
            logger.info(f"   Not my turn (is_captain={self.is_captain}, current_turn={self.server_veto_turn}, my_team={self.my_team})")
    
    async def _handle_server_veto_update(self, payload: dict):
        """Handle server veto updates (server vetoed, turn changes)"""
        logger.info(f"Bot {self.bot_alias} received server veto update")
        
        # Update server veto state
        self.available_servers = payload.get('remaining_servers', [])
        self.server_veto_turn = payload.get('next_turn')
        
        # Add vetoed server to our list
        vetoed_server = payload.get('server_name')
        if vetoed_server and vetoed_server not in self.vetoed_servers:
            self.vetoed_servers.append(vetoed_server)
        
        logger.info(f"   Remaining servers: {self.available_servers}")
        logger.info(f"   Vetoed servers: {self.vetoed_servers}")
        logger.info(f"   Current turn: {self.server_veto_turn}")
        logger.info(f"   Is captain: {self.is_captain}, My team: {self.my_team}")
        
        # If it's my turn and I'm captain, make a server veto decision
        if self.is_captain and self.server_veto_turn == self.my_team:
            logger.info(f"Bot {self.bot_alias} - IT'S MY TURN! Making server veto decision...")
            await self._handle_server_veto_action()
        else:
            logger.info(f"   Not my turn (is_captain={self.is_captain}, current_turn={self.server_veto_turn}, my_team={self.my_team})")
    
    async def _handle_server_veto_complete(self, payload: dict):
        """Handle server veto phase completion and transition to map veto"""
        logger.info(f"Bot {self.bot_alias} server veto phase completed!")
        logger.info(f"   Final server: {payload.get('final_server')}")
        
        # Reset server veto state
        self.available_servers = []
        self.vetoed_servers = []
        self.server_veto_turn = None
        self.server_veto_deadline = None
        
        # Initialize map veto state from payload
        self.current_turn = payload.get('current_turn')
        self.available_maps = payload.get('available_maps', [])
        self.veto_deadline = payload.get('veto_deadline')
        self.vetoed_maps = []
        
        # FIX: PRESERVE captain/team info instead of re-initializing
        # The server_veto_complete payload doesn't contain team player data,
        # so we must preserve the existing captain/team information
        logger.info(f"[FIX] Preserving captain/team info:")
        logger.info(f"   Before: is_captain={self.is_captain}, my_team={self.my_team}")
        
        # Don't reset is_captain and my_team - keep the values from match_data
        # The original code was resetting these to False/None, which broke the flow
        
        logger.info(f"   After: is_captain={self.is_captain}, my_team={self.my_team}")
        
        logger.info(f"Bot {self.bot_alias} map veto phase starting!")
        logger.info(f"   Current turn: {self.current_turn}")
        logger.info(f"   Available maps: {self.available_maps}")
        logger.info(f"   Is captain: {self.is_captain}, My team: {self.my_team}")
        
        # If it's my turn and I'm captain, make a map veto decision
        if self.is_captain and self.current_turn == self.my_team:
            logger.info(f"Bot {self.bot_alias} - IT'S MY TURN! Making map veto decision...")
            await self._make_map_veto_decision()
        else:
            logger.info(f"   Not my turn (is_captain={self.is_captain}, current_turn={self.current_turn}, my_team={self.my_team})")
    
    async def _handle_server_veto_timeout(self, payload: dict):
        """Handle server veto timeout - a team took too long"""
        timed_out_team = payload.get('timed_out_team')
        auto_vetoed_server = payload.get('auto_vetoed_server')
        server_veto_complete = payload.get('server_veto_complete', False)
        
        logger.info(f"Bot {self.bot_alias} server veto TIMEOUT occurred!")
        logger.info(f"   Timed out team: {timed_out_team}")
        logger.info(f"   Auto-vetoed server: {auto_vetoed_server}")
        logger.info(f"   Server veto complete: {server_veto_complete}")
        
        if server_veto_complete:
            # Server veto phase is done, moving to map veto
            final_server = payload.get('final_server')
            logger.info(f"   Final server: {final_server}")
            
            # Reset server veto state
            self.available_servers = []
            self.vetoed_servers = []
            self.server_veto_turn = None
            self.server_veto_deadline = None
            
            # Initialize map veto state from payload
            self.current_turn = payload.get('current_turn')
            self.available_maps = payload.get('available_maps', [])
            self.veto_deadline = payload.get('veto_deadline')
            self.vetoed_maps = []
            
            # FIX: PRESERVE captain/team info instead of re-initializing
            # The server_veto_timeout payload doesn't contain team player data,
            # so we must preserve the existing captain/team information
            logger.info(f"[FIX] Preserving captain/team info (timeout):")
            logger.info(f"   Before: is_captain={self.is_captain}, my_team={self.my_team}")
            # Don't reset is_captain and my_team - keep the values from match_data
            logger.info(f"   After: is_captain={self.is_captain}, my_team={self.my_team}")
            
            logger.info(f"Bot {self.bot_alias} map veto phase starting (after server veto timeout)!")
            logger.info(f"   Current turn: {self.current_turn}")
            logger.info(f"   Available maps: {self.available_maps}")
            logger.info(f"   Is captain: {self.is_captain}, My team: {self.my_team}")
            
            # If it's my turn and I'm captain, make a map veto decision
            if self.is_captain and self.current_turn == self.my_team:
                logger.info(f"Bot {self.bot_alias} - IT'S MY TURN! Making map veto decision...")
                await self._make_map_veto_decision()
            else:
                logger.info(f"   Not my turn (is_captain={self.is_captain}, current_turn={self.current_turn}, my_team={self.my_team})")
        else:
            # Update state for next turn
            self.available_servers = payload.get('remaining_servers', [])
            self.server_veto_turn = payload.get('next_turn')
            self.server_veto_deadline = payload.get('deadline')
            
            if auto_vetoed_server and auto_vetoed_server not in self.vetoed_servers:
                self.vetoed_servers.append(auto_vetoed_server)
            
            # If it's now my turn after timeout, make a veto
            if self.is_captain and self.server_veto_turn == self.my_team:
                logger.info(f"   It's now my turn after timeout, making server veto decision...")
                await self._handle_server_veto_action()
    
    async def _handle_map_veto_started(self, payload: dict):
        """Handle map veto phase started"""
        logger.info(f"Bot {self.bot_alias} map veto phase started!")
        
        match_id = payload.get('match_id')
        current_turn = payload.get('current_turn')
        available_maps = payload.get('available_maps', [])
        
        logger.info(f"   Match ID: {match_id}")
        logger.info(f"   Current turn: {current_turn}")
        logger.info(f"   Available maps: {available_maps}")
        
        # Update map veto state
        self.available_maps = available_maps
        self.veto_turn = current_turn
        
        # If it's my turn and I'm captain, make a map veto decision
        if self.is_captain and self.veto_turn == self.my_team:
            logger.info(f"Bot {self.bot_alias} - IT'S MY TURN! Making map veto decision...")
            await self._make_map_veto_decision()
        else:
            logger.info(f"   Not my turn (is_captain={self.is_captain}, current_turn={self.veto_turn}, my_team={self.my_team})")
    
    async def _handle_server_vetoed(self, payload: dict):
        """Handle server vetoed event"""
        vetoed_server = payload.get('server_name')
        vetoed_by = payload.get('vetoed_by')
        next_turn = payload.get('next_turn')
        remaining_servers = payload.get('remaining_servers', [])
        
        logger.info(f"Bot {self.bot_alias} received server vetoed event")
        logger.info(f"   Vetoed server: {vetoed_server}")
        logger.info(f"   Vetoed by: {vetoed_by}")
        logger.info(f"   Next turn: {next_turn}")
        logger.info(f"   Remaining servers: {remaining_servers}")
        
        # Update state
        self.available_servers = remaining_servers
        self.server_veto_turn = next_turn
        
        # Add to vetoed servers list
        if vetoed_server and vetoed_server not in self.vetoed_servers:
            self.vetoed_servers.append(vetoed_server)
        
        # If it's my turn and I'm captain, make a server veto decision
        if self.is_captain and self.server_veto_turn == self.my_team:
            logger.info(f"Bot {self.bot_alias} - IT'S MY TURN! Making server veto decision...")
            await self._handle_server_veto_action()
        else:
            logger.info(f"   Not my turn (is_captain={self.is_captain}, current_turn={self.server_veto_turn}, my_team={self.my_team})")
    
    async def _handle_match_timeout(self, payload: dict):
        """Handle match timeout"""
        match_id = payload.get('match_id')
        timeout_type = payload.get('timeout_type', 'unknown')
        reason = payload.get('reason', 'Match timed out')
        
        logger.info(f"Bot {self.bot_alias} received match timeout")
        logger.info(f"   Match ID: {match_id[:8] if match_id else 'Unknown'}")
        logger.info(f"   Timeout type: {timeout_type}")
        logger.info(f"   Reason: {reason}")
        
        self._reset_match_flow_state()

        # Reset all match-related state
        self.current_match_id = None
        self.veto_complete = False
        self.is_captain = False
        self.my_team = None
        self.available_maps = []
        self.vetoed_maps = []
        self.current_turn = None
        self.veto_deadline = None
        self.is_constructor = False
        self.pregame_id = None
        self.game_started = False
        self.joined_custom_game = False
    
    async def _make_map_veto_decision(self):
        """Make a veto decision when it's the bot's turn"""
        if not self.available_maps:
            logger.warning(f"Bot {self.bot_alias} no maps available to veto!")
            return
        
        # Choose veto strategy based on bot personality
        if self.veto_strategy == 'aggressive':
            map_to_veto = self._aggressive_veto()
        elif self.veto_strategy == 'strategic':
            map_to_veto = self._strategic_veto()
        else:  # random
            map_to_veto = self._random_veto()
        
        logger.info(f"Bot {self.bot_alias} vetoing map: {map_to_veto} (strategy: {self.veto_strategy})")
        
        # Add some realistic delay (1-3 seconds)
        delay = random.uniform(1.0, 3.0)
        await asyncio.sleep(delay)
        
        # Send veto action (server accepts both 'map' and 'map_name')
        await self._send_message('veto_map', {
            'match_id': self.current_match_id,
            'map_name': map_to_veto
        })
    
    async def _handle_server_veto_action(self):
        """Make a server veto decision when it's the bot's turn"""
        if not self.available_servers:
            logger.warning(f"Bot {self.bot_alias} no servers available to veto!")
            return
        
        # Choose server to veto (random for now, could add strategy later)
        server_to_veto = random.choice(self.available_servers)
        
        logger.info(f"Bot {self.bot_alias} vetoing server: {server_to_veto}")
        
        # Add some realistic delay (1-3 seconds)
        delay = random.uniform(1.0, 3.0)
        await asyncio.sleep(delay)
        
        # Send server veto action
        await self._send_message('veto_server', {
            'match_id': self.current_match_id,
            'server_name': server_to_veto
        })
    
    def _random_veto(self) -> str:
        """Randomly select a map to veto"""
        return random.choice(self.available_maps)
    
    def _aggressive_veto(self) -> str:
        """Always veto the most popular/strongest maps"""
        priority_maps = ['Haven', 'Bind', 'Ascent', 'Split', 'Icebox', 'Breeze', 'Fracture', 'Lotus', 'Pearl']
        
        for map_name in priority_maps:
            if map_name in self.available_maps:
                return map_name
        
        return random.choice(self.available_maps)
    
    def _strategic_veto(self) -> str:
        """Strategic veto based on team preferences (placeholder for now)"""
        # For now, just use aggressive strategy
        # Could implement more sophisticated logic here
        return self._aggressive_veto()
    
    async def _handle_construction_started(self, payload: dict):
        """Handle constructor assignment event."""
        self._reset_match_flow_state()

        self.is_constructor = payload.get('is_constructor', False)
        self.current_match_id = payload.get('match_id')
        self.side_selection_active = False
        self.side_selection_pending = False
        self.side_selection_deadline = None
        
        if self.is_constructor:
            logger.info(f"Bot {self.bot_alias} is CONSTRUCTOR for match {self.current_match_id[:8] if self.current_match_id else 'Unknown'}")
            logger.info(f"   Map: {payload.get('map')}")
            logger.info(f"   Server: {payload.get('server')}")
            logger.info(f"   Team: {payload.get('team')}")
        else:
            logger.info(f"Bot {self.bot_alias} is regular player for match {self.current_match_id[:8] if self.current_match_id else 'Unknown'}")
            logger.info(f"   Team: {payload.get('team')}")
    
    async def _handle_join_custom_game(self, payload: dict):
        """Handle join custom game instruction"""
        match_id = payload.get('match_id')
        pregame_id = payload.get('pregame_id')
        team = payload.get('team')
        
        logger.info(f"Bot {self.bot_alias} instructed to join custom game")
        logger.info(f"   Match: {match_id[:8] if match_id else 'Unknown'}")
        logger.info(f"   Pregame: {pregame_id[:8] if pregame_id else 'Unknown'}")
        logger.info(f"   Team: {team}")
        
        self.join_instruction_received = True
        if pregame_id:
            self.pregame_id = pregame_id

        logger.info(
            f"Bot {self.bot_alias} queued to join custom game on next READY snapshot."
        )
    
    async def _handle_all_players_joined(self, payload: dict):
        """Handle all players joined event (constructor can start game)"""
        match_id = payload.get('match_id')
        is_constructor = payload.get('is_constructor', False)
        
        if is_constructor and self.is_constructor:
            logger.info(
                f"Bot {self.bot_alias} (CONSTRUCTOR) - All players joined! Awaiting snapshot validation before starting game."
            )
            self.ready_to_start = True
        else:
            logger.info(f"Bot {self.bot_alias} - All players joined, waiting for constructor to start game...")
    
    async def _handle_match_cancelled(self, payload: dict):
        """Handle match cancellation"""
        match_id = payload.get('match_id')
        reason = payload.get('reason', 'unknown')
        
        logger.warning(f"Bot {self.bot_alias} match cancelled: {reason}")
        logger.warning(f"   Match: {match_id[:8] if match_id else 'Unknown'}")
        
        self._reset_match_flow_state()

        # Reset state
        self.is_constructor = False
        self.pregame_id = None
        self.game_started = False
        self.joined_custom_game = False
        self.current_match_id = None
        self.side_selection_active = False
        self.side_selection_pending = False
        self.side_selection_deadline = None
    
    async def _handle_joined_custom_game(self, payload: dict):
        """Handle successful join confirmation"""
        match_id = payload.get('match_id')
        team = payload.get('team')
        
        logger.info(f"Bot {self.bot_alias} confirmed joined custom game")
        logger.info(f"   Match: {match_id[:8] if match_id else 'Unknown'}")
        logger.info(f"   Team: {team}")
    
    async def _handle_join_custom_game_failed(self, payload: dict):
        """Handle join failure"""
        match_id = payload.get('match_id')
        team = payload.get('team')
        error = payload.get('error', 'Unknown error')
        
        logger.error(f"Bot {self.bot_alias} failed to join custom game: {error}")
        logger.error(f"   Match: {match_id[:8] if match_id else 'Unknown'}")
        logger.error(f"   Team: {team}")

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info(f" Bot {self.bot_alias} disconnected")


async def create_bot_with_websocket(bot_num: int, base_elo: int, base_mmr: int, region: str) -> Optional[BotWebSocketClient]:
    """
    Create a bot player with proper UUID and WebSocket connection.
    This simulates a real user joining the system.
    """
    # Generate proper UUID (like real users)
    bot_puuid = str(uuid.uuid4())
    bot_alias = f"QueueBot{bot_num}"
    
    # Create bot player in database
    def create_bot():
        # Calculate bot's specific ELO and MMR
        bot_elo = base_elo + random.randint(-50, 50)
        bot_mmr = base_mmr + random.randint(-50, 50)
        bot_mu = mmr_to_trueskill_mu(bot_mmr)
        games_played = random.randint(120, 400)
        wins = random.randint(int(games_played * 0.45), int(games_played * 0.65))
        losses = max(games_played - wins, 0)
        frags = random.randint(15, 24) * games_played
        deaths = max(int(frags / random.uniform(1.2, 1.6)), 1)
        assists = random.randint(4, 10) * games_played
        
        bot, created = Player.objects.get_or_create(
            puuid=bot_puuid,
            defaults={
                'username': bot_alias,
                'alias': bot_alias,
                'region': region,
                'elo': bot_elo,
                'mmr': bot_mmr,
                'trueskill_mu': bot_mu,
                'trueskill_sigma': 9.0,
                'rank': 'S',
                'team': 'none',
                'games_played': games_played,
                'wins': wins,
                'loss': losses,
                'frags': frags,
                'deaths': deaths,
                'assists': assists,
            }
        )
        
        # Update if existed
        if not created:
            bot.elo = bot_elo
            bot.mmr = bot_mmr
            bot.trueskill_mu = bot_mu
            bot.trueskill_sigma = 9.0
            bot.games_played = games_played
            bot.wins = wins
            bot.loss = losses
            bot.frags = frags
            bot.deaths = deaths
            bot.assists = assists
            bot.save()
        
        return bot
    
    bot_player = await sync_to_async(create_bot)()
    logger.info(f"Created bot player: {bot_alias} (PUUID: {bot_puuid[:8]}...)")
    
    # Create WebSocket client
    bot_client = BotWebSocketClient(bot_puuid, bot_alias)
    
    try:
        # Connect to WebSocket consumer
        await bot_client.connect()
        
        # Create lobby and join queue (like real users)
        success = await bot_client.create_lobby_and_queue()
        
        if success:
            logger.info(f" Bot {bot_alias} successfully set up and queued")
            return bot_client
        else:
            logger.error(f" Bot {bot_alias} failed to queue")
            await bot_client.disconnect()
            return None
            
    except Exception as e:
        logger.error(f" Bot {bot_alias} setup failed: {e}")
        await bot_client.disconnect()
        return None


async def get_your_player_info():
    """Get your player info from database"""
    print("\n[1/3] Finding your player account...")
    
    def find_player():
        # Look for your specific player first (evisc#erate)
        you = Player.objects.filter(username__icontains='evisc').first()
        if you:
            return you
        # If not found, find any non-bot, non-sim, non-test players
        you = Player.objects.exclude(
            username__icontains='bot'
        ).exclude(
            username__icontains='sim'
        ).exclude(
            username__icontains='test'
        ).exclude(
            alias__icontains='bot'
        ).exclude(
            alias__icontains='sim'
        ).exclude(
            alias__icontains='test'
        ).first()
        
        return you
    
    you = await sync_to_async(find_player)()
    
    if you:
        print(f"    Found your player: {you.alias} (ELO: {you.elo})")
        return you
    else:
        print("    Could not find your player account!")
        print("    Make sure you've logged in at least once to create your player profile")
        return None


async def wait_for_match_or_timeout(bot_clients: List[BotWebSocketClient], timeout_seconds: int = 120):
    """Wait for match to be found or timeout"""
    print(f"\n[3/3] Waiting for match (timeout: {timeout_seconds}s)...")
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        
        if elapsed >= timeout_seconds:
            print(f"   Timeout reached ({timeout_seconds}s)")
            return False
        
        # Check if any bot found a match
        for bot in bot_clients:
            if bot.match_found:
                print(f"    Match found! Bot {bot.bot_alias} detected match")
                return True
        
        # Show progress every 10 seconds
        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
            remaining = timeout_seconds - int(elapsed)
            print(f"   Still waiting... ({remaining}s remaining)")
        
        await asyncio.sleep(1)


async def wait_for_veto_completion(bot_clients: List[BotWebSocketClient], timeout_seconds: int = 300):
    """Wait for veto phase to complete across all bots"""
    print(f"\n[4/4] Waiting for veto phase completion (timeout: {timeout_seconds}s)...")
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        
        if elapsed >= timeout_seconds:
            print(f"   Veto timeout reached ({timeout_seconds}s)")
            return False
        
        # Check if veto is complete (at least one bot should have veto_complete)
        veto_complete_count = sum(1 for bot in bot_clients if bot.veto_complete)
        
        if veto_complete_count > 0:
            print(f"    Veto phase completed! ({veto_complete_count} bots confirmed)")
            return True
        
        # Show progress every 5 seconds
        if int(elapsed) % 5 == 0 and int(elapsed) > 0:
            remaining = timeout_seconds - int(elapsed)
            confirmed = sum(1 for bot in bot_clients if bot.match_confirmed)
            print(f"   Waiting for veto... {confirmed}/{len(bot_clients)} bots confirmed match ({remaining}s remaining)")
        
        await asyncio.sleep(1)


async def wait_for_game_constructor_completion(bot_clients: List[BotWebSocketClient], timeout_seconds: int = 180):
    """Wait for game constructor phase to complete (all players join and game starts)"""
    print(f"\n[5/5] Waiting for game constructor phase completion (timeout: {timeout_seconds}s)...")
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        
        if elapsed >= timeout_seconds:
            print(f"   Game constructor timeout reached ({timeout_seconds}s)")
            return False
        
        # Check if game started (constructor bot should have game_started = True)
        constructor_bot = next((bot for bot in bot_clients if bot.is_constructor), None)
        if constructor_bot and constructor_bot.game_started:
            print(f"    Game started successfully by constructor {constructor_bot.bot_alias}!")
            return True
        
        # Check if match was cancelled
        cancelled_bots = sum(1 for bot in bot_clients if not bot.current_match_id and bot.match_confirmed)
        if cancelled_bots > 0:
            print(f"    Match was cancelled ({cancelled_bots} bots show cancelled state)")
            return False
        
        # Show progress every 10 seconds
        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
            remaining = timeout_seconds - int(elapsed)
            joined_count = sum(1 for bot in bot_clients if bot.joined_custom_game)
            constructor_count = sum(1 for bot in bot_clients if bot.is_constructor)
            print(f"   Waiting for game start... {joined_count}/{len(bot_clients)} bots joined,{constructor_count} constructor(s) ({remaining}s remaining)")
        await asyncio.sleep(1)


async def cleanup_bots(bot_clients: List[BotWebSocketClient]):
    """Clean up bot WebSocket connections"""
    print("\nCleaning up bot connections...")
    
    for bot in bot_clients:
        try:
            await bot.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting bot {bot.bot_alias}: {e}")
    
    print("    All bot connections closed")


async def main():
    """Main test function"""
    print("=" * 80)
    print(" QUEUE TEST WITH BOTS V5 - Complete Game Flow Simulation")
    print("=" * 80)
    print("This version tests the complete game flow including:")
    print("- Match acceptance and veto functionality")
    print("- Game constructor logic and join tracking")
    print("- Custom game lobby simulation")
    print("- End-to-end game flow testing")
    print("=" * 80)
    
    # Configuration
    NUM_BOTS = 9
    BASE_ELO = 6200
    BASE_MMR = 6000
    REGION = 'na'
    
    bot_clients = []
    
    try:
        # Step 1: Verify your player exists
        your_player = await get_your_player_info()
        if not your_player:
            print("\n Cannot proceed without your player account")
            return
        
        # Step 2: Create bots with WebSocket connections
        print(f"\n[2/3] Creating {NUM_BOTS} bots with WebSocket connections...")
        print(f"    Base ELO: {BASE_ELO} (±50 variation)")
        print(f"    Base MMR: {BASE_MMR} (±50 variation)")
        
        for i in range(NUM_BOTS):
            print(f"    Creating bot {i+1}/{NUM_BOTS}...")
            
            bot_client = await create_bot_with_websocket(i, BASE_ELO, BASE_MMR, REGION)
            
            if bot_client:
                bot_clients.append(bot_client)
                print(f"    Bot {i+1} ready")
            else:
                print(f"    Bot {i+1} failed")
            
            # Small delay between bot creation
            await asyncio.sleep(0.5)
        
        successful_bots = len(bot_clients)
        print(f"\n    Successfully created {successful_bots}/{NUM_BOTS} bots")
        
        if successful_bots == 0:
            print("    No bots were created successfully")
            return
        
        # Step 3: Wait for match or timeout
        print(f"\n    {successful_bots} bots are now in queue")
        print("    Now join queue with your client to trigger matchmaking!")
        print("    The bots will auto-accept when a match is found")
        
        match_found = await wait_for_match_or_timeout(bot_clients, timeout_seconds=300)
        
        if match_found:
            print("\nSUCCESS! Match was found and bots auto-accepted")
            print("    Check your client - you should see the match confirmation")
            print("    Accept the match to proceed to veto phase")
            
            # Wait for veto phase to complete (with extended timeout)
            print("\n   Waiting for veto phase to complete...")
            veto_completed = await wait_for_veto_completion(bot_clients, timeout_seconds=300)
            
            if veto_completed:
                print("\n    Veto phase completed successfully!")
                
                # Wait for game constructor phase to complete
                print("\n   Waiting for game constructor phase to complete...")
                game_started = await wait_for_game_constructor_completion(bot_clients, timeout_seconds=180)
                
                if game_started:
                    print("\n    Game constructor phase completed successfully!")
                    print("    All bots successfully joined and game started!")
                else:
                    print("\n     Game constructor phase did not complete within timeout")
                    print("    Check server logs for join tracking issues")
                
                print("    Bots will disconnect in 10 seconds...")
                await asyncio.sleep(10)
            else:
                print("\n     Veto phase did not complete within timeout")
                print("    Check Celery worker logs for auto-veto activity")
                print("    Bots will disconnect in 10 seconds...")
                await asyncio.sleep(10)
            
        else:
            print("\nNo match found within timeout period")
            print("    Make sure you join queue with your client")
            print("    Check that Celery worker is running for matchmaking")
    
    except KeyboardInterrupt:
        print("\n\n  Test interrupted by user")
    
    except Exception as e:
        print(f"\n Test failed with error: {e}")
        logger.exception("Test error details:")
    
    finally:
        # Always cleanup
        await cleanup_bots(bot_clients)
        
        print("\n" + "=" * 80)
        print("Test completed!")
        print("=" * 80)
        print(" Use cleanup_bots_simple.py to clean up database entries")
        print(" Restart Daphne if you see connection issues")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())