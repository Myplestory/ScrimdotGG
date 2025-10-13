"""
Bot Auto-Acceptor
Monitors for match_found events and automatically accepts for all bot players.
"""

import os
import sys
import asyncio
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from channels.layers import get_channel_layer
from matchmaking.match_confirmation import MatchConfirmationManager
from asgiref.sync import sync_to_async
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotAutoAcceptor:
    """Automatically accepts matches for bot players"""
    
    def __init__(self):
        self.monitored_bots = set()  # Set of bot PUUIDs
        self.active_matches = {}  # {match_id: {match_data, accepted_bots}}
        self.running = False
    
    def add_bot(self, puuid: str):
        """Add a bot to monitor"""
        self.monitored_bots.add(puuid)
        logger.info(f"[BOT_ACCEPTOR] Monitoring bot: {puuid}")
    
    def add_bots(self, puuids: list):
        """Add multiple bots to monitor"""
        for puuid in puuids:
            self.add_bot(puuid)
    
    async def check_for_matches(self):
        """Check Redis for active match confirmations"""
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            
            # Get all match confirmation keys
            match_keys = redis_conn.keys("match_confirmation:*:data")
            
            for key in match_keys:
                match_id = key.decode('utf-8').split(':')[1]
                
                # Skip if already processed
                if match_id in self.active_matches:
                    continue
                
                # Get match data
                match_data_json = redis_conn.get(key)
                if not match_data_json:
                    continue
                
                import json
                match_data = json.loads(match_data_json)
                
                # Check if any of our bots are in this match
                all_players = []
                if 'team_a' in match_data and 'team_b' in match_data:
                    all_players.extend([p['puuid'] for p in match_data['team_a']['players']])
                    all_players.extend([p['puuid'] for p in match_data['team_b']['players']])
                elif 'lobby1' in match_data and 'lobby2' in match_data:
                    all_players.extend([p['puuid'] for p in match_data['lobby1']['players']])
                    all_players.extend([p['puuid'] for p in match_data['lobby2']['players']])
                
                bots_in_match = [p for p in all_players if p in self.monitored_bots]
                
                if bots_in_match:
                    logger.info(f"[BOT_ACCEPTOR] Found match {match_id[:8]} with {len(bots_in_match)} bots")
                    self.active_matches[match_id] = {
                        'match_data': match_data,
                        'bots': bots_in_match,
                        'accepted': set()
                    }
                    
                    # Auto-accept for all bots
                    await self.accept_for_bots(match_id, bots_in_match)
        
        except Exception as e:
            logger.error(f"[BOT_ACCEPTOR] Error checking matches: {e}")
    
    async def accept_for_bots(self, match_id: str, bot_puuids: list):
        """Auto-accept match for all bots (concurrent with random delays)"""
        import random
        
        async def accept_with_delay(puuid: str):
            """Accept match for a bot after random delay"""
            try:
                # Random delay between 1-15 seconds (realistic player behavior)
                delay = random.uniform(1.0, 15.0)
                logger.info(f"[BOT_ACCEPTOR] Bot {puuid[:12]} will accept in {delay:.1f}s")
                await asyncio.sleep(delay)
                
                result = await MatchConfirmationManager.accept_match(match_id, puuid)
                
                if result.get('status') == 'success':
                    if match_id in self.active_matches:
                        self.active_matches[match_id]['accepted'].add(puuid)
                    accepted_count = result.get('accepted_count', 0)
                    total_players = result.get('total_players', 10)
                    
                    logger.info(f"[BOT_ACCEPTOR] Bot {puuid[:12]} accepted [{accepted_count}/{total_players}]")
                    
                    if result.get('match_confirmed'):
                        logger.info(f"[BOT_ACCEPTOR] Match {match_id[:8]} fully accepted! All players ready.")
                        # Clean up
                        if match_id in self.active_matches:
                            del self.active_matches[match_id]
                else:
                    logger.warning(f"[BOT_ACCEPTOR] Bot {puuid[:12]} failed to accept: {result.get('message')}")
            
            except Exception as e:
                logger.error(f"[BOT_ACCEPTOR] Error accepting for bot {puuid}: {e}")
        
        # Accept all bots concurrently (each with their own random delay)
        await asyncio.gather(*[accept_with_delay(puuid) for puuid in bot_puuids])
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("[BOT_ACCEPTOR] Starting auto-accept monitoring...")
        self.running = True
        
        while self.running:
            try:
                await self.check_for_matches()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"[BOT_ACCEPTOR] Monitor loop error: {e}")
                await asyncio.sleep(1)
    
    def stop(self):
        """Stop monitoring"""
        logger.info("[BOT_ACCEPTOR] Stopping auto-accept monitoring...")
        self.running = False


# Singleton instance
_acceptor_instance = None

def get_acceptor():
    """Get singleton acceptor instance"""
    global _acceptor_instance
    if _acceptor_instance is None:
        _acceptor_instance = BotAutoAcceptor()
    return _acceptor_instance


async def start_bot_acceptor(bot_puuids: list):
    """Start bot auto-acceptor with list of bot PUUIDs"""
    acceptor = get_acceptor()
    acceptor.add_bots(bot_puuids)
    
    # Start monitoring in background
    task = asyncio.create_task(acceptor.monitor_loop())
    return acceptor, task


if __name__ == "__main__":
    # Test mode - monitor all queuebot- players
    async def test():
        from scrimgg.models import Player
        
        def get_bots():
            return list(Player.objects.filter(puuid__startswith='queuebot-').values_list('puuid', flat=True))
        
        bot_puuids = await sync_to_async(get_bots)()
        
        logger.info(f"[TEST] Found {len(bot_puuids)} bots to monitor")
        
        acceptor, task = await start_bot_acceptor(bot_puuids)
        
        logger.info("[TEST] Monitoring for matches... Press Ctrl+C to stop")
        
        try:
            await task
        except KeyboardInterrupt:
            acceptor.stop()
            logger.info("[TEST] Stopped")
    
    asyncio.run(test())

