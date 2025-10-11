import requests, os, json, time, asyncio
from valclient import Client
from datetime import datetime
from pugapi import PugSocketClient


folder_name = 'data'
file_name = 'data.json'
file_path = os.path.join(os.path.dirname(__file__), folder_name, file_name)

class ValorantAPI(object):
    def __init__(self):
        self.client = None
        self.args = None
        self.pugsocket = None
        self.pugsocket_url = "ws://localhost:8000/ws/matchmaking/"
        self.session_id = None
        self.puuid = None
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.args = data
        except Exception as e:
            print(f"An error occurred while reading the JSON file: {e}")
    
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
                url = 'http://127.0.0.1:8000/login/login/'
                try:
                    response = requests.post(url, json=jsonargs)
                    if response.status_code == 200:
                        self.pugsocket_url = f"ws://localhost:8000/ws/matchmaking/{self.client.puuid}/"
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
                    
                    self.pugsocket.match_found_callback = match_found_callback
                    self._pending_match_data = None
                    
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
          
    # def queueup():
        
    # DEPRECATED - Use WebSocket events instead
    def queueupbypass(self,lobbyid,mapchoices,serverchoices):
        url = 'http://127.0.0.1:8000/matchmaking/queueup/'
        jsonargs = {
                    'puuid':self.client.puuid,
                    'lobbyid':lobbyid,
                    'mapchoices':mapchoices,
                    'serverchoices':serverchoices
            }
        response = requests.post(url, json=jsonargs)
        if response.status_code in [200, 201]:
            data = response.json()
            if data["status"] == 'build':
                if data["constructor"] == self.client.puuid:
                    partyid = self.client.party_fetch_player()
                    custom = self.client.party_change_to_custom()
                    buildargs = {
                        "Map": self.args['mapPreferences'][data["match_map"]],
                        "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
                        "GamePod": self._get_server_url(data["match_server"]),
                        "UseBots":False,
                        "GameRules":{
                            "AllowGameModifiers": "true",
                            "PlayOutAllRounds": "true",
                            "SkipMatchHistory": "true",
                            "TournamentMode": "false",
                            "IsOvertimeWinByTwo": "true",
                        },
                    }
                    setroom = 'http://127.0.0.1:8000/matchmaking/setroom/'
                    jsonargs = {
                            'pregame_id':custom["ID"],
                            'match_id':data['match_id']
                    }
                    response = requests.post(setroom, json=jsonargs)
                    if response.status_code in [200, 201]:
                        data = response.json()
                        settings = self.client.party_set_custom_game_settings(buildargs)
                        time.sleep(4)
                        self.client.party_start_custom_game()
                        return {"status": "success", "message": f"Matchroom successfully set for : {self.client.puuid}", 'data': data, 'buildargs': buildargs, 'custom_info':settings,'party_id':partyid}
                    else:
                        return {"error": "Request failed", "status_code": response.status_code}
                else:
                    time.sleep(2)
                    matchid = data["match_id"]
                    fetchroom = 'http://127.0.0.1:8000/matchmaking/fetchroom/'
                    jsonargs = {
                            'match':matchid,
                    }
                    response = requests.post(fetchroom, json=jsonargs)
                    if response.status_code in [200, 201]:
                        data = response.json()
                        self.client.party_join(data['pregame_id'])
                        return {"status": "success", "message": f"Matchroom successfully set for : {self.client.puuid}", 'data': data,}           
            else:
                    return data
        else:
                return {"error": "Request failed", "status_code": response.status_code}
              
              
    # DEPRECATED - Use WebSocket events instead
    def matchfound(self,lobbyid,mapchoices,serverchoices):
        url = 'http://127.0.0.1:8000/matchmaking/queueup/'
        jsonargs = {
                    'puuid':self.client.puuid,
                    'lobbyid':lobbyid,
                    'mapchoices':mapchoices,
                    'serverchoices':serverchoices
            }
        response = requests.post(url, json=jsonargs)
        if response.status_code in [200, 201]:
            data = response.json()
            if data["status"] == 'build':
                if data["constructor"] == self.client.puuid:
                    partyid = self.client.party_fetch_player()
                    custom = self.client.party_change_to_custom()
                    buildargs = {
                        "Map": self.args['mapPreferences'][data["match_map"]],
                        "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
                        "GamePod": self._get_server_url(data["match_server"]),
                        "UseBots":False,
                        "GameRules":{
                            "AllowGameModifiers": "true",
                            "PlayOutAllRounds": "true",
                            "SkipMatchHistory": "true",
                            "TournamentMode": "false",
                            "IsOvertimeWinByTwo": "true",
                        },
                    }
                    setroom = 'http://127.0.0.1:8000/matchmaking/setroom/'
                    jsonargs = {
                            'pregame_id':custom["ID"],
                            'match_id':data['match_id']
                    }
                    response = requests.post(setroom, json=jsonargs)
                    if response.status_code in [200, 201]:
                        data = response.json()
                        settings = self.client.party_set_custom_game_settings(buildargs)
                        time.sleep(4)
                        self.client.party_start_custom_game()
                        return {"status": "success", "message": f"Matchroom successfully set for : {self.client.puuid}", 'data': data, 'buildargs': buildargs, 'custom_info':settings,'party_id':partyid}
                    else:
                        return {"error": "Request failed", "status_code": response.status_code}
                else:
                    time.sleep(2)
                    matchid = data["match_id"]
                    fetchroom = 'http://127.0.0.1:8000/matchmaking/fetchroom/'
                    jsonargs = {
                            'match':matchid,
                    }
                    response = requests.post(fetchroom, json=jsonargs)
                    if response.status_code in [200, 201]:
                        data = response.json()
                        self.client.party_join(data['pregame_id'])
                        return {"status": "success", "message": f"Matchroom successfully set for : {self.client.puuid}", 'data': data,}           
            
            else:
                    return data
        else:
                return {"error": "Request failed", "status_code": response.status_code}
    
    def _get_server_url(self, server_name):
        """Helper method to get server URL from nested serverPreferences structure"""
        if not self.args or 'serverPreferences' not in self.args:
            return None
        
        server_prefs = self.args['serverPreferences']
        
        # Search through all regions for the server
        for region, servers in server_prefs.items():
            if server_name in servers:
                return servers[server_name]
        
        return None
    
    
    
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
        import logging
        logger = logging.getLogger(__name__)
        
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
              