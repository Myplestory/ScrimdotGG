"""
Bot WebSocket Client for Testing
Connects bots to the matchmaking WebSocket consumer for realistic testing.
"""

import asyncio
import websockets
import json
import logging
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)


class BotWebSocketClient:
    """
    WebSocket client for bot players.
    Handles connection, event listening, and proper cleanup.
    """
    
    def __init__(self, bot_puuid: str, server_url: str = "ws://localhost:8000"):
        self.bot_puuid = bot_puuid
        self.websocket_url = f"{server_url}/ws/matchmaking/{bot_puuid}/"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.running = False
        self.listen_task: Optional[asyncio.Task] = None
        
        # Event callbacks
        self.match_found_callback: Optional[Callable] = None
        self.player_accepted_callback: Optional[Callable] = None
        self.match_ready_callback: Optional[Callable] = None
        
        # Match data
        self.current_match_id: Optional[str] = None
    
    async def connect(self) -> bool:
        """
        Connect to the WebSocket server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"[BOT WS] Connecting bot {self.bot_puuid[:12]}... to {self.websocket_url}")
            # Add keepalive to prevent connection from timing out
            self.websocket = await websockets.connect(
                self.websocket_url,
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=10,   # Wait 10 seconds for pong response
                close_timeout=10   # Timeout for close handshake
            )
            self.connected = True
            self.running = True
            logger.info(f"[BOT WS] ✅ Bot {self.bot_puuid[:12]} connected with keepalive")
            
            # Start listening for messages
            self.listen_task = asyncio.create_task(self._listen())
            
            return True
        except Exception as e:
            logger.error(f"[BOT WS] ❌ Failed to connect bot {self.bot_puuid[:12]}: {e}")
            self.connected = False
            return False
    
    async def _listen(self):
        """
        Listen for incoming WebSocket messages.
        Runs in background task.
        """
        try:
            async for message in self.websocket:
                if not self.running:
                    break
                
                try:
                    data = json.loads(message)
                    event = data.get('event')
                    payload = data.get('data', {})
                    
                    await self._handle_event(event, payload)
                except json.JSONDecodeError as e:
                    logger.error(f"[BOT WS] Failed to parse message for bot {self.bot_puuid[:12]}: {e}")
                except Exception as e:
                    logger.error(f"[BOT WS] Error handling message for bot {self.bot_puuid[:12]}: {e}")
        except websockets.ConnectionClosed:
            logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} connection closed")
            self.connected = False
            self.running = False
        except Exception as e:
            logger.error(f"[BOT WS] Listen error for bot {self.bot_puuid[:12]}: {e}")
            self.connected = False
            self.running = False
    
    async def _handle_event(self, event: str, payload: dict):
        """
        Handle incoming WebSocket events.
        
        Args:
            event: Event name
            payload: Event data
        """
        logger.debug(f"[BOT WS] Bot {self.bot_puuid[:12]} received event: {event}")
        
        if event == 'match_found':
            self.current_match_id = payload.get('match_id')
            logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} found match: {self.current_match_id[:8] if self.current_match_id else 'N/A'}")
            
            if self.match_found_callback:
                await self.match_found_callback(payload)
        
        elif event == 'player_accepted':
            accepted_count = payload.get('accepted_count', 0)
            total_players = payload.get('total_players', 10)
            logger.debug(f"[BOT WS] Bot {self.bot_puuid[:12]} sees acceptance: {accepted_count}/{total_players}")
            
            if self.player_accepted_callback:
                await self.player_accepted_callback(payload)
        
        elif event == 'match_ready':
            logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} - Match is ready!")
            
            if self.match_ready_callback:
                await self.match_ready_callback(payload)
        
        elif event == 'match_timeout':
            logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} - Match timed out")
            self.current_match_id = None
        
        elif event == 'lobby_queued':
            logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} - Lobby queued")
        
        elif event == 'lobby_removed_from_queue':
            logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} - Removed from queue")
        
        else:
            logger.debug(f"[BOT WS] Bot {self.bot_puuid[:12]} - Unhandled event: {event}")
    
    async def accept_match(self, match_id: str) -> bool:
        """
        Send match acceptance through WebSocket.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.connected or not self.websocket:
            logger.error(f"[BOT WS] Bot {self.bot_puuid[:12]} not connected, cannot accept match")
            return False
        
        try:
            message = json.dumps({
                'event': 'accept_match',
                'payload': {'match_id': match_id}
            })
            await self.websocket.send(message)
            logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} sent accept for match {match_id[:8]}")
            return True
        except Exception as e:
            logger.error(f"[BOT WS] Failed to send accept for bot {self.bot_puuid[:12]}: {e}")
            return False
    
    async def close(self):
        """
        Close the WebSocket connection gracefully.
        Ensures proper cleanup of resources.
        """
        logger.info(f"[BOT WS] Closing connection for bot {self.bot_puuid[:12]}")
        
        # Stop the listen loop
        self.running = False
        self.connected = False
        
        # Cancel listen task if it exists
        if self.listen_task and not self.listen_task.done():
            self.listen_task.cancel()
            try:
                await asyncio.wait_for(self.listen_task, timeout=2.0)
            except asyncio.CancelledError:
                logger.debug(f"[BOT WS] Listen task cancelled for bot {self.bot_puuid[:12]}")
            except asyncio.TimeoutError:
                logger.warning(f"[BOT WS] Listen task timeout for bot {self.bot_puuid[:12]}")
            except Exception as e:
                logger.warning(f"[BOT WS] Error cancelling listen task for bot {self.bot_puuid[:12]}: {e}")
        
        # Close the WebSocket with timeout
        if self.websocket:
            try:
                # Send close frame
                if not self.websocket.closed:
                    close_task = asyncio.create_task(self.websocket.close())
                    await asyncio.wait_for(close_task, timeout=3.0)
                logger.info(f"[BOT WS] ✅ Bot {self.bot_puuid[:12]} connection closed cleanly")
            except asyncio.TimeoutError:
                logger.warning(f"[BOT WS] WebSocket close timeout for bot {self.bot_puuid[:12]}, forcing close")
            except Exception as e:
                logger.warning(f"[BOT WS] Error closing websocket for bot {self.bot_puuid[:12]}: {e}")
        
        # Clear references
        self.websocket = None
        self.listen_task = None
        self.match_found_callback = None
        self.player_accepted_callback = None
        self.match_ready_callback = None
        
        logger.debug(f"[BOT WS] All resources cleared for bot {self.bot_puuid[:12]}")
    
    def is_connected(self) -> bool:
        """Check if bot is connected."""
        return self.connected and self.websocket is not None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.close()


