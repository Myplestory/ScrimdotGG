"""
Match Confirmation Manager
Handles 30-second match acceptance flow and player tracking.
"""

from django_redis import get_redis_connection
from django.utils import timezone
from typing import Dict, List, Set, Optional
import logging
import uuid
import json

logger = logging.getLogger(__name__)


class MatchConfirmationManager:
    """
    Manages match confirmation/acceptance phase.
    All 10 players must accept within 30 seconds or match is cancelled.
    """
    
    # Redis keys
    MATCH_KEY_TEMPLATE = "match_confirmation:{match_id}"
    NOTIFIED_PLAYERS_KEY = "{base}:notified"
    ACCEPTED_PLAYERS_KEY = "{base}:accepted"
    MATCH_DATA_KEY = "{base}:data"
    LOBBIES_KEY = "{base}:lobbies"
    
    # Timeouts
    ACCEPTANCE_TIMEOUT = 30  # seconds
    MATCH_DATA_TTL = 300  # 5 minutes
    
    @staticmethod
    def get_redis():
        """Get Redis connection"""
        return get_redis_connection("default")
    
    @staticmethod
    async def initiate_confirmation(match_data: Dict) -> str:
        """
        Initiate match confirmation phase.
        
        Args:
            match_data: Match data from Matchmaker (either team-based or lobby-based format)
            
        Returns:
            Match confirmation ID
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            
            # Generate unique match confirmation ID
            match_id = str(uuid.uuid4())
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            # Get all player PUUIDs (handle both formats)
            all_players = []
            
            # Check if it's team-based format (original) or lobby-based format (converted)
            if 'team_a' in match_data and 'team_b' in match_data:
                # Original team-based format
                all_players.extend([p['puuid'] for p in match_data['team_a']['players']])
                all_players.extend([p['puuid'] for p in match_data['team_b']['players']])
            elif 'lobby1' in match_data and 'lobby2' in match_data:
                # Converted lobby-based format
                all_players.extend([p['puuid'] for p in match_data['lobby1']['players']])
                all_players.extend([p['puuid'] for p in match_data['lobby2']['players']])
            else:
                raise ValueError("Invalid match data format - must have either team_a/team_b or lobby1/lobby2")
            
            # Store notified players
            notified_key = MatchConfirmationManager.NOTIFIED_PLAYERS_KEY.format(base=base_key)
            redis_conn.sadd(notified_key, *all_players)
            redis_conn.expire(notified_key, MatchConfirmationManager.MATCH_DATA_TTL)
            
            # Initialize accepted players (empty)
            accepted_key = MatchConfirmationManager.ACCEPTED_PLAYERS_KEY.format(base=base_key)
            redis_conn.expire(accepted_key, MatchConfirmationManager.ACCEPTANCE_TIMEOUT)
            
            # Store match data
            data_key = MatchConfirmationManager.MATCH_DATA_KEY.format(base=base_key)
            match_data['match_id'] = match_id
            match_data['initiated_at'] = timezone.now().isoformat()
            redis_conn.setex(
                data_key,
                MatchConfirmationManager.MATCH_DATA_TTL,
                json.dumps(match_data)
            )
            
            # Store lobby IDs (handle both formats)
            lobbies_key = MatchConfirmationManager.LOBBIES_KEY.format(base=base_key)
            if 'lobbies' in match_data:
                # Original format with lobbies list
                redis_conn.sadd(lobbies_key, *match_data['lobbies'])
            elif 'lobby1' in match_data and 'lobby2' in match_data:
                # Converted format with lobby1/lobby2
                redis_conn.sadd(lobbies_key, match_data['lobby1']['id'], match_data['lobby2']['id'])
            else:
                raise ValueError("Cannot determine lobby IDs from match data")
            redis_conn.expire(lobbies_key, MatchConfirmationManager.MATCH_DATA_TTL)
            
            logger.info(f"Match confirmation initiated: {match_id} with {len(all_players)} players")
            
            return match_id
            
        except Exception as e:
            logger.error(f"Error initiating match confirmation: {str(e)}")
            raise
    
    @staticmethod
    async def accept_match(match_id: str, player_puuid: str) -> Dict:
        """
        Accept match for a player (main method called by consumer).
        
        Args:
            match_id: Match confirmation ID
            player_puuid: Player's PUUID
            
        Returns:
            Dict with acceptance status and all required fields for consumer
        """
        try:
            # Mark the acceptance
            acceptance_result = await MatchConfirmationManager.mark_acceptance(match_id, player_puuid)
            
            if acceptance_result['status'] != 'success':
                return acceptance_result
            
            # Get additional data needed for consumer
            accepted_count = acceptance_result['accepted_count']
            total_players = acceptance_result['total_count']
            all_accepted = acceptance_result['all_accepted']
            
            # Get player's lobby ID
            lobby_id = await MatchConfirmationManager._get_player_lobby_id(player_puuid)
            
            # Calculate timeout seconds remaining
            timeout_seconds = await MatchConfirmationManager._get_timeout_remaining(match_id)
            
            # Get all lobbies involved in this match
            match_lobbies = await MatchConfirmationManager.get_match_lobbies(match_id)
            
            result = {
                'status': 'success',
                'message': 'Match accepted',
                'match_confirmed': all_accepted,
                'accepted_count': accepted_count,
                'total_players': total_players,
                'timeout_seconds': timeout_seconds,
                'match_id': match_id,
                'lobby_id': lobby_id,
                'match_lobbies': match_lobbies
            }
            
            logger.info(f"Player {player_puuid} accepted match {match_id}: {accepted_count}/{total_players} accepted, {timeout_seconds}s remaining")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in accept_match: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to accept match: {str(e)}'
            }

    @staticmethod
    async def mark_acceptance(match_id: str, player_puuid: str) -> Dict:
        """
        Mark player as having accepted the match.
        
        Args:
            match_id: Match confirmation ID
            player_puuid: Player's PUUID
            
        Returns:
            Dict with acceptance status
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            notified_key = MatchConfirmationManager.NOTIFIED_PLAYERS_KEY.format(base=base_key)
            accepted_key = MatchConfirmationManager.ACCEPTED_PLAYERS_KEY.format(base=base_key)
            
            # Check if player was notified for this match
            if not redis_conn.sismember(notified_key, player_puuid):
                return {
                    'status': 'error',
                    'message': 'Player not part of this match'
                }
            
            # Check if already accepted
            if redis_conn.sismember(accepted_key, player_puuid):
                return {
                    'status': 'info',
                    'message': 'Player already accepted'
                }
            
            # Mark as accepted
            redis_conn.sadd(accepted_key, player_puuid)
            
            # Get acceptance counts
            total_players = redis_conn.scard(notified_key)
            accepted_count = redis_conn.scard(accepted_key)
            
            logger.info(f"Player {player_puuid} accepted match {match_id} ({accepted_count}/{total_players})")
            
            return {
                'status': 'success',
                'message': 'Match accepted',
                'accepted_count': accepted_count,
                'total_count': total_players,
                'all_accepted': accepted_count == total_players
            }
            
        except Exception as e:
            logger.error(f"Error marking acceptance: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to mark acceptance: {str(e)}'
            }
    
    @staticmethod
    async def check_all_accepted(match_id: str) -> bool:
        """
        Check if all players have accepted the match.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            True if all accepted, False otherwise
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            notified_key = MatchConfirmationManager.NOTIFIED_PLAYERS_KEY.format(base=base_key)
            accepted_key = MatchConfirmationManager.ACCEPTED_PLAYERS_KEY.format(base=base_key)
            
            total_players = redis_conn.scard(notified_key)
            accepted_count = redis_conn.scard(accepted_key)
            
            return total_players > 0 and total_players == accepted_count
            
        except Exception as e:
            logger.error(f"Error checking all accepted: {str(e)}")
            return False
    
    @staticmethod
    async def get_non_accepting_players(match_id: str) -> List[str]:
        """
        Get list of players who haven't accepted.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            List of player PUUIDs
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            notified_key = MatchConfirmationManager.NOTIFIED_PLAYERS_KEY.format(base=base_key)
            accepted_key = MatchConfirmationManager.ACCEPTED_PLAYERS_KEY.format(base=base_key)
            
            all_players = redis_conn.smembers(notified_key)
            accepted_players = redis_conn.smembers(accepted_key)
            
            non_accepting = all_players - accepted_players
            
            return [p.decode() for p in non_accepting]
            
        except Exception as e:
            logger.error(f"Error getting non-accepting players: {str(e)}")
            return []
    
    @staticmethod
    async def get_accepting_players(match_id: str) -> List[str]:
        """
        Get list of players who accepted.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            List of player PUUIDs
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            accepted_key = MatchConfirmationManager.ACCEPTED_PLAYERS_KEY.format(base=base_key)
            
            accepted_players = redis_conn.smembers(accepted_key)
            
            return [p.decode() for p in accepted_players]
            
        except Exception as e:
            logger.error(f"Error getting accepting players: {str(e)}")
            return []
    
    @staticmethod
    async def get_match_lobbies(match_id: str) -> List[str]:
        """
        Get lobby IDs involved in this match.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            List of lobby IDs
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            lobbies_key = MatchConfirmationManager.LOBBIES_KEY.format(base=base_key)
            
            lobbies = redis_conn.smembers(lobbies_key)
            
            return [l.decode() for l in lobbies]
            
        except Exception as e:
            logger.error(f"Error getting match lobbies: {str(e)}")
            return []
    
    @staticmethod
    async def get_match_data(match_id: str) -> Optional[Dict]:
        """
        Get full match data.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            Match data dict or None
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            data_key = MatchConfirmationManager.MATCH_DATA_KEY.format(base=base_key)
            
            match_data_json = redis_conn.get(data_key)
            if not match_data_json:
                return None
            
            return json.loads(match_data_json)
            
        except Exception as e:
            logger.error(f"Error getting match data: {str(e)}")
            return None
    
    @staticmethod
    async def _get_player_lobby_id(player_puuid: str) -> Optional[str]:
        """
        Get the lobby ID for a player.
        
        Args:
            player_puuid: Player's PUUID
            
        Returns:
            Lobby ID or None if not found
        """
        try:
            from django.apps import apps
            from asgiref.sync import sync_to_async
            
            Lobby = apps.get_model('scrimgg', 'Lobby')
            Player = apps.get_model('scrimgg', 'Player')
            
            def get_lobby_id():
                try:
                    player = Player.objects.get(puuid=player_puuid)
                    lobby = Lobby.objects.filter(players=player, is_active=True).first()
                    return lobby.id if lobby else None
                except Player.DoesNotExist:
                    return None
            
            return await sync_to_async(get_lobby_id)()
            
        except Exception as e:
            logger.error(f"Error getting player lobby ID: {str(e)}")
            return None
    
    @staticmethod
    async def _get_timeout_remaining(match_id: str) -> int:
        """
        Calculate remaining timeout seconds for a match.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            Seconds remaining (0 if expired)
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            # Check if match data exists
            data_key = MatchConfirmationManager.MATCH_DATA_KEY.format(base=base_key)
            match_data = redis_conn.get(data_key)
            
            if not match_data:
                return 0  # Match doesn't exist or expired
            
            try:
                match_info = json.loads(match_data)
                initiated_at = match_info.get('initiated_at')
                
                if initiated_at:
                    from datetime import datetime
                    initiated_time = datetime.fromisoformat(initiated_at.replace('Z', '+00:00'))
                    now = timezone.now()
                    
                    # Calculate seconds elapsed
                    time_diff = (now - initiated_time).total_seconds()
                    remaining = max(0, MatchConfirmationManager.ACCEPTANCE_TIMEOUT - time_diff)
                    return int(remaining)
                
                return MatchConfirmationManager.ACCEPTANCE_TIMEOUT  # Default if no timestamp
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Error parsing match data for timeout calculation: {e}")
                return MatchConfirmationManager.ACCEPTANCE_TIMEOUT
            
        except Exception as e:
            logger.error(f"Error calculating timeout remaining: {str(e)}")
            return MatchConfirmationManager.ACCEPTANCE_TIMEOUT
    
    @staticmethod
    async def decline_match(match_id: str, player_puuid: str) -> Dict:
        """
        Decline match for a player.
        
        Args:
            match_id: Match confirmation ID
            player_puuid: Player's PUUID
            
        Returns:
            Dict with decline status and affected lobbies
        """
        try:
            # Get match data before cancellation
            match_data = await MatchConfirmationManager.get_match_data(match_id)
            if not match_data:
                return {
                    'status': 'error',
                    'message': 'Match not found'
                }
            
            # Get affected lobbies
            match_lobbies = await MatchConfirmationManager.get_match_lobbies(match_id)
            
            # Cancel the match
            cancel_result = await MatchConfirmationManager.cancel_match(match_id, 'Player declined match')
            
            if cancel_result['status'] == 'cancelled':
                logger.info(f"Player {player_puuid} declined match {match_id}")
                return {
                    'status': 'success',
                    'message': 'Match declined successfully',
                    'affected_lobbies': match_lobbies,
                    'match_id': match_id
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to cancel match: {cancel_result.get("message")}'
                }
                
        except Exception as e:
            logger.error(f"Error declining match: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to decline match: {str(e)}'
            }
    
    @staticmethod
    async def cancel_match(match_id: str, reason: str = 'timeout') -> Dict:
        """
        Cancel a match confirmation.
        
        Args:
            match_id: Match confirmation ID
            reason: Cancellation reason
            
        Returns:
            Dict with cancellation info
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            # Get data before cleanup
            lobbies = await MatchConfirmationManager.get_match_lobbies(match_id)
            accepting_players = await MatchConfirmationManager.get_accepting_players(match_id)
            non_accepting_players = await MatchConfirmationManager.get_non_accepting_players(match_id)
            
            # Cleanup Redis keys
            notified_key = MatchConfirmationManager.NOTIFIED_PLAYERS_KEY.format(base=base_key)
            accepted_key = MatchConfirmationManager.ACCEPTED_PLAYERS_KEY.format(base=base_key)
            data_key = MatchConfirmationManager.MATCH_DATA_KEY.format(base=base_key)
            lobbies_key = MatchConfirmationManager.LOBBIES_KEY.format(base=base_key)
            
            redis_conn.delete(notified_key, accepted_key, data_key, lobbies_key)
            
            logger.info(f"Match {match_id} cancelled: {reason}")
            
            return {
                'status': 'cancelled',
                'reason': reason,
                'lobbies': lobbies,
                'accepting_players': accepting_players,
                'non_accepting_players': non_accepting_players
            }
            
        except Exception as e:
            logger.error(f"Error cancelling match: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to cancel match: {str(e)}'
            }
    
    @staticmethod
    async def cleanup_match(match_id: str) -> None:
        """
        Clean up match confirmation data after completion.
        
        Args:
            match_id: Match confirmation ID
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            notified_key = MatchConfirmationManager.NOTIFIED_PLAYERS_KEY.format(base=base_key)
            accepted_key = MatchConfirmationManager.ACCEPTED_PLAYERS_KEY.format(base=base_key)
            data_key = MatchConfirmationManager.MATCH_DATA_KEY.format(base=base_key)
            lobbies_key = MatchConfirmationManager.LOBBIES_KEY.format(base=base_key)
            
            redis_conn.delete(notified_key, accepted_key, data_key, lobbies_key)
            
            logger.info(f"Match {match_id} cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up match: {str(e)}")
    
    @staticmethod
    async def get_all_active_confirmations() -> List[Dict]:
        """
        Get all active match confirmations.
        
        Returns:
            List of active match confirmation data
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            
            # Find all match confirmation keys
            pattern = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id="*")
            match_keys = redis_conn.keys(pattern)
            
            active_confirmations = []
            
            for match_key in match_keys:
                match_id = match_key.decode('utf-8').split(':')[-1]
                
                # Get match data
                data_key = MatchConfirmationManager.MATCH_DATA_KEY.format(base=match_key.decode('utf-8'))
                match_data = redis_conn.get(data_key)
                
                if match_data:
                    try:
                        match_info = json.loads(match_data)
                        match_info['id'] = match_id
                        active_confirmations.append(match_info)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON data for match {match_id}")
            
            return active_confirmations
            
        except Exception as e:
            logger.error(f"Error getting active confirmations: {str(e)}")
            return []
    
    @staticmethod
    async def is_match_expired(match_id: str) -> bool:
        """
        Check if a match confirmation has expired.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            True if expired, False otherwise
        """
        try:
            redis_conn = MatchConfirmationManager.get_redis()
            base_key = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id=match_id)
            
            # Check if match data exists
            data_key = MatchConfirmationManager.MATCH_DATA_KEY.format(base=base_key)
            match_data = redis_conn.get(data_key)
            
            if not match_data:
                return True  # Match doesn't exist, consider it expired
            
            try:
                match_info = json.loads(match_data)
                created_at = match_info.get('created_at')
                
                if created_at:
                    from datetime import datetime
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    now = timezone.now()
                    
                    # Check if more than ACCEPTANCE_TIMEOUT seconds have passed
                    time_diff = (now - created_time).total_seconds()
                    return time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT
                
                return True  # No creation time, consider expired
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Error parsing match data for {match_id}: {e}")
                return True
            
        except Exception as e:
            logger.error(f"Error checking if match expired: {str(e)}")
            return True
    
    @staticmethod
    async def handle_expired_match(match_id: str) -> Dict:
        """
        Handle an expired match confirmation.
        
        Args:
            match_id: Match confirmation ID
            
        Returns:
            Result of the expiration handling
        """
        try:
            # Get match data before cleanup
            match_data = await MatchConfirmationManager.get_match_data(match_id)
            
            if not match_data:
                return {
                    'status': 'error',
                    'message': 'Match not found'
                }
            
            # Get affected lobbies
            lobbies = await MatchConfirmationManager.get_match_lobbies(match_id)
            
            # Cancel the match
            cancel_result = await MatchConfirmationManager.cancel_match(match_id, 'Match confirmation timed out')
            
            if cancel_result['status'] == 'cancelled':
                # Requeue the lobbies if they're still eligible
                requeued_lobbies = []
                
                for lobby_id in lobbies:
                    try:
                        # Check if lobby is still eligible for queue
                        from .queue_manager import QueueManager
                        from .lobby_manager import LobbyManager
                        
                        # Get lobby leader
                        Lobby = __import__('django.apps', fromlist=['apps']).apps.get_model('scrimgg', 'Lobby')
                        
                        def get_lobby():
                            return Lobby.objects.select_related('lobby_leader').get(id=lobby_id)
                        
                        from asgiref.sync import sync_to_async
                        lobby = await sync_to_async(get_lobby)()
                        
                        if lobby.lobby_leader:
                            # Try to requeue
                            requeue_result = await QueueManager.join_queue(lobby_id, lobby.lobby_leader.puuid)
                            
                            if requeue_result['status'] == 'success':
                                requeued_lobbies.append(lobby_id)
                                logger.info(f"Requeued lobby {lobby_id} after match timeout")
                            else:
                                logger.warning(f"Failed to requeue lobby {lobby_id}: {requeue_result.get('message')}")
                                
                    except Exception as e:
                        logger.error(f"Error requeuing lobby {lobby_id}: {str(e)}")
                
                return {
                    'status': 'success',
                    'message': 'Expired match handled successfully',
                    'affected_lobbies': lobbies,
                    'requeued_lobbies': requeued_lobbies,
                    'match_id': match_id
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to cancel expired match: {cancel_result.get("message")}'
                }
                
        except Exception as e:
            logger.error(f"Error handling expired match: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to handle expired match: {str(e)}'
            }

