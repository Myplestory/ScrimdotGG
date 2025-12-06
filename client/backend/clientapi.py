import requests, os, json, time, asyncio, random
from valclient import Client
from datetime import datetime
from quart import current_app
from pugapi import PugSocketClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


folder_name = 'data'
file_name = 'data.json'
file_path = os.path.join(os.path.dirname(__file__), folder_name, file_name)

class ValorantAPI(object):
    def __init__(self):
        from app.settings import DJANGO_WS_URL, DJANGO_API_URL
        self.client = None
        self.args = None
        self.pugsocket = None
        self.django_api_url = DJANGO_API_URL.rstrip('/')
        self.pugsocket_url = DJANGO_WS_URL.rstrip('/')
        self.session_id = None
        self.puuid = None
        self.latest_match_state = None
        
        # Pregame ID validation tracking
        self.expected_pregame_id = None  # Pregame ID expected from match_state_update snapshot
        self.sent_pregame_id = None  # Pregame ID sent by constructor (if this client is constructor)
        self.is_constructor = False  # Track if this client is the constructor
        self.current_match_id = None  # Track current match ID for validation context
        self.pregame_id_validation_errors = []  # Track validation failures (for debugging/monitoring)
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.args = data
        except Exception as e:
            logger.error(f"An error occurred while reading the JSON file: {e}")
    
    ### LOGIN ###
    async def login(self, region):
        try:
            if not self.client:
                self.client = Client(region=region)
                self.client.activate()
                print("Client activated.")
                    
            if self.client.puuid:
                jsonargs = {
                    'puuid': self.client.puuid,
                    'region': region,
                    'username': f'{self.client.player_name}#{self.client.player_tag}',
                    'alias': f'{self.client.player_name}#{self.client.player_tag}',
                }
                url = f'{self.django_api_url}/login/login/'
                try:
                    response = requests.post(url, json=jsonargs)
                    if response.status_code == 200:
                        # Build WebSocket URL from base URL + puuid
                        base_ws_url = self.pugsocket_url.rstrip('/')
                        self.pugsocket_url = f"{base_ws_url}/{self.client.puuid}/"
                        data = response.json()
                        self.session_id = data.get('sessionid')
                        print(f"Client successfully activated for: {self.client.puuid}")
                        connection_status = await self.start_websocket_connection()
                        if connection_status["status"] == "success":
                            return {
                                "status": "success",
                                "message": f"Client successfully activated and WebSocket connected for: {self.client.puuid}"
                            }
                        else:
                            return {
                                "status": "failed",
                                "details": connection_status["message"]
                            }
                    else:
                        print(f"Login request failed with status code: {response.status_code}")
                        return {
                            "error": "Request failed",
                            "status_code": response.status_code
                        }
                except Exception as e:
                    print(f"Exception during login request: {e}")
                    return {"error": str(e)}
            else:
                print("Client activation failed.")
                return {"status": "error", "message": "Client activation failed"}
        except Exception as e:
            print(f"Exception during login: {e}")
            return {"status": "error", "message": str(e)}
          
    ### WEBSOCKET INIT ###
    async def start_websocket_connection(self, max_retries=3, backoff=2):
        if not self.pugsocket:
            self.pugsocket = PugSocketClient()
        for attempt in range(1, max_retries + 1):
            print(f"Attempting WebSocket connection [Attempt {attempt}/{max_retries}] to {self.pugsocket_url}")
            connection_status = await self.pugsocket.start_connection(self.pugsocket_url)
            if connection_status["status"] == "success":
                    print("WebSocket connection established.")
                    
                    # Store reference to self for callback closure
                    api_instance = self
                    
                    # Set up the match_found callback to forward to main WebSocket
                    async def match_found_callback(data):
                        """Forward match_found event to main WebSocket connection"""
                        try:
                            print(f"[MATCH_FOUND_CALLBACK] Received match_found event: {data}")
                            
                            # Get the match data and store it temporarily
                            api_instance._pending_match_data = data
                            
                            print(f"[MATCH_FOUND_CALLBACK] Stored pending match data, will be picked up by main loop")
                        except Exception as e:
                            print(f"[MATCH_FOUND_CALLBACK] Error storing match_found: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Set up the match_proposed callback to forward to main WebSocket
                    async def match_proposed_callback(data):
                        """Forward match_proposed event to main WebSocket connection"""
                        try:
                            print(f"[MATCH_PROPOSED_CALLBACK] Received match_proposed event: {data}")
                            
                            # Store the match proposed data temporarily
                            api_instance._pending_match_proposed_data = data
                            
                            print(f"[MATCH_PROPOSED_CALLBACK] Stored pending match proposed data, will be picked up by main loop")
                        except Exception as e:
                            print(f"[MATCH_PROPOSED_CALLBACK] Error storing match_proposed: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Set up the player_accepted callback to forward to main WebSocket
                    async def player_accepted_callback(data):
                        """Forward player_accepted event to main WebSocket connection"""
                        try:
                            print(f"[PLAYER_ACCEPTED_CALLBACK] Received player_accepted event: {data}")
                            
                            # Store the player accepted data temporarily
                            api_instance._pending_player_accepted_data = data
                            
                            print(f"[PLAYER_ACCEPTED_CALLBACK] Stored pending player accepted data, will be picked up by main loop")
                        except Exception as e:
                            print(f"[PLAYER_ACCEPTED_CALLBACK] Error storing player_accepted: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Set up the match_ready callback to forward to main WebSocket
                    async def match_ready_callback(data):
                        """Forward match_ready event to main WebSocket connection"""
                        try:
                            print(f"[MATCH_READY_CALLBACK] Received match_ready event: {data}")
                            
                            # Store the match ready data temporarily
                            api_instance._pending_match_ready_data = data
                            
                            print(f"[MATCH_READY_CALLBACK] Stored pending match ready data, will be picked up by main loop")
                        except Exception as e:
                            print(f"[MATCH_READY_CALLBACK] Error storing match_ready: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Set up the match_confirmed callback to forward to main WebSocket
                    async def match_confirmed_callback(data):
                        """Forward match_confirmed event to main WebSocket connection"""
                        try:
                            print(f"[MATCH_CONFIRMED_CALLBACK] Received match_confirmed event: {data}")
                            
                            # Store the match confirmed data temporarily
                            api_instance._pending_match_confirmed_data = data
                            
                            print(f"[MATCH_CONFIRMED_CALLBACK] Stored pending match confirmed data, will be picked up by main loop")
                        except Exception as e:
                            print(f"[MATCH_CONFIRMED_CALLBACK] Error storing match_confirmed: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Set up the match_data callback to forward to main WebSocket
                    async def match_data_callback(data):
                        """Forward match_data event to main WebSocket connection"""
                        try:
                            print(f"[MATCH_DATA_CALLBACK] Received match_data event: {data}")
                            
                            # Store the match data response temporarily
                            api_instance._pending_match_data_response = data
                            
                            print(f"[MATCH_DATA_CALLBACK] Stored pending match data response, will be picked up by main loop")
                        except Exception as e:
                            print(f"[MATCH_DATA_CALLBACK] Error storing match_data: {e}")
                            import traceback
                            traceback.print_exc()

                    # Set up the match_state_update callback to forward to main WebSocket
                    async def match_state_update_callback(data):
                        """Forward match_state_update snapshots to all frontend clients (IMMEDIATE)"""
                        try:
                            self.latest_match_state = data
                            
                            # Extract and validate pregame_id from snapshot
                            self._update_pregame_id_from_snapshot(data)
                            
                            from quart import current_app
                            await current_app.conn_mgr.broadcast('match_state_update', data)
                            print(f"[MATCH_STATE_UPDATE_CALLBACK] Broadcasted match_state_update for match {data.get('match_id')}")
                        except Exception as e:
                            print(f"[MATCH_STATE_UPDATE_CALLBACK] Error broadcasting match_state_update: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    self.pugsocket.match_found_callback = match_found_callback
                    self.pugsocket.match_proposed_callback = match_proposed_callback
                    self.pugsocket.player_accepted_callback = player_accepted_callback
                    self.pugsocket.match_ready_callback = match_ready_callback
                    self.pugsocket.match_confirmed_callback = match_confirmed_callback
                    self.pugsocket.match_data_callback = match_data_callback
                    self.pugsocket.match_state_update_callback = match_state_update_callback
                    self.match_state_update_callback = match_state_update_callback

                    async def match_construction_started_callback(data):
                        from quart import current_app
                        
                        print(f"[MATCH_CONSTRUCTION_STARTED_CALLBACK] Received event: {data}")
                        self.latest_match_state = data
                        await current_app.conn_mgr.broadcast('match_construction_started', data)
                        print(f"[MATCH_CONSTRUCTION_STARTED_CALLBACK] Broadcasted to frontend")
                        
                        # Handle constructor game creation via service
                        is_constructor = data.get('is_constructor', False)
                        if is_constructor:
                            valorant_service = current_app.valorant
                            match_id = data.get('match_id')
                            map_name = data.get('map')
                            server = data.get('server')
                            team = data.get('team')
                            await valorant_service.create_custom_game(match_id, map_name, server, team)

                    async def join_custom_game_callback(data):
                        from quart import current_app
                        await current_app.conn_mgr.broadcast('join_custom_game', data)

                    async def player_joined_game_callback(data):
                        from quart import current_app
                        await current_app.conn_mgr.broadcast('player_joined_game', data)

                    async def player_join_failed_callback(data):
                        from quart import current_app
                        await current_app.conn_mgr.broadcast('player_join_failed', data)

                    async def all_players_joined_callback(data):
                        from quart import current_app
                        
                        # Broadcast to frontend
                        await current_app.conn_mgr.broadcast('all_players_joined', data)
                        
                        # Handle constructor game start via service
                        is_constructor = data.get('is_constructor', False)
                        if is_constructor:
                            valorant_service = current_app.valorant
                            match_id = data.get('match_id')
                            await valorant_service.start_custom_game(match_id)

                    async def match_in_progress_callback(data):
                        from quart import current_app
                        await current_app.conn_mgr.broadcast('match_in_progress', data)

                    async def match_completed_callback(data):
                        from quart import current_app
                        await current_app.conn_mgr.broadcast('match_completed', data)

                    self.pugsocket.match_construction_started_callback = match_construction_started_callback
                    self.pugsocket.join_custom_game_callback = join_custom_game_callback
                    self.pugsocket.player_joined_game_callback = player_joined_game_callback
                    self.pugsocket.player_join_failed_callback = player_join_failed_callback
                    self.pugsocket.all_players_joined_callback = all_players_joined_callback
                    self.pugsocket.match_in_progress_callback = match_in_progress_callback
                    self.pugsocket.match_completed_callback = match_completed_callback
                    self._pending_match_data = None
                    self._pending_match_proposed_data = None
                    self._pending_player_accepted_data = None
                    self._pending_match_ready_data = None
                    self._pending_match_confirmed_data = None
                    self._pending_match_data_response = None
                    
                    await asyncio.sleep(1)
                    return connection_status
            print(f"Connection failed: {connection_status.get('message', 'No message provided')}")
            if attempt < max_retries:
                sleep_time = backoff * attempt
                print(f"Waiting {sleep_time} seconds before next attempt...")
                await asyncio.sleep(sleep_time)
        print(f"Failed to connect after {max_retries} attempts.")
        return {
            "status": "failure",
            "message": f"Could not establish WebSocket after {max_retries} tries"
        }
        
    ### INFO ###
        
    async def get_player_model(self):
        if not self.pugsocket or not self.pugsocket.is_connected():
            print("WebSocket is not connected. Cannot fetch player model.")
            return {"error": "WebSocket is not connected"}
        self.pugsocket.player_data_event.clear()
        print(f"Emitting player_model for {self.client.puuid}")
        message = {
            "puuid": self.client.puuid
        }
        try:
            await self.pugsocket.send_message("get_player_model", message)
            print("Sent 'get_player_model' message.")
            timeout = 5
            try:
                await asyncio.wait_for(self.pugsocket.player_data_event.wait(), timeout=timeout)
                print("Player data event received.")
                return {
                    "status": "success",
                    "message": f"Player model successfully retrieved for: {self.client.puuid}",
                    "data": self.pugsocket.player_data,
                    "puuid": self.client.puuid,
                }
            except asyncio.TimeoutError:
                print("Player model retrieval timed out.")
                return {"error": "Player model retrieval timed out"}
        except Exception as e:
            print(f"Error sending 'get_player_model' message: {e}")
            return {"error": f"Error sending 'get_player_model' message: {str(e)}"}
        
    ### CHAT ###
    
    async def send_lobby_message(self, payload):
        """
        Sends a chat message to the lobby.
        """
        message = payload.get("message")
        user_alias = payload.get("userAlias")
        lobby_id = payload.get("lobby_id")
        timestamp = payload.get("timestamp", datetime.now().isoformat())
        if not message or not user_alias or not lobby_id:
            raise ValueError("Message, user alias, and lobby ID are required.")
        if not self.pugsocket or not self.pugsocket.is_connected():
            raise ValueError("WebSocket is not connected.")
        try:
            ws_payload = {
                "event": "lobby_message",
                "payload": {
                    "message": message,
                    "lobby_id": lobby_id,
                    "userAlias": user_alias,
                    "timestamp": timestamp
                }
            }
            await self.pugsocket.send_lobby_message(ws_payload)
            return {"status": "success", "message": "Lobby message sent successfully"}
        except Exception as e:
            print(f"Error sending lobby message: {e}")
            raise e



    async def send_direct_message(self, payload):
        """
        Sends a direct message to a specific player.
        """
        if not self.pugsocket or not self.pugsocket.is_connected():
            raise ValueError("WebSocket is not connected.")
        message = payload.get("message")
        user_alias = payload.get("userAlias")
        recipient_puuid = payload.get("recipientPuuid")
        timestamp = payload.get("timestamp", datetime.now().isoformat())
        if not message or not user_alias or not recipient_puuid:
            raise ValueError("Message, user alias, and recipient PUUID are required.")
        try:
            await self.pugsocket.send_direct_message(message, user_alias, recipient_puuid, timestamp)
            return {"status": "success", "message": "Direct message sent successfully"}
        except Exception as e:
            print(f"Error sending direct message: {e}")
            raise e
  
            
    ### LOBBY ###
    async def createlobby(self):
        if not self.pugsocket or not self.pugsocket.is_connected():
            print("WebSocket is not connected. Cannot create lobby.")
            return {"error": "WebSocket is not connected"}
        self.pugsocket.lobby_created_event.clear()
        print(f"Emitting lobby creation for {self.client.puuid}")
        message = {
            "puuid": self.client.puuid
        }
        try:
            await self.pugsocket.send_message("create_lobby", message)
            print("Sent 'create_lobby' message.")
            timeout = 5  # Increased timeout
            try:
                await asyncio.wait_for(self.pugsocket.lobby_created_event.wait(), timeout=timeout)
                print("Lobby creation event received.")
                return {
                    "status": "success",
                    "message": f"Lobby successfully created for: {self.client.puuid}",
                    'data': self.pugsocket.lobby_data,
                    "puuid": self.client.puuid,
                }
            except asyncio.TimeoutError:
                print("Lobby creation timed out.")
                return {"error": "Lobby creation timed out"}
        except Exception as e:
            print(f"Error sending 'create_lobby' message: {e}")
            return {"error": f"Error sending 'create_lobby' message: {str(e)}"}
    
    async def _create_custom_game(self, match_id: str, map_name: str, server: str, team: str = None):
        """
        Constructor client creates the custom game in Valorant.
        Performance: Runs in background task to avoid blocking
        """
        try:
            if not self.client:
                logger.error("[CREATE_CUSTOM_GAME] Client not initialized")
                return
            
            logger.info(f"[CREATE_CUSTOM_GAME] Starting custom game creation for match {match_id}")
            logger.info(f"[CREATE_CUSTOM_GAME] Map: {map_name}, Server: {server}")
            
            # Change party to custom mode
            custom_response = self.client.party_change_to_custom()
            pregame_id = custom_response.get('ID')
            
            if not pregame_id:
                raise ValueError("Failed to get pregame ID from custom game creation")

            logger.info(f"[CREATE_CUSTOM_GAME] Got pregame_id: {pregame_id} Map: {map_name}, Server: {server}")
            
            # Track the pregame_id we're sending
            self.sent_pregame_id = pregame_id
            self.is_constructor = True
            self.current_match_id = match_id
            logger.info(f"[VALIDATION] Constructor tracking sent pregame_id: {pregame_id[:8]}")
            
            # Set custom game settings
            logger.info("[CREATE_CUSTOM_GAME] Configuring game settings...")
            
            # Get map UUID from args
            map_uuid = None
            if self.args and 'mapPreferences' in self.args:
                map_uuid = self.args['mapPreferences'].get(map_name.lower())
            
            if not map_uuid:
                raise ValueError(f"Map UUID not found for map: {map_name}")
            
            # Get server GamePod URL
            game_pod = self._get_server_url(server)
            if not game_pod:
                raise ValueError(f"Server GamePod not found for server: {server}")
            
            settings = {
                "Map": map_uuid,
                "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
                "GamePod": game_pod,
                "UseBots": False,
                "GameRules": {
                    "AllowGameModifiers": "true",
                    "PlayOutAllRounds": "true",
                    "SkipMatchHistory": "true",
                    "TournamentMode": "false",
                    "IsOvertimeWinByTwo": "true",
                },
            }
            
            logger.info(f"[CREATE_CUSTOM_GAME] Settings: {json.dumps(settings, indent=2)}")
            self.client.party_set_custom_game_settings(settings)
            logger.info("[CREATE_CUSTOM_GAME] Settings applied successfully")
            
            # Wait a moment for settings to apply
            await asyncio.sleep(2)

            # VALIDATION: Before notifying server, ensure we have a valid pregame_id
            if not self._validate_pregame_id(pregame_id, 'custom_game_creation', match_id):
                logger.error(
                    f"[VALIDATION] Failed validation before notifying server, "
                    "but proceeding with notification"
                )

            # Notify Django server via WebSocket
            logger.info(f"[CREATE_CUSTOM_GAME] Notifying server of custom game creation: {pregame_id}")
            if self.pugsocket:
                await self.pugsocket.send_message('custom_game_created', {
                    'match_id': match_id,
                    'pregame_id': pregame_id,
                    'constructor_puuid': self.client.puuid
                })
                logger.info("[CREATE_CUSTOM_GAME] Successfully notified server")
            else:
                logger.error("[CREATE_CUSTOM_GAME] PugSocket not connected, cannot notify server")
            
            # CRITICAL: Constructor must send player_joined_game so server counts it in joined_players
            # Without this, server will only see 9/10 joined (missing constructor)
            await asyncio.sleep(random.uniform(0.3, 0.8))  # Small delay before reporting join
            logger.info(f"[CREATE_CUSTOM_GAME] Constructor reporting self as joined (team: {team or 'unknown'})")
            if self.pugsocket:
                # If team not provided, try to determine from latest_match_state
                if not team and self.latest_match_state:
                    try:
                        team_a_players = self.latest_match_state.get('team_a_players', [])
                        team_b_players = self.latest_match_state.get('team_b_players', [])
                        if any(p.get('puuid') == self.client.puuid for p in team_a_players):
                            team = 'team_a'
                        elif any(p.get('puuid') == self.client.puuid for p in team_b_players):
                            team = 'team_b'
                    except Exception as e:
                        logger.warning(f"[CREATE_CUSTOM_GAME] Could not determine team from snapshot: {e}")
                
                # Default to team_a if still unknown
                if not team:
                    team = 'team_a'
                
                await self.pugsocket.send_message('player_joined_game', {
                    'match_id': match_id,
                    'player_puuid': self.client.puuid,
                    'team': team
                })
                logger.info("[CREATE_CUSTOM_GAME] Successfully reported constructor as joined")
            
            # Store the game creation data for when all players join
            self._pending_game_start = {
                'match_id': match_id,
                'pregame_id': pregame_id,
                'settings_applied': True
            }
            
            logger.info("[CREATE_CUSTOM_GAME] Waiting for all players to join before starting game...")
            
        except Exception as e:
            logger.exception(f"[CREATE_CUSTOM_GAME] Error creating custom game: {str(e)}")
            # Reset validation state on error
            self.reset_pregame_validation()
            # Notify server of failure
            if self.pugsocket:
                try:
                    await self.pugsocket.send_message('custom_game_created', {
                        'match_id': match_id,
                        'pregame_id': None,
                        'constructor_puuid': self.client.puuid if self.client else None,
                        'error': str(e)
                    })
                except Exception as notify_error:
                    logger.error(f"[CREATE_CUSTOM_GAME] Failed to notify server of error: {notify_error}")
          
    
    def _get_server_url(self, server_name):
        """Helper method to get server URL from nested serverPreferences structure"""
        if not self.args or 'serverPreferences' not in self.args:
            return None
        
        server_prefs = self.args['serverPreferences']
        
        # Search through all regions for the server
        for region, servers in server_prefs.items():
            # Convert both keys to lowercase for case-insensitive lookup
            servers_lower = {k.lower(): v for k, v in servers.items()}
            if server_name.lower() in servers_lower:
                return servers_lower[server_name.lower()]
        
        return None
    
    
    
    def _extract_pregame_id_from_snapshot(self, snapshot: dict):
        """
        Extract pregame_id from match_state_update snapshot.
        
        Args:
            snapshot: match_state_update payload from server
        
        Returns:
            pregame_id if found, None otherwise
        """
        if not snapshot:
            return None
        
        try:
            execution = snapshot.get('execution') or {}
            pregame_id = execution.get('pregame_id')
            return pregame_id
        except Exception as e:
            logger.warning(f"[VALIDATION] Error extracting pregame_id from snapshot: {e}")
            return None

    def _extract_match_id_from_snapshot(self, snapshot: dict):
        """Extract match_id from snapshot."""
        if not snapshot:
            return None
        return snapshot.get('match_id')

    def _extract_constructor_from_snapshot(self, snapshot: dict):
        """Extract constructor puuid from snapshot."""
        if not snapshot:
            return None
        try:
            execution = snapshot.get('execution') or {}
            return execution.get('constructor')
        except Exception:
            return None

    def _validate_pregame_id(self, received_pregame_id: str, source: str, match_id: str = None) -> bool:
        """
        Validate that received pregame_id matches expected value.
        
        Args:
            received_pregame_id: The pregame_id received from server/event
            source: Source of the pregame_id (e.g., 'join_custom_game', 'match_state_update')
            match_id: Optional match_id for context
        
        Returns:
            True if valid or no expected value set yet, False if mismatch detected
        """
        if not received_pregame_id:
            return True  # No ID to validate (may be None initially)
        
        # For constructor: validate that sent pregame_id matches what we're seeing
        if self.is_constructor and self.sent_pregame_id:
            if self.sent_pregame_id != received_pregame_id:
                error_msg = (
                    f"[PREGAME_ID VALIDATION] CONSTRUCTOR MISMATCH: "
                    f"sent {self.sent_pregame_id[:8]}, got {received_pregame_id[:8]} "
                    f"(source: {source}, match: {match_id[:8] if match_id else 'Unknown'})"
                )
                logger.error(error_msg)
                self.pregame_id_validation_errors.append(error_msg)
                return False
        
        # For non-constructor: validate against expected value from snapshot
        if not self.is_constructor and self.expected_pregame_id:
            if self.expected_pregame_id != received_pregame_id:
                error_msg = (
                    f"[PREGAME_ID VALIDATION] PLAYER MISMATCH: "
                    f"expected {self.expected_pregame_id[:8]}, got {received_pregame_id[:8]} "
                    f"(source: {source}, match: {match_id[:8] if match_id else 'Unknown'})"
                )
                logger.error(error_msg)
                self.pregame_id_validation_errors.append(error_msg)
                # For non-constructor players, this is a critical error - don't proceed
                return False
        
        # Validation passed or no expected value yet
        if self.expected_pregame_id or self.sent_pregame_id:
            logger.debug(
                f"[PREGAME_ID VALIDATION] ✓ Validated: {received_pregame_id[:8]} "
                f"(source: {source})"
            )
        return True

    def _update_pregame_id_from_snapshot(self, snapshot: dict):
        """
        Update expected/sent pregame_id from match_state_update snapshot.
        Called from match_state_update_callback.
        """
        if not snapshot:
            return
        
        match_id = self._extract_match_id_from_snapshot(snapshot)
        if match_id:
            self.current_match_id = match_id
        
        pregame_id = self._extract_pregame_id_from_snapshot(snapshot)
        if not pregame_id:
            return  # No pregame_id in snapshot yet
        
        constructor_puuid = self._extract_constructor_from_snapshot(snapshot)
        is_constructor = constructor_puuid == self.puuid if constructor_puuid and self.puuid else False
        self.is_constructor = is_constructor
        
        # Track pregame_id based on role
        if is_constructor:
            # Constructor: validate snapshot matches what we sent
            if self.sent_pregame_id:
                self._validate_pregame_id(pregame_id, 'match_state_update', match_id)
            else:
                # Haven't sent yet, but snapshot has it (shouldn't happen, but track it)
                logger.warning(
                    f"[VALIDATION] Constructor sees pregame_id in snapshot before sending: {pregame_id[:8]}"
                )
        else:
            # Non-constructor: track expected value
            if self.expected_pregame_id is None:
                # First time seeing pregame_id - set as expected
                self.expected_pregame_id = pregame_id
                logger.info(
                    f"[VALIDATION] Tracking expected pregame_id: {pregame_id[:8]} "
                    f"(match: {match_id[:8] if match_id else 'Unknown'})"
                )
            elif self.expected_pregame_id != pregame_id:
                # Mismatch detected in snapshot itself
                error_msg = (
                    f"[PREGAME_ID VALIDATION] SNAPSHOT MISMATCH: "
                    f"expected {self.expected_pregame_id[:8]}, got {pregame_id[:8]} "
                    f"in match_state_update (match: {match_id[:8] if match_id else 'Unknown'})"
                )
                logger.error(error_msg)
                self.pregame_id_validation_errors.append(error_msg)

    def reset_pregame_validation(self):
        """Reset validation state (call when match ends or is cancelled)."""
        self.expected_pregame_id = None
        self.sent_pregame_id = None
        self.is_constructor = False
        self.current_match_id = None
        # Note: Keep validation_errors for debugging/monitoring, but could clear if desired

    def get_region_servers(self, region_code):
        """Get servers for a specific region code"""
        region_mapping = {
            'na': 'North America',
            'eu': 'Europe West',  # Default EU region
            'latam': 'Latin America',
            'br': 'Brazil',
            'ap': 'Asia Pacific',
            'kr': 'Korea'
        }
        
        region_name = region_mapping.get(region_code, 'North America')
        
        if self.args and 'serverPreferences' in self.args:
            return self.args['serverPreferences'].get(region_name, {})
        
        return {}
    
    
    # ============================================================
    # Match Monitoring (Phase 3)
    # ============================================================
    
    async def monitor_match(self, match_id: str, coregame_id: str):
        """
        Monitor live match and send updates to Django server.
        
        Performance Strategy:
        - Only constructor client monitors the match
        - Poll ValClient every 30 seconds (not 3 seconds)
        - Send only delta updates (score changes)
        - Stop monitoring when match completes
        
        This runs in background without blocking main thread.
        """
        logger.info(f"Starting match monitoring for {match_id}")
        
        last_score = {'team_a': 0, 'team_b': 0, 'round': 0}
        
        while True:
            try:
                # Fetch current match state from ValClient
                match_data = self.client.coregame_fetch_match(coregame_id)
                
                if not match_data:
                    logger.warning("No match data returned - match may have ended")
                    break
                
                # Parse score data
                current_score = self._parse_match_score(match_data)
                
                # Only send update if score changed
                if current_score != last_score:
                    await self._send_score_update(match_id, current_score)
                    last_score = current_score
                
                # Check if match completed
                if self._is_match_complete(match_data):
                    logger.info(f"Match {match_id} completed")
                    await self._send_match_complete(match_id, match_data)
                    break
                
                # Wait 30 seconds before next poll (performance optimization)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error monitoring match: {str(e)}")
                await asyncio.sleep(30)  # Continue monitoring despite errors
        
        logger.info(f"Match monitoring ended for {match_id}")
    
    
    def _parse_match_score(self, match_data: dict) -> dict:
        """
        Extract current score from ValClient match data.
        
        Performance: O(1) - direct field access
        """
        # Parse Valorant API response format
        teams = match_data.get('Teams', [])
        
        team_a_score = 0
        team_b_score = 0
        
        if len(teams) >= 2:
            team_a_score = teams[0].get('RoundsWon', 0)
            team_b_score = teams[1].get('RoundsWon', 0)
        
        current_round = match_data.get('RoundNumber', 0)
        
        return {
            'team_a': team_a_score,
            'team_b': team_b_score,
            'round': current_round
        }
    
    
    async def _send_score_update(self, match_id: str, score: dict):
        """
        Send score update to Django server via WebSocket.
        
        Performance: Single WebSocket message
        """
        if not self.pugsocket or not self.pugsocket.is_connected():
            return
        
        await self.pugsocket.send_message('match_score_update', {
            'match_id': match_id,
            'team_a_score': score['team_a'],
            'team_b_score': score['team_b'],
            'current_round': score['round']
        })
    
    
    def _is_match_complete(self, match_data: dict) -> bool:
        """
        Check if match is complete (team reached 13 rounds).
        
        Performance: O(1)
        """
        teams = match_data.get('Teams', [])
        if len(teams) < 2:
            return False
        
        team_a_score = teams[0].get('RoundsWon', 0)
        team_b_score = teams[1].get('RoundsWon', 0)
        
        # Standard match: first to 13
        # Overtime: win by 2 (if enabled in game rules)
        return team_a_score >= 13 or team_b_score >= 13
    
    
    async def _send_match_complete(self, match_id: str, match_data: dict):
        """
        Send match completion event to Django server.
        """
        if not self.pugsocket or not self.pugsocket.is_connected():
            return
        
        # Parse final scores
        final_score = self._parse_match_score(match_data)
        
        # Send completion event
        await self.pugsocket.send_message('match_completed', {
            'match_id': match_id,
            'final_data': {
                'team_a_score': final_score['team_a'],
                'team_b_score': final_score['team_b'],
                'total_rounds': final_score['round']
            }
        })
              