"""
Bot Auto-Acceptor with WebSocket Connections
Monitors for match_found events via WebSocket and automatically accepts for bot players.
This version uses proper WebSocket connections like real clients.
"""

import os
import sys
import asyncio
import django
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from testing.bot_websocket_client import BotWebSocketManager, BotWebSocketClient
from asgiref.sync import sync_to_async
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotAutoAcceptorWS:
    """
    Automatically accepts matches for bot players using WebSocket connections.
    Uses real WebSocket connections so broadcasts work correctly.
    """
    
    def __init__(self, server_url: str = "ws://localhost:8000"):
        self.ws_manager = BotWebSocketManager(server_url=server_url)
        self.monitored_bots = set()  # Bots that should auto-accept
        self.ignore_bots = set()  # Bots that should NOT accept (for timeout testing)
        self.active_matches = {}  # {match_id: {bots, acceptance_tasks}}
        self.running = False
    
    def add_bot(self, puuid: str, auto_accept: bool = True):
        """
        Add a bot to monitor.
        
        Args:
            puuid: Bot's PUUID
            auto_accept: If True, bot will auto-accept matches. If False, bot will NOT accept.
        """
        if auto_accept:
            self.monitored_bots.add(puuid)
            logger.info(f"[BOT_ACCEPTOR_WS] Will auto-accept for: {puuid}")
        else:
            self.ignore_bots.add(puuid)
            logger.info(f"[BOT_ACCEPTOR_WS] Will NOT accept for: {puuid}")
    
    def add_bots(self, puuids: list, auto_accept_all: bool = True, exclude_last: bool = False):
        """
        Add multiple bots to monitor.
        
        Args:
            puuids: List of bot PUUIDs
            auto_accept_all: If True, all bots auto-accept. If False, none accept.
            exclude_last: If True, exclude the last bot from auto-accepting (for timeout testing)
        """
        for i, puuid in enumerate(puuids):
            # If exclude_last is True, don't auto-accept the last bot
            should_accept = auto_accept_all and not (exclude_last and i == len(puuids) - 1)
            self.add_bot(puuid, auto_accept=should_accept)
    
    async def connect_bots(self, puuids: list) -> int:
        """
        Connect all bots to WebSocket.
        
        Args:
            puuids: List of all bot PUUIDs (both accepting and non-accepting)
            
        Returns:
            Number of successfully connected bots
        """
        logger.info(f"[BOT_ACCEPTOR_WS] Connecting {len(puuids)} bots to WebSocket...")
        
        # Connect all bots
        success_count = await self.ws_manager.connect_bots(puuids)
        
        # Set up match_found callbacks for all bots
        for puuid in puuids:
            bot_client = self.ws_manager.get_bot(puuid)
            if bot_client:
                # Bind the callback
                bot_client.match_found_callback = self._create_match_found_callback(puuid, bot_client)
        
        logger.info(f"[BOT_ACCEPTOR_WS] ✅ Connected {success_count}/{len(puuids)} bots with callbacks")
        return success_count
    
    def _create_match_found_callback(self, bot_puuid: str, bot_client: BotWebSocketClient):
        """
        Create a match_found callback for a specific bot.
        
        Args:
            bot_puuid: Bot's PUUID
            bot_client: Bot's WebSocket client
            
        Returns:
            Async callback function
        """
        async def on_match_found(payload: dict):
            match_id = payload.get('match_id')
            
            if not match_id:
                logger.warning(f"[BOT_ACCEPTOR_WS] Bot {bot_puuid[:12]} received match_found without match_id")
                return
            
            logger.info(f"[BOT_ACCEPTOR_WS] Bot {bot_puuid[:12]} found match: {match_id[:8]}")
            
            # Check if this bot should auto-accept
            if bot_puuid in self.monitored_bots:
                # Random delay between 1-15 seconds
                delay = random.uniform(1.0, 15.0)
                logger.info(f"[BOT_ACCEPTOR_WS] Bot {bot_puuid[:12]} will accept in {delay:.1f}s")
                
                # Create acceptance task
                task = asyncio.create_task(self._accept_after_delay(bot_client, match_id, delay))
                
                # Track the task
                if match_id not in self.active_matches:
                    self.active_matches[match_id] = {
                        'bots': set(),
                        'tasks': []
                    }
                self.active_matches[match_id]['bots'].add(bot_puuid)
                self.active_matches[match_id]['tasks'].append(task)
            
            elif bot_puuid in self.ignore_bots:
                logger.info(f"[BOT_ACCEPTOR_WS] Bot {bot_puuid[:12]} will NOT accept (testing timeout)")
            
            else:
                logger.warning(f"[BOT_ACCEPTOR_WS] Bot {bot_puuid[:12]} not in monitored or ignore lists")
        
        return on_match_found
    
    async def _accept_after_delay(self, bot_client: BotWebSocketClient, match_id: str, delay: float):
        """
        Accept a match after a delay.
        
        Args:
            bot_client: Bot's WebSocket client
            match_id: Match confirmation ID
            delay: Delay in seconds before accepting
        """
        try:
            await asyncio.sleep(delay)
            
            success = await bot_client.accept_match(match_id)
            
            if success:
                logger.info(f"[BOT_ACCEPTOR_WS] ✅ Bot {bot_client.bot_puuid[:12]} accepted match {match_id[:8]}")
            else:
                logger.error(f"[BOT_ACCEPTOR_WS] ❌ Bot {bot_client.bot_puuid[:12]} failed to accept match {match_id[:8]}")
        
        except asyncio.CancelledError:
            logger.info(f"[BOT_ACCEPTOR_WS] Acceptance cancelled for bot {bot_client.bot_puuid[:12]}")
        except Exception as e:
            logger.error(f"[BOT_ACCEPTOR_WS] Error in accept_after_delay for bot {bot_client.bot_puuid[:12]}: {e}")
    
    async def cleanup_match(self, match_id: str):
        """
        Clean up match data after completion/timeout.
        
        Args:
            match_id: Match confirmation ID
        """
        if match_id not in self.active_matches:
            return
        
        match_data = self.active_matches[match_id]
        tasks = match_data.get('tasks', [])
        
        if tasks:
            logger.debug(f"[BOT_ACCEPTOR_WS] Cancelling {len(tasks)} pending tasks for match {match_id[:8]}")
            
            # Cancel all pending acceptance tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to finish cancelling (with timeout)
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"[BOT_ACCEPTOR_WS] Timeout waiting for tasks to cancel for match {match_id[:8]}")
            except Exception as e:
                logger.debug(f"[BOT_ACCEPTOR_WS] Error during task cleanup: {e}")
        
        del self.active_matches[match_id]
        logger.info(f"[BOT_ACCEPTOR_WS] ✅ Cleaned up match {match_id[:8]}")
    
    async def close(self):
        """
        Close all WebSocket connections and cleanup.
        Ensures all resources are properly released.
        """
        logger.info("[BOT_ACCEPTOR_WS] Starting shutdown sequence...")
        
        try:
            # Step 1: Cancel all active match tasks
            if self.active_matches:
                logger.info(f"[BOT_ACCEPTOR_WS] Cleaning up {len(self.active_matches)} active matches...")
                match_ids = list(self.active_matches.keys())
                
                cleanup_tasks = [self.cleanup_match(match_id) for match_id in match_ids]
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*cleanup_tasks, return_exceptions=True),
                        timeout=5.0
                    )
                    logger.info(f"[BOT_ACCEPTOR_WS] ✅ All match tasks cleaned up")
                except asyncio.TimeoutError:
                    logger.warning(f"[BOT_ACCEPTOR_WS] Timeout cleaning up matches, forcing shutdown")
            
            # Step 2: Close all WebSocket connections
            logger.info(f"[BOT_ACCEPTOR_WS] Closing WebSocket connections...")
            await self.ws_manager.close_all()
            
            # Step 3: Clear state
            self.running = False
            self.monitored_bots.clear()
            self.ignore_bots.clear()
            self.active_matches.clear()
            
            logger.info("[BOT_ACCEPTOR_WS] ✅ Shutdown complete - all connections closed and resources cleared")
            
        except Exception as e:
            logger.error(f"[BOT_ACCEPTOR_WS] Error during shutdown: {e}")
            # Force cleanup even on error
            self.running = False
            try:
                await self.ws_manager.close_all()
            except:
                pass
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            'total_bots': len(self.monitored_bots) + len(self.ignore_bots),
            'auto_accept_bots': len(self.monitored_bots),
            'ignore_bots': len(self.ignore_bots),
            'connected_bots': self.ws_manager.get_connected_count(),
            'active_matches': len(self.active_matches)
        }


