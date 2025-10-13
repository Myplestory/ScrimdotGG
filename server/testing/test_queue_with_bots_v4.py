"""
Queue Test with Bot Players V4 - Real User Simulation
Creates 9 bot players with proper UUIDs that connect via WebSocket consumers.
Tests complete user flow including match acceptance and veto functionality.

This tests:
1. 9 bots with UUIDs connecting via WebSocket (ALL 9 will accept)
2. You join queue via client (10th player)
3. Matchmaker finds match
4. ALL 9 bots auto-accept via WebSocket
5. YOU accept
6. Match confirmed → redirect to match page
7. Veto phase starts
8. Test veto functionality

Key improvements over V3:
- Bots use proper UUID format (like real users)
- Bots connect via WebSocket consumer (same path as real users)
- Identical validation and queue flow
- Better simulation of real user behavior
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
        self.websocket = None
        self.lobby_id = None
        self.connected = False
        self.in_queue = False
        self.match_found = False
        
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
            logger.info(f"🤖 Bot {self.bot_alias} connected to WebSocket")
            
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            logger.error(f"❌ Bot {self.bot_alias} failed to connect: {e}")
            raise
    
    async def _listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                await self._handle_message(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🤖 Bot {self.bot_alias} WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"❌ Bot {self.bot_alias} message handling error: {e}")
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket messages"""
        event = data.get('event')
        payload = data.get('data', {})
        error = data.get('error')
        
        # Log all messages for debugging
        logger.debug(f"🤖 Bot {self.bot_alias} received: {data}")
        
        if error:
            logger.error(f"❌ Bot {self.bot_alias} WebSocket error: {error}")
            
        elif event == 'lobby_created':
            logger.info(f"🏠 Bot {self.bot_alias} lobby created successfully")
            
        elif event == 'joined_queue':
            self.in_queue = True
            logger.info(f"✅ Bot {self.bot_alias} joined queue successfully")
            
        elif event == 'queue_blocked':
            logger.error(f"❌ Bot {self.bot_alias} queue blocked: {payload.get('message')}")
            
        elif event == 'match_found' or event == 'pug_match_found':
            self.match_found = True
            match_id = payload.get('match_id')
            logger.info(f"🎮 Bot {self.bot_alias} found match {match_id[:8] if match_id else 'Unknown'}, auto-accepting...")
            
            # Auto-accept the match (consumer expects match_id in payload)
            await self._send_message('accept_match', {
                'match_id': match_id,
                'player_puuid': self.bot_puuid
            })
            
        elif event == 'match_confirmed':
            logger.info(f"✅ Bot {self.bot_alias} match confirmed!")
            
        elif event == 'error':
            logger.error(f"❌ Bot {self.bot_alias} error: {payload}")
            
        else:
            # Log unhandled events for debugging
            logger.debug(f"🤖 Bot {self.bot_alias} unhandled event '{event}': {payload}")
    
    async def _send_message(self, event: str, payload: dict):
        """Send a message to the WebSocket"""
        if not self.connected or not self.websocket:
            logger.error(f"❌ Bot {self.bot_alias} not connected, cannot send {event}")
            return
        
        message = json.dumps({
            "event": event,
            "payload": payload
        })
        
        try:
            await self.websocket.send(message)
            logger.debug(f"📤 Bot {self.bot_alias} sent: {event}")
        except Exception as e:
            logger.error(f"❌ Bot {self.bot_alias} failed to send {event}: {e}")
    
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
                logger.error(f"❌ Bot {self.bot_alias} failed to get lobby")
                return False
            
            self.lobby_id = str(lobby.id)
            logger.info(f"🏠 Bot {self.bot_alias} got lobby: {self.lobby_id}")
            
            # Step 3: Set lobby preferences
            await self._send_message('update_lobby_preferences', {
                'lobby_id': self.lobby_id,
                'requester_puuid': self.bot_puuid,
                'map_preferences': ['Ascent', 'Bind', 'Breeze', 'Haven', 'Icebox', 'Lotus', 'Pearl'],
                'server_preferences': ['Virginia', 'Illinois']
            })
            
            # Wait a moment for preferences update
            await asyncio.sleep(0.5)
            
            # Step 4: Join queue via WebSocket (like real users)
            await self._send_message('add_lobby_to_queue', {
                'lobby_id': self.lobby_id,
                'requester_puuid': self.bot_puuid
            })
            
            logger.info(f"🎯 Bot {self.bot_alias} requested to join queue")
            return True
            
        except Exception as e:
            logger.error(f"❌ Bot {self.bot_alias} failed to create lobby and queue: {e}")
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
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info(f"🤖 Bot {self.bot_alias} disconnected")


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
                'team': 'none'
            }
        )
        
        # Update if existed
        if not created:
            bot.elo = bot_elo
            bot.mmr = bot_mmr
            bot.trueskill_mu = bot_mu
            bot.trueskill_sigma = 9.0
            bot.save()
        
        return bot
    
    bot_player = await sync_to_async(create_bot)()
    logger.info(f"👤 Created bot player: {bot_alias} (PUUID: {bot_puuid[:8]}...)")
    
    # Create WebSocket client
    bot_client = BotWebSocketClient(bot_puuid, bot_alias)
    
    try:
        # Connect to WebSocket consumer
        await bot_client.connect()
        
        # Create lobby and join queue (like real users)
        success = await bot_client.create_lobby_and_queue()
        
        if success:
            logger.info(f"✅ Bot {bot_alias} successfully set up and queued")
            return bot_client
        else:
            logger.error(f"❌ Bot {bot_alias} failed to queue")
            await bot_client.disconnect()
            return None
            
    except Exception as e:
        logger.error(f"❌ Bot {bot_alias} setup failed: {e}")
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
        print(f"   ✅ Found your player: {you.alias} (ELO: {you.elo})")
        return you
    else:
        print("   ❌ Could not find your player account!")
        print("   💡 Make sure you've logged in at least once to create your player profile")
        return None


