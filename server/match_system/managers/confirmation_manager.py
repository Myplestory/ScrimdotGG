"""
Match Confirmation Manager - Orchestration Layer
Wraps legacy matchmaking code and adds broadcasting.
"""
import logging
from typing import Dict
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class MatchConfirmationManager:
    """
    Orchestration layer for match confirmation.
    Wraps old matchmaking/match_confirmation.py and adds broadcasting.
    """
    
    @staticmethod
    async def accept_match(match_id: str, player_puuid: str) -> Dict:
        """
        Accept match for a player with full orchestration.
        
        This is the NEW orchestration layer that:
        1. Calls old match_confirmation.py for Redis/business logic
        2. Adds broadcasting to all lobbies involved
        3. Broadcasts match_ready when all players accept
        
        Args:
            match_id: Match confirmation ID
            player_puuid: Player's PUUID
            
        Returns:
            Dict with acceptance status
        """
        try:
            # Import old manager for business logic
            from matchmaking.match_confirmation import MatchConfirmationManager as OldManager
            
            # Call old manager for Redis operations and business logic
            result = await OldManager.accept_match(match_id, player_puuid)
            
            if result['status'] != 'success':
                return result
            
            # Extract data for broadcasting
            match_lobbies = result.get('match_lobbies', [])
            accepted_count = result.get('accepted_count')
            total_players = result.get('total_players')
            timeout_seconds = result.get('timeout_seconds')
            match_confirmed = result.get('match_confirmed', False)
            
            # Get channel layer for broadcasting
            channel_layer = get_channel_layer()
            
            if match_confirmed:
                # All players accepted - broadcast match_ready to ALL lobbies
                logger.info(f"🎉 MATCH READY! All players accepted match {match_id[:8]}...")
                logger.info(f"   Notifying {len(match_lobbies)} lobbies that match is ready")
                
                for lobby_id in match_lobbies:
                    await channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'match_ready',
                            'message': 'Match is ready!',
                            'match_id': str(result.get('match_id')) if result.get('match_id') else None
                        }
                    )
                
                logger.info(f"   ✅ All {len(match_lobbies)} lobbies notified - match starting!")
            else:
                # Broadcast acceptance progress to ALL lobbies involved
                if match_lobbies:
                    for lobby_id in match_lobbies:
                        await channel_layer.group_send(
                            f"lobby_{lobby_id}",
                            {
                                'type': 'player_accepted',
                                'accepted_count': accepted_count,
                                'total_players': total_players,
                                'timeout_seconds': timeout_seconds
                            }
                        )
                    
                    logger.info(
                        f"Player acceptance update sent to ALL {len(match_lobbies)} lobbies: "
                        f"{accepted_count}/{total_players} accepted"
                    )
                else:
                    logger.warning(f"Could not determine match lobbies for player {player_puuid}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in match_system accept_match orchestration: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': f'Failed to accept match: {str(e)}'
            }
    
    @staticmethod
    async def decline_match(match_id: str, player_puuid: str) -> Dict:
        """
        Decline match for a player.
        
        Args:
            match_id: Match confirmation ID
            player_puuid: Player's PUUID
            
        Returns:
            Dict with decline status
        """
        try:
            # Import old manager for business logic
            from matchmaking.match_confirmation import MatchConfirmationManager as OldManager
            
            # Call old manager (which already handles broadcasting)
            result = await OldManager.decline_match(match_id, player_puuid)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in match_system decline_match orchestration: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to decline match: {str(e)}'
            }
    
    @staticmethod
    async def get_match_data(match_confirmation_id: str) -> Dict:
        """
        Get match data.
        
        Args:
            match_confirmation_id: Match confirmation ID
            
        Returns:
            Dict with match data
        """
        try:
            from matchmaking.match_confirmation import MatchConfirmationManager as OldManager
            return await OldManager.get_match_data(match_confirmation_id)
        except Exception as e:
            logger.error(f"Error getting match data: {str(e)}")
            return None