# Singleton instance for compatibility with old code
_acceptor_instance_ws = None

def get_acceptor_ws():
    """Get singleton acceptor instance (WebSocket version)"""
    global _acceptor_instance_ws
    if _acceptor_instance_ws is None:
        _acceptor_instance_ws = BotAutoAcceptorWS()
    return _acceptor_instance_ws


async def start_bot_acceptor_ws(bot_puuids: list, exclude_last: bool = True):
    """
    Start bot auto-acceptor with WebSocket connections.
    
    Args:
        bot_puuids: List of bot PUUIDs
        exclude_last: If True, last bot will NOT accept (for timeout testing)
        
    Returns:
        BotAutoAcceptorWS instance
    """
    acceptor = BotAutoAcceptorWS()
    
    # Add bots (exclude last one from auto-accepting if requested)
    acceptor.add_bots(bot_puuids, auto_accept_all=True, exclude_last=exclude_last)
    
    # Connect all bots to WebSocket
    await acceptor.connect_bots(bot_puuids)
    
    logger.info(f"[BOT_ACCEPTOR_WS] Started with {len(bot_puuids)} bots")
    logger.info(f"[BOT_ACCEPTOR_WS] Stats: {acceptor.get_stats()}")
    
    return acceptor


if __name__ == "__main__":
    # Test mode - monitor all queuebot- players
    async def test():
        from scrimgg.models import Player
        
        def get_bots():
            return list(Player.objects.filter(puuid__startswith='queuebot-').values_list('puuid', flat=True))
        
        bot_puuids = await sync_to_async(get_bots)()
        
        logger.info(f"[TEST] Found {len(bot_puuids)} bots to monitor")
        
        acceptor = await start_bot_acceptor_ws(bot_puuids, exclude_last=True)
        
        logger.info("[TEST] Monitoring for matches... Press Ctrl+C to stop")
        
        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(10)
                stats = acceptor.get_stats()
                logger.info(f"[TEST] Stats: {stats}")
        except KeyboardInterrupt:
            logger.info("[TEST] Stopping...")
        finally:
            await acceptor.close()
            logger.info("[TEST] Stopped")
    
    asyncio.run(test())