async def wait_for_match_or_timeout(bot_clients: List[BotWebSocketClient], timeout_seconds: int = 120):
    """Wait for match to be found or timeout"""
    print(f"\n[3/3] Waiting for match (timeout: {timeout_seconds}s)...")
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        
        if elapsed >= timeout_seconds:
            print(f"   ⏰ Timeout reached ({timeout_seconds}s)")
            return False
        
        # Check if any bot found a match
        for bot in bot_clients:
            if bot.match_found:
                print(f"   🎮 Match found! Bot {bot.bot_alias} detected match")
                return True
        
        # Show progress every 10 seconds
        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
            remaining = timeout_seconds - int(elapsed)
            print(f"   ⏳ Still waiting... ({remaining}s remaining)")
        
        await asyncio.sleep(1)


async def cleanup_bots(bot_clients: List[BotWebSocketClient]):
    """Clean up bot WebSocket connections"""
    print("\n🧹 Cleaning up bot connections...")
    
    for bot in bot_clients:
        try:
            await bot.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting bot {bot.bot_alias}: {e}")
    
    print("   ✅ All bot connections closed")


async def main():
    """Main test function"""
    print("=" * 80)
    print("🤖 QUEUE TEST WITH BOTS V4 - Real User Simulation")
    print("=" * 80)
    print("This version uses proper UUIDs and WebSocket connections")
    print("Bots behave identically to real users for accurate testing")
    print("=" * 80)
    
    # Configuration
    NUM_BOTS = 9
    BASE_ELO = 6000
    BASE_MMR = 6000
    REGION = 'na'
    
    bot_clients = []
    
    try:
        # Step 1: Verify your player exists
        your_player = await get_your_player_info()
        if not your_player:
            print("\n❌ Cannot proceed without your player account")
            return
        
        # Step 2: Create bots with WebSocket connections
        print(f"\n[2/3] Creating {NUM_BOTS} bots with WebSocket connections...")
        print(f"   📊 Base ELO: {BASE_ELO} (±50 variation)")
        print(f"   📊 Base MMR: {BASE_MMR} (±50 variation)")
        
        for i in range(NUM_BOTS):
            print(f"   🤖 Creating bot {i+1}/{NUM_BOTS}...")
            
            bot_client = await create_bot_with_websocket(i, BASE_ELO, BASE_MMR, REGION)
            
            if bot_client:
                bot_clients.append(bot_client)
                print(f"   ✅ Bot {i+1} ready")
            else:
                print(f"   ❌ Bot {i+1} failed")
            
            # Small delay between bot creation
            await asyncio.sleep(0.5)
        
        successful_bots = len(bot_clients)
        print(f"\n   📊 Successfully created {successful_bots}/{NUM_BOTS} bots")
        
        if successful_bots == 0:
            print("   ❌ No bots were created successfully")
            return
        
        # Step 3: Wait for match or timeout
        print(f"\n   🎯 {successful_bots} bots are now in queue")
        print("   💡 Now join queue with your client to trigger matchmaking!")
        print("   💡 The bots will auto-accept when a match is found")
        
        match_found = await wait_for_match_or_timeout(bot_clients, timeout_seconds=300)
        
        if match_found:
            print("\n🎉 SUCCESS! Match was found and bots auto-accepted")
            print("   💡 Check your client - you should see the match confirmation")
            print("   💡 Accept the match to proceed to veto phase")
            
            # Keep bots alive for a bit longer for veto testing
            print("\n   ⏳ Keeping bots alive for veto testing (60s)...")
            await asyncio.sleep(60)
            
        else:
            print("\n⏰ No match found within timeout period")
            print("   💡 Make sure you join queue with your client")
            print("   💡 Check that Celery worker is running for matchmaking")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test error details:")
    
    finally:
        # Always cleanup
        await cleanup_bots(bot_clients)
        
        print("\n" + "=" * 80)
        print("🏁 Test completed!")
        print("=" * 80)
        print("💡 Use cleanup_bots_simple.py to clean up database entries")
        print("💡 Restart Daphne if you see connection issues")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