class BotWebSocketManager:
    """
    Manages multiple bot WebSocket connections.
    Handles connection lifecycle and cleanup for all bots.
    """
    
    def __init__(self, server_url: str = "ws://localhost:8000"):
        self.server_url = server_url
        self.clients: Dict[str, BotWebSocketClient] = {}
        self.running = False
    
    async def connect_bot(self, bot_puuid: str) -> Optional[BotWebSocketClient]:
        """
        Connect a single bot.
        
        Args:
            bot_puuid: Bot's PUUID
            
        Returns:
            BotWebSocketClient if successful, None otherwise
        """
        if bot_puuid in self.clients:
            logger.warning(f"[BOT WS MANAGER] Bot {bot_puuid[:12]} already connected")
            return self.clients[bot_puuid]
        
        client = BotWebSocketClient(bot_puuid, self.server_url)
        success = await client.connect()
        
        if success:
            self.clients[bot_puuid] = client
            logger.info(f"[BOT WS MANAGER] Bot {bot_puuid[:12]} added to manager")
            return client
        else:
            logger.error(f"[BOT WS MANAGER] Failed to connect bot {bot_puuid[:12]}")
            return None
    
    async def connect_bots(self, bot_puuids: list) -> int:
        """
        Connect multiple bots concurrently.
        
        Args:
            bot_puuids: List of bot PUUIDs
            
        Returns:
            Number of successfully connected bots
        """
        logger.info(f"[BOT WS MANAGER] Connecting {len(bot_puuids)} bots...")
        
        # Connect all bots concurrently
        tasks = [self.connect_bot(puuid) for puuid in bot_puuids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful connections
        success_count = sum(1 for r in results if isinstance(r, BotWebSocketClient) and r is not None)
        
        logger.info(f"[BOT WS MANAGER] ✅ Connected {success_count}/{len(bot_puuids)} bots")
        return success_count
    
    def get_bot(self, bot_puuid: str) -> Optional[BotWebSocketClient]:
        """Get a bot client by PUUID."""
        return self.clients.get(bot_puuid)
    
    def get_all_bots(self) -> list:
        """Get all connected bot clients."""
        return list(self.clients.values())
    
    def get_connected_count(self) -> int:
        """Get number of connected bots."""
        return sum(1 for client in self.clients.values() if client.is_connected())
    
    async def close_bot(self, bot_puuid: str):
        """
        Close a single bot connection.
        
        Args:
            bot_puuid: Bot's PUUID
        """
        if bot_puuid in self.clients:
            await self.clients[bot_puuid].close()
            del self.clients[bot_puuid]
            logger.info(f"[BOT WS MANAGER] Bot {bot_puuid[:12]} removed from manager")
    
    async def close_all(self):
        """
        Close all bot connections gracefully.
        Ensures proper cleanup of all resources.
        """
        if not self.clients:
            logger.info(f"[BOT WS MANAGER] No bot connections to close")
            return
        
        logger.info(f"[BOT WS MANAGER] Closing all {len(self.clients)} bot connections...")
        
        # Close all bots concurrently with timeout
        close_tasks = [client.close() for client in self.clients.values()]
        
        try:
            # Give 10 seconds total for all connections to close
            results = await asyncio.wait_for(
                asyncio.gather(*close_tasks, return_exceptions=True),
                timeout=10.0
            )
            
            # Count successes and failures
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                logger.warning(f"[BOT WS MANAGER] {len(errors)} connections had errors during close")
                for error in errors[:3]:  # Show first 3 errors
                    logger.debug(f"[BOT WS MANAGER] Close error: {error}")
            
            logger.info(f"[BOT WS MANAGER] ✅ All {len(self.clients)} bot connections closed")
            
        except asyncio.TimeoutError:
            logger.warning(f"[BOT WS MANAGER] Timeout closing connections, some may not have closed cleanly")
        except Exception as e:
            logger.error(f"[BOT WS MANAGER] Error during close_all: {e}")
        finally:
            # Always clear the clients dict
            self.clients.clear()
            self.running = False
            logger.info(f"[BOT WS MANAGER] Client list cleared")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.running = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.close_all()


# Example usage
if __name__ == "__main__":
    async def test():
        # Test with context manager (automatic cleanup)
        async with BotWebSocketManager() as manager:
            # Connect bots
            bot_puuids = [f"test-bot-{i}" for i in range(3)]
            await manager.connect_bots(bot_puuids)
            
            # Wait a bit
            await asyncio.sleep(5)
            
            # Context manager will automatically close all connections
        
        print("Test complete - all connections cleaned up")
    
    asyncio.run(test())

