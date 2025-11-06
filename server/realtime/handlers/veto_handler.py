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
    Thin layer that calls match_system orchestration.
    """
    
    async def handle_get_match_data(self, data):
        """
        Handle get_match_data event.
        Calls match_system.MatchManager (which has the business logic).
        """
        try:
            # Import from match_system (where veto logic NOW lives)
            from match_system.managers import MatchManager
            
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            
            if not match_id:
                await self.send_error("Match ID is required")
                return
            
            # Call match_system manager (has all the business logic)
            match_data = await MatchManager.get_match_data(match_id)
            
            if match_data:
                await self.send_event('match_data', match_data)
                logger.info(f"Sent match data for {match_id} to player {self.puuid}")
            else:
                await self.send_error(f"Match data not found for {match_id}")
                
        except Exception as e:
            logger.error(f"Error getting match data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.send_error(str(e))
    
    async def handle_veto_server(self, data):
        """
        Handle veto_server event.
        Calls match_system.MatchManager (orchestration + broadcasting).
        """
        try:
            # Import from match_system (where veto logic NOW lives)
            from match_system.managers import MatchManager
            
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            server_name = payload.get('server_name') or payload.get('server')
            
            if not match_id or not server_name:
                await self.send_error("match_id and server_name are required")
                return
            
            logger.info(f"Player {self.puuid[:12]}... vetoing server {server_name} in match {match_id[:8]}...")
            
            # Call NEW manager - it handles business logic + broadcasting
            result = await MatchManager.veto_server(match_id, self.puuid, server_name)
            
            if result['status'] == 'success':
                await self.send_event('server_veto_acknowledged', result)
                logger.info(f"Server veto successful for match {match_id}")
            else:
                await self.send_error(result.get('message', 'Failed to veto server'))
                
        except Exception as e:
            logger.error(f"Error vetoing server: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.send_error(str(e))
    
    async def handle_veto_map(self, data):
        """
        Handle veto_map event.
        Calls match_system.MatchManager (orchestration + broadcasting).
        """
        try:
            # Import from match_system (where veto logic NOW lives)
            from match_system.managers import MatchManager
            
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            map_name = payload.get('map') or payload.get('map_name')
            
            if not match_id or not map_name:
                await self.send_error("match_id and map are required")
                return
            
            logger.info(f"Player {self.puuid[:12]}... vetoing map {map_name} in match {match_id[:8]}...")
            
            # Call NEW manager - it handles business logic + broadcasting
            result = await MatchManager.veto_map(match_id, self.puuid, map_name)
            
            if result['status'] == 'success':
                await self.send_event('veto_acknowledged', result)
                logger.info(f"Map veto successful for match {match_id}")
            else:
                await self.send_error(result.get('message', 'Failed to veto map'))
                
        except Exception as e:
            logger.error(f"Error vetoing map: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.send_error(str(e))
    
    async def handle_select_side(self, data):
        """
        Handle select_side event.
        Calls match_system.MatchManager (orchestration + broadcasting).
        """
        try:
            # Import from match_system (where veto logic NOW lives)
            from match_system.managers import MatchManager
            
            payload = data.get('payload', {})
            match_id = payload.get('match_id')
            side = payload.get('side')
            
            if not match_id or not side:
                await self.send_error("match_id and side are required")
                return
            
            logger.info(f"Player {self.puuid[:12]}... selecting side {side} in match {match_id[:8]}...")
            
            # Call NEW manager - it handles business logic + broadcasting
            result = await MatchManager.select_side(match_id, self.puuid, side)
            
            if result['status'] == 'success':
                await self.send_event('side_acknowledged', result)
                logger.info(f"Side selection successful for match {match_id}")
            else:
                await self.send_error(result.get('message', 'Failed to select side'))
                
        except Exception as e:
            logger.error(f"Error selecting side: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.send_error(str(e))
