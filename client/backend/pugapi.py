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

    ### ASYNC EVENTS ###
        self.lobby_created_event = asyncio.Event()
        self.player_data_event = asyncio.Event()

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
                if self.websocket and not self.websocket.closed:
                    print("[PUGAPI] WebSocket connection is alive")
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
            payload = data.get("data")
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
