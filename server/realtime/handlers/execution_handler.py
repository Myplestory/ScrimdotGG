"""
Match execution WebSocket event handler.
Handles custom game creation and live match events.

EXTRACTED FROM: matchmaking/consumers.py
"""

import logging
from .base import BaseHandler

logger = logging.getLogger(__name__)


class ExecutionHandler(BaseHandler):
    """
    Handles match execution events (game creation, player joins, etc.).
    """
    
    async def handle_custom_game_created(self, data):
        """Handle custom_game_created event."""
        from match_execution.execution_manager import MatchExecutionManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            pregame_id = payload.get('pregame_id')
            
            result = await MatchExecutionManager.handle_custom_game_created(
                match_id, pregame_id, self.puuid
            )
            
            if result['status'] == 'success':
                await self.send_success("Custom game created")
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error handling custom game created: {e}")
            await self.send_error(str(e))
    
    async def handle_player_joined_game(self, data):
        """Handle player_joined_game event."""
        from match_execution.execution_manager import MatchExecutionManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            
            result = await MatchExecutionManager.handle_player_joined(match_id, self.puuid)
            
            if result['status'] == 'success':
                await self.send_success("Player joined successfully")
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error handling player joined: {e}")
            await self.send_error(str(e))
    
    async def handle_match_started(self, data):
        """Handle match_started event."""
        from match_execution.execution_manager import MatchExecutionManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            coregame_id = payload.get('coregame_id')
            
            result = await MatchExecutionManager.handle_match_started(match_id, coregame_id)
            
            if result['status'] == 'success':
                await self.send_success("Match started")
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error handling match started: {e}")
            await self.send_error(str(e))
    
    async def handle_player_join_failed(self, data):
        """Handle player_join_failed event."""
        logger.warning(f"Player {self.puuid[:8]}... failed to join match")
        # Handle retry logic or notify team
        pass
    
    async def handle_match_score_update(self, data):
        """Handle match_score_update event."""
        # Update match scores in database
        pass
    
    async def handle_match_completed(self, data):
        """Handle match_completed event."""
        # Mark match as completed, calculate stats
        pass
    
    async def handle_request_rejoin(self, data):
        """Handle request_rejoin event."""
        # Generate rejoin token for disconnected player
        pass
    
    async def handle_get_match_statistics(self, data):
        """Handle get_match_statistics event."""
        # Fetch and return match statistics
        pass

