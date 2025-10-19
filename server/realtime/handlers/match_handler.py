"""
Match confirmation WebSocket event handler.
Handles match acceptance/decline during confirmation phase.

EXTRACTED FROM: matchmaking/consumers.py
"""

import logging
from .base import BaseHandler

logger = logging.getLogger(__name__)


class MatchHandler(BaseHandler):
    """
    Handles match confirmation events (accept/decline).
    """
    
    async def handle_accept_match(self, data):
        """Handle accept_match event."""
        from match_system.managers import MatchConfirmationManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id') or payload.get('match_confirmation_id')
            
            if not match_id:
                await self.send_error("Match ID is required")
                return
            
            result = await MatchConfirmationManager.accept_match(match_id, self.puuid)
            
            if result['status'] == 'success':
                # If match is fully confirmed, join match group
                if result.get('all_accepted'):
                    actual_match_id = result.get('match_instance_id')
                    if actual_match_id:
                        await self.consumer.join_match_group(actual_match_id)
                
                await self.send_event('player_accepted', result)
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error accepting match: {e}")
            await self.send_error(str(e))
    
    async def handle_decline_match(self, data):
        """Handle decline_match event."""
        from match_system.managers import MatchConfirmationManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id') or payload.get('match_confirmation_id')
            
            if not match_id:
                await self.send_error("Match ID is required")
                return
            
            result = await MatchConfirmationManager.decline_match(match_id, self.puuid)
            
            if result['status'] == 'success':
                await self.send_success("Match declined")
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error declining match: {e}")
            await self.send_error(str(e))

