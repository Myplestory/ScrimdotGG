"""
Veto and side selection WebSocket event handler.

EXTRACTED FROM: matchmaking/consumers.py
"""

import logging
from .base import BaseHandler

logger = logging.getLogger(__name__)


class VetoHandler(BaseHandler):
    """
    Handles veto and side selection events.
    """
    
    async def handle_get_match_data(self, data):
        """Handle get_match_data event."""
        from match_system.managers import MatchManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            
            if not match_id:
                await self.send_error("Match ID is required")
                return
            
            result = await MatchManager.get_match_data(match_id, self.puuid)
            
            if result['status'] == 'success':
                await self.send_event('match_data', result['match_data'])
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error getting match data: {e}")
            await self.send_error(str(e))
    
    async def handle_veto_server(self, data):
        """Handle veto_server event."""
        from match_system.managers import MatchManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            server_name = payload.get('server')
            
            result = await MatchManager.veto_server(match_id, self.puuid, server_name)
            
            if result['status'] == 'success':
                await self.send_success("Server vetoed")
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error vetoing server: {e}")
            await self.send_error(str(e))
    
    async def handle_veto_map(self, data):
        """Handle veto_map event."""
        from match_system.managers import MatchManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            map_name = payload.get('map')
            
            result = await MatchManager.veto_map(match_id, self.puuid, map_name)
            
            if result['status'] == 'success':
                await self.send_success("Map vetoed")
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error vetoing map: {e}")
            await self.send_error(str(e))
    
    async def handle_select_side(self, data):
        """Handle select_side event."""
        from match_system.managers import MatchManager
        
        try:
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            side = payload.get('side')
            
            result = await MatchManager.select_side(match_id, self.puuid, side)
            
            if result['status'] == 'success':
                await self.send_success("Side selected")
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error selecting side: {e}")
            await self.send_error(str(e))

