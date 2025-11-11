import asyncio
import json
import websockets


class PugSocketClient:
    def __init__(self):
        self.websocket = None
        self.connected = False
        
        self.pugsocket_url = None
        self.pugsocket_sess = None
        
        self.lobby_data = None
        self.player_data = None
        self.chat_messages = []
        self.latest_match_state = None

    ### ASYNC EVENTS ###
        self.lobby_created_event = asyncio.Event()
        self.player_data_event = asyncio.Event()
        self.match_data_event = asyncio.Event()

        # Callback hooks set by clientapi
        self.match_ready_callback = None
        self.player_accepted_callback = None
        self.match_confirmed_callback = None
        self.match_data_callback = None
        self.match_state_update_callback = None
        self.match_construction_started_callback = None
        self.join_custom_game_callback = None
        self.player_joined_game_callback = None
        self.player_join_failed_callback = None
        self.all_players_joined_callback = None
        self.match_in_progress_callback = None
        self.match_completed_callback = None

    ### CONNECTION COMMANDS ###

    async def start_connection(self, websocket_url):
        """Start a WebSocket connection."""
        self.pugsocket_url = websocket_url
        try:
            self.websocket = await websockets.connect(websocket_url)
            self.connected = True
            print("[PUGAPI] WebSocket connection established")
            asyncio.create_task(self.listen_for_messages())
            asyncio.create_task(self.connection_monitor())
            return {"status": "success", "message": "WebSocket connection established"}
        except Exception as e:
            self.connected = False
            print(f"[PUGAPI] Failed to connect to WebSocket: {e}")
            return {"status": "failure", "message": f"Failed to connect to WebSocket: {str(e)}"}

    async def connection_monitor(self):
        """Monitor WebSocket connection status."""
        while self.connected:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                if self.websocket:
                    # Try to ping the connection to check if it's alive
                    try:
                        await self.websocket.ping()
                        print("[PUGAPI] WebSocket connection is alive")
                    except Exception:
                        print("[PUGAPI] WebSocket connection is dead!")
                        self.connected = False
                        break
                else:
                    print("[PUGAPI] WebSocket connection is dead!")
                    self.connected = False
                    break
            except Exception as e:
                print(f"[PUGAPI] Connection monitor error: {e}")
                break

    async def stop_connection(self):
        """Stop the WebSocket connection."""
        if self.connected and self.websocket:
            await self.websocket.close()
            self.connected = False
            print("WebSocket connection closed")

    def is_connected(self):
        """Check if the client is connected."""
        return self.connected

    ### LISTENING FOR EVENTS ###

    async def listen_for_messages(self):
        """Listen for incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                await self.handle_message(message)
        except websockets.ConnectionClosed:
            print("[PUGAPI] WebSocket connection closed by the server")
            self.connected = False
        except Exception as e:
            print(f"[PUGAPI] Error while listening to WebSocket messages: {e}")
            self.connected = False

    async def handle_message(self, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            print(f"[PUGAPI] Received message: {data}")
            event = data.get("event")
            payload = data.get("payload")
            print(f"[PUGAPI] Event: {event}, Payload: {payload}")
            # Route the message to the correct handler
            if event == "lobby_info":
                await self.on_lobby_info(payload)
            elif event == "lobby_created":
                await self.on_lobby_created(payload)
            elif event == "player_model":
                await self.on_player_model(payload)
            elif event == "enqueue":
                await self.on_enqueue(payload)
            elif event == "match_ready":
                await self.on_match_ready(payload)
            elif event == "player_accepted":
                await self.on_player_accepted(payload)
            elif event == "lobby_message":
                await self.on_lobby_message(payload)
            elif event == "direct_message":
                await self.on_direct_message(payload)
            elif event == "match_found":
                await self.on_match_found(payload)
            elif event == "match_proposed":
                await self.on_match_proposed(payload)
            elif event == "match_confirmed":
                await self.on_match_confirmed(payload)
            elif event == "match_data":
                await self.on_match_data(payload)
            elif event == "match_state_update":
                await self.on_match_state_update(payload)
            elif event == "match_construction_started":
                await self.on_match_construction_started(payload)
            elif event == "join_custom_game":
                await self.on_join_custom_game(payload)
            elif event == "player_joined_game":
                await self.on_player_joined_game(payload)
            elif event == "player_join_failed":
                await self.on_player_join_failed(payload)
            elif event == "all_players_joined":
                await self.on_all_players_joined(payload)
            elif event == "match_in_progress":
                await self.on_match_in_progress(payload)
            elif event == "match_completed":
                await self.on_match_completed(payload)
            else:
                print(f"Unknown event received: {event}")
        except Exception as e:
            print(f"Error processing WebSocket message: {e}")

    ### EVENT HANDLERS ###
    
    async def on_player_model(self, data):
        """Handle player model event."""
        try:
            self.player_data = data
            self.player_data_event.set()  # Signal player data reception
            print("Player model received:", self.player_data)
        except Exception as e:
            print(f"Error processing 'player_model' event: {e}")

    async def on_match_ready(self, data):
        """Handle match ready event."""
        try:
            print("Match ready:", data.get("message"))
            
            # Forward to main WebSocket connection via callback
            if hasattr(self, 'match_ready_callback'):
                await self.match_ready_callback(data)
        except Exception as e:
            print(f"Error processing 'match_ready' event: {e}")

    async def on_player_accepted(self, data):
        """Handle player accepted event."""
        try:
            accepted_count = data.get("accepted_count", 0)
            total_players = data.get("total_players", 10)
            timeout_seconds = data.get("timeout_seconds", 30)
            print(f"Players accepted: {accepted_count}/{total_players}, timeout: {timeout_seconds}s")
            
            # Forward to main WebSocket connection via callback
            if hasattr(self, 'player_accepted_callback'):
                await self.player_accepted_callback(data)
        except Exception as e:
            print(f"Error processing 'player_accepted' event: {e}")

    async def on_lobby_created(self, data):
        """Handle lobby created event."""
        try:
            self.lobby_data = data
            self.lobby_created_event.set()  # Signal lobby creation
            print("Lobby created:", self.lobby_data)
        except Exception as e:
            print(f"Error processing 'lobby_created' event: {e}")

    async def on_lobby_info(self, data):
        """Handle lobby info event."""
        try:
            print("Lobby Info:", data)
        except Exception as e:
            print(f"Error processing 'lobby_info' event: {e}")
            
    async def on_direct_message(self, data):
        """Handle direct (private) messages."""
        try:
            username = data.get("username", "Unknown")
            message = data.get("message", "")
            timestamp = data.get("timestamp", "Unknown time")
            self.chat_messages.append({
                "type": "direct",
                "username": username,
                "message": message,
                "timestamp": timestamp
            })
            print(f"Direct message from {username}: {message} (at {timestamp})")
        except Exception as e:
            print(f"Error processing 'direct_message': {e}")
            
    async def on_lobby_message(self, data):
        """Handle lobby chat messages."""
        try:
            username = data.get("username", "Unknown")
            message = data.get("message", "")
            timestamp = data.get("timestamp", "Unknown time")
            self.chat_messages.append({
                "type": "lobby",
                "username": username,
                "message": message,
                "timestamp": timestamp
            })
            print(f"Lobby chat message from {username}: {message} (at {timestamp})")
        except Exception as e:
            print(f"Error processing 'lobby_message': {e}")

    async def on_enqueue(self, data):
        """Handle enqueue event."""
        try:
            print("Enqueue:", data.get("message"))
        except Exception as e:
            print(f"Error processing 'enqueue' event: {e}")

    async def on_match_found(self, data):
        """Handle match found event."""
        try:
            match_id = data.get("match_id")
            match_confirmation_id = data.get("match_confirmation_id")
            timeout_seconds = data.get("timeout_seconds", 30)
            message = data.get("message", "Match found! Please accept to continue.")
            
            print(f"[MATCH FOUND] Match ID: {match_id}, Timeout: {timeout_seconds}s")
            print(f"[MATCH FOUND] Message: {message}")
            
            # Store the match data for the main WebSocket to pick up
            self.match_found_data = data
            print(f"[MATCH FOUND] Stored match data for main WebSocket")
            
            # Emit event to notify main WebSocket connection
            if hasattr(self, 'match_found_callback'):
                await self.match_found_callback(data)
        except Exception as e:
            print(f"Error processing 'match_found' event: {e}")
    
    async def on_match_proposed(self, data):
        """Handle match proposed event (acceptance required)."""
        try:
            match_id = data.get("match_id")
            timeout_seconds = data.get("timeout_seconds", 30)
            
            print(f"[MATCH PROPOSED] Match ID: {match_id}, Timeout: {timeout_seconds}s")
            
            # Forward to main WebSocket connection via callback
            if hasattr(self, 'match_proposed_callback'):
                await self.match_proposed_callback(data)
        except Exception as e:
            print(f"Error processing 'match_proposed' event: {e}")
    
    async def on_match_confirmed(self, data):
        """Handle match confirmed event."""
        try:
            match_id = data.get("match_id")
            team = data.get("team")
            redirect_url = data.get("redirect_url")
            
            print(f"[MATCH CONFIRMED] Match ID: {match_id}, Team: {team}")
            print(f"[MATCH CONFIRMED] Redirect URL: {redirect_url}")
            
            # Forward to main WebSocket connection via callback
            if hasattr(self, 'match_confirmed_callback'):
                await self.match_confirmed_callback(data)
        except Exception as e:
            print(f"Error processing 'match_confirmed' event: {e}")
    
    async def on_map_veto_started(self, data):
        """Handle map veto started event."""
        try:
            match_id = data.get("match_id")
            print(f"[MAP VETO STARTED] Match ID: {match_id}")
            
            # Forward to main WebSocket connection via callback
            if hasattr(self, 'map_veto_started_callback'):
                await self.map_veto_started_callback(data)
        except Exception as e:
            print(f"Error processing 'map_veto_started' event: {e}")
    
    async def on_match_data(self, data):
        """Handle match data."""
        try:
            self.match_data = data
            self.match_data_event.set()
            print("Match data received:", self.match_data)

            # Forward to main WebSocket connection via callback
            if hasattr(self, 'match_data_callback'):
                await self.match_data_callback(data)
        except Exception as e:
            print(f"Error processing 'match_data' event: {e}")

    async def on_match_state_update(self, data):
        """Handle unified match state snapshot from Django."""
        try:
            self.latest_match_state = data
            if hasattr(self, 'match_state_update_callback'):
                await self.match_state_update_callback(data)
        except Exception as e:
            print(f"Error processing 'match_state_update' event: {e}")
    
    async def on_side_selection_timeout(self, data):
        """Handle side selection timeout (auto-select) from Django."""
        try:
            auto_selected_side = data.get("auto_selected_side")
            side_selection_complete = data.get("side_selection_complete", False)
            match_ready = data.get("match_ready", False)
            
            print(f"[SIDE SELECTION TIMEOUT] Auto-selected: {auto_selected_side}, Complete: {side_selection_complete}, Match Ready: {match_ready}")
            
            # Forward to main WebSocket connection via callback
            if hasattr(self, 'side_selection_timeout_callback'):
                await self.side_selection_timeout_callback(data)
        except Exception as e:
            print(f"Error processing 'side_selection_timeout' event: {e}")
    
    async def on_side_selected(self, data):
        """Handle side selection from Django."""
        try:
            side = data.get("side")
            selected_by = data.get("selected_by")
            print(f"[SIDE SELECTED] {selected_by} selected {side}")
            
            # Forward to main WebSocket connection via callback
            if hasattr(self, 'side_selected_callback'):
                await self.side_selected_callback(data)
        except Exception as e:
            print(f"Error processing 'side_selected' event: {e}")

    async def on_side_acknowledged(self, data):
        """Handle side selection acknowledgment from Django."""
        try:
            status = data.get("status")
            side = data.get("side")
            selected_by = data.get("selected_by")
            side_complete = data.get("side_complete", False)
            match_ready = data.get("match_ready", False)
            print(f"[SIDE ACKNOWLEDGED] {selected_by} selected {side}, complete: {side_complete}, ready: {match_ready}")
            
            # Forward to main WebSocket connection via callback
            if hasattr(self, 'side_acknowledged_callback'):
                await self.side_acknowledged_callback(data)
        except Exception as e:
            print(f"Error processing 'side_acknowledged' event: {e}")

    async def on_match_construction_started(self, data):
        """Handle constructor assignment from the server."""
        try:
            if self.match_construction_started_callback:
                await self.match_construction_started_callback(data)
        except Exception as e:
            print(f"Error processing 'match_construction_started' event: {e}")

    async def on_join_custom_game(self, data):
        try:
            if self.join_custom_game_callback:
                await self.join_custom_game_callback(data)
        except Exception as e:
            print(f"Error processing 'join_custom_game' event: {e}")

    async def on_player_joined_game(self, data):
        try:
            if self.player_joined_game_callback:
                await self.player_joined_game_callback(data)
        except Exception as e:
            print(f"Error processing 'player_joined_game' event: {e}")

    async def on_player_join_failed(self, data):
        try:
            if self.player_join_failed_callback:
                await self.player_join_failed_callback(data)
        except Exception as e:
            print(f"Error processing 'player_join_failed' event: {e}")

    async def on_all_players_joined(self, data):
        try:
            if self.all_players_joined_callback:
                await self.all_players_joined_callback(data)
        except Exception as e:
            print(f"Error processing 'all_players_joined' event: {e}")

    async def on_match_in_progress(self, data):
        try:
            if self.match_in_progress_callback:
                await self.match_in_progress_callback(data)
        except Exception as e:
            print(f"Error processing 'match_in_progress' event: {e}")

    async def on_match_completed(self, data):
        try:
            if self.match_completed_callback:
                await self.match_completed_callback(data)
        except Exception as e:
            print(f"Error processing 'match_completed' event: {e}")

    ### COMMANDS ###

    async def enqueue(self, data):
        """Send enqueue command to the server."""
        try:
            message = {"event": "enqueue", "payload": data}
            await self.websocket.send(json.dumps(message))
            print("Enqueue command sent:", data)
        except Exception as e:
            print(f"Error sending enqueue command: {e}")
            
    # Default emit message
    async def send_message(self, event, payload):
        """Send a message through the WebSocket."""
        try:
            message = {"event": event, "payload": payload}
            await self.websocket.send(json.dumps(message))
            print(f"Message sent to event '{event}': {payload}")
        except Exception as e:
            print(f"Error sending message: {e}")
            
    ### CHAT ###

    async def send_lobby_message(self, payload):
        """Send a lobby message through the WebSocket."""
        await self.send_message("lobby_message", payload)

    async def send_direct_message(self, message, username, recipient_puuid, timestamp):
        """Send a direct message through the WebSocket."""
        if not self.connected:
            print("WebSocket is not connected. Cannot send direct message.")
            return {"status": "error", "message": "WebSocket is not connected"}
        try:
            payload = {
                "message": message,
                "username": username,
                "recipient_puuid": recipient_puuid,
                "timestamp": timestamp
            }
            await self.websocket.send(json.dumps({"event": "direct_message", "payload": payload}))
            print(f"Direct message sent: {message} to {recipient_puuid} by {username} at {timestamp}")
            return {"status": "success", "message": "Direct message sent successfully"}
        except Exception as e:
            print(f"Error sending direct message: {e}")
            return {"status": "error", "message": f"Failed to send direct message: {str(e)}"}
