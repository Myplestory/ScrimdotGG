"""
WebSocket Test Script for Lobby Operations
Tests the WebSocket consumer implementation
"""

import asyncio
import websockets
import json
from datetime import datetime


class WebSocketLobbyTester:
    def __init__(self, puuid, ws_url):
        self.puuid = puuid
        self.ws_url = ws_url
        self.ws = None
        self.lobby_id = None
        
    async def connect(self):
        """Connect to WebSocket server"""
        print(f"\n[{self.puuid}] Connecting to {self.ws_url}...")
        self.ws = await websockets.connect(self.ws_url)
        print(f"[{self.puuid}] ✓ Connected")
        
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.ws:
            await self.ws.close()
            print(f"[{self.puuid}] ✓ Disconnected")
    
    async def send_event(self, event, payload):
        """Send event to server"""
        message = json.dumps({
            'event': event,
            'payload': payload
        })
        await self.ws.send(message)
        print(f"[{self.puuid}] → Sent: {event}")
    
    async def receive_event(self, timeout=5):
        """Receive event from server"""
        try:
            response = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            data = json.loads(response)
            print(f"[{self.puuid}] ← Received: {data.get('event', 'unknown')}")
            return data
        except asyncio.TimeoutError:
            print(f"[{self.puuid}] ⚠ Timeout waiting for response")
            return None
    
    async def create_lobby(self):
        """Test: Create lobby"""
        print(f"\n{'='*60}")
        print(f"TEST: Create Lobby ({self.puuid})")
        print(f"{'='*60}")
        
        await self.send_event('create_lobby', {'puuid': self.puuid})
        response = await self.receive_event()
        
        if response and response.get('event') == 'lobby_created':
            self.lobby_id = response['data']['id']
            print(f"✅ Lobby created: {self.lobby_id}")
            print(f"   - Leader: {response['data']['lobby_leader']['alias']}")
            print(f"   - Size: {response['data']['size']}")
            return True
        else:
            print(f"❌ Failed to create lobby")
            if response and 'error' in response:
                print(f"   Error: {response['error']}")
            return False
    
    async def update_preferences(self):
        """Test: Update lobby preferences"""
        print(f"\n{'='*60}")
        print(f"TEST: Update Preferences")
        print(f"{'='*60}")
        
        await self.send_event('update_lobby_preferences', {
            'lobby_id': self.lobby_id,
            'requester_puuid': self.puuid,
            'map_preferences': ['Ascent', 'Bind', 'Haven', 'Pearl', 'Split'],
            'server_preferences': ['Virginia', 'Illinois']
        })
        
        response = await self.receive_event()
        
        if response and response.get('event') == 'preferences_updated':
            print(f"✅ Preferences updated")
            print(f"   - Maps: {response['data']['map_preferences']}")
            print(f"   - Servers: {response['data']['server_preferences']}")
            return True
        else:
            print(f"❌ Failed to update preferences")
            if response and 'error' in response:
                print(f"   Error: {response['error']}")
            return False
    
    async def invite_player(self, player_puuid):
        """Test: Invite player to lobby"""
        print(f"\n{'='*60}")
        print(f"TEST: Invite Player {player_puuid}")
        print(f"{'='*60}")
        
        await self.send_event('invite_to_lobby', {
            'lobby_id': self.lobby_id,
            'player_puuid': player_puuid,
            'inviter_puuid': self.puuid
        })
        
        response = await self.receive_event()
        
        if response and response.get('event') == 'player_invited':
            print(f"✅ Player invited")
            print(f"   - New size: {response['data']['size']}")
            return True
        else:
            print(f"❌ Failed to invite player")
            if response and 'error' in response:
                print(f"   Error: {response['error']}")
            return False
    
    async def leave_lobby(self):
        """Test: Leave lobby"""
        print(f"\n{'='*60}")
        print(f"TEST: Leave Lobby")
        print(f"{'='*60}")
        
        await self.send_event('leave_lobby', {
            'lobby_id': self.lobby_id,
            'player_puuid': self.puuid
        })
        
        response = await self.receive_event()
        
        if response and response.get('event') == 'left_lobby':
            print(f"✅ Left lobby successfully")
            return True
        else:
            print(f"❌ Failed to leave lobby")
            if response and 'error' in response:
                print(f"   Error: {response['error']}")
            return False
    
    async def send_chat_message(self, message):
        """Test: Send lobby chat message"""
        print(f"\n{'='*60}")
        print(f"TEST: Send Chat Message")
        print(f"{'='*60}")
        
        await self.send_event('lobby_message', {
            'message': message,
            'lobby_id': self.lobby_id,
            'userAlias': self.puuid,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"✓ Chat message sent: {message}")


async def test_single_player_flow():
    """Test single player lobby flow"""
    print("\n" + "="*60)
    print("WEBSOCKET TEST: Single Player Flow")
    print("="*60)
    
    # Note: Update PUUID with actual player PUUID from your database
    tester = WebSocketLobbyTester(
        puuid='test-player-websocket',
        ws_url='ws://localhost:8000/ws/matchmaking/test-player-websocket/'
    )
    
    try:
        await tester.connect()
        
        # Test 1: Create lobby
        if not await tester.create_lobby():
            return
        
        # Test 2: Update preferences
        await tester.update_preferences()
        
        # Test 3: Send chat message
        await tester.send_chat_message("Hello from WebSocket test!")
        
        # Test 4: Leave lobby
        await tester.leave_lobby()
        
        print("\n" + "="*60)
        print("✅ Single player test completed")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tester.disconnect()


async def test_multi_player_flow():
    """Test multi-player lobby flow"""
    print("\n" + "="*60)
    print("WEBSOCKET TEST: Multi-Player Flow")
    print("="*60)
    
    player1 = WebSocketLobbyTester(
        puuid='test-player-1',
        ws_url='ws://localhost:8000/ws/matchmaking/test-player-1/'
    )
    
    player2 = WebSocketLobbyTester(
        puuid='test-player-2',
        ws_url='ws://localhost:8000/ws/matchmaking/test-player-2/'
    )
    
    try:
        # Connect both players
        await player1.connect()
        await player2.connect()
        
        # Player 1 creates lobby
        if not await player1.create_lobby():
            return
        
        # Player 1 invites Player 2
        await player1.invite_player('test-player-2')
        
        # Both players send chat messages
        await player1.send_chat_message("Hey player 2!")
        await player2.send_chat_message("Hi player 1!")
        
        # Player 2 leaves
        player2.lobby_id = player1.lobby_id
        await player2.leave_lobby()
        
        # Player 1 leaves
        await player1.leave_lobby()
        
        print("\n" + "="*60)
        print("✅ Multi-player test completed")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await player1.disconnect()
        await player2.disconnect()


if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║         WebSocket Lobby Operations Test Suite             ║
╚════════════════════════════════════════════════════════════╝

Prerequisites:
1. Django server must be running (python manage.py runserver)
2. Redis must be running
3. Players must exist in database with PUUIDs:
   - test-player-websocket
   - test-player-1  
   - test-player-2

Note: Update PUUIDs in script if using different test accounts.
    """)
    
    choice = input("Run [1] Single Player or [2] Multi-Player test? (1/2): ").strip()
    
    if choice == '1':
        asyncio.run(test_single_player_flow())
    elif choice == '2':
        asyncio.run(test_multi_player_flow())
    else:
        print("Invalid choice. Exiting.")

