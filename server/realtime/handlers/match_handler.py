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
    Thin layer that calls match_system orchestration.
    """
    
    async def handle_accept_match(self, data):
        """
        Handle accept_match event.
        Calls NEW match_system manager (which does orchestration).
        """
        try:
            # Import NEW manager from match_system (orchestration layer)
            from match_system.managers import MatchConfirmationManager
            
            payload = data.get('payload', {})
            match_id = payload.get('match_id') or payload.get('match_confirmation_id')
            
            if not match_id:
                await self.send_error("Match ID is required")
                return
            
            logger.info(f"✅ Player {self.puuid[:12]}... ACCEPTED match {match_id[:8]}...")
            
            # Call NEW manager - it handles ALL orchestration including broadcasting
            result = await MatchConfirmationManager.accept_match(match_id, self.puuid)
            
            if result['status'] == 'success':
                # Convert any UUID objects to strings for JSON serialization
                safe_result = {
                    'status': result.get('status'),
                    'match_confirmed': result.get('match_confirmed'),
                    'accepted_count': result.get('accepted_count'),
                    'total_players': result.get('total_players'),
                    'timeout_seconds': result.get('timeout_seconds'),
                    'match_id': str(result.get('match_id')) if result.get('match_id') else None,
                    'lobby_id': str(result.get('lobby_id')) if result.get('lobby_id') else None,
                }
                
                # Send acknowledgment to accepting player
                await self.send_event('match_accepted', safe_result)
                
                logger.info(f"Player {self.puuid} accepted match {match_id}")
            else:
                await self.send_error(result.get('message', 'Failed to accept match'))
                
        except Exception as e:
            logger.error(f"Error accepting match: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.send_error(str(e))
    
    async def handle_decline_match(self, data):
        """
        Handle decline_match event.
        Calls NEW match_system manager (which does orchestration).
        """
        try:
            # Import NEW manager from match_system (orchestration layer)
            from match_system.managers import MatchConfirmationManager
            
            payload = data.get('payload', {})
            match_id = payload.get('match_id') or payload.get('match_confirmation_id')
            
            if not match_id:
                await self.send_error("Match ID is required")
                return
            
            result = await MatchConfirmationManager.decline_match(match_id, self.puuid)
            
            if result['status'] == 'success':
                await self.send_success("Match declined")
            else:
                await self.send_error(result.get('message', 'Failed to decline match'))
                
        except Exception as e:
            logger.error(f"Error declining match: {e}")
            await self.send_error(str(e))

