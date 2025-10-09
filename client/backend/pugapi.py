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
            print("WebSocket connection established")
            asyncio.create_task(self.listen_for_messages())
            return {"status": "success", "message": "WebSocket connection established"}
        except Exception as e:
            self.connected = False
            print(f"Failed to connect to WebSocket: {e}")
            return {"status": "failure", "message": f"Failed to connect to WebSocket: {str(e)}"}

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
            print("WebSocket connection closed by the server")
            self.connected = False
        except Exception as e:
            print(f"Error while listening to WebSocket messages: {e}")

    async def handle_message(self, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            print(data)
            event = data.get("event")
            payload = data.get("data")
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
        except Exception as e:
            print(f"Error processing 'match_ready' event: {e}")

    async def on_player_accepted(self, data):
        """Handle player accepted event."""
        try:
            accepted_count = data.get("accepted_count", 0)
            print("Players accepted:", accepted_count)
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
