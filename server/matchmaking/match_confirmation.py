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
            
            # Build lobby data map for requeue (no database queries needed)
            lobby_leaders = {}
            full_lobby_data = {}  # Store complete lobby data for requeue
            
            # Extract from match_lobbies if available
            if 'match_lobbies' in match_data:
                for lobby in match_data['match_lobbies']:
                    lobby_id = lobby.get('id')
                    players = lobby.get('players', [])
                    if lobby_id and players:
                        # Store leader PUUID
                        lobby_leaders[lobby_id] = players[0]['puuid']
                        
                        # Store full lobby data for requeue
                        full_lobby_data[lobby_id] = {
                            'id': lobby_id,
                            'players': players,
                            'size': lobby.get('size', len(players)),
                            'average_elo': lobby.get('average_elo', 0),
                            'average_mmr': lobby.get('average_mmr', 0),
                            'map_preferences': lobby.get('map_preferences', []),
                            'server_preferences': lobby.get('server_preferences', []),
                            'queued_at': lobby.get('queued_at', timezone.now().isoformat())
                        }
            
            # Fallback to lobby1/lobby2 format
            elif 'lobby1' in match_data and 'lobby2' in match_data:
                for lobby_key in ['lobby1', 'lobby2']:
                    lobby = match_data[lobby_key]
                    lobby_id = lobby.get('id')
                    players = lobby.get('players', [])
                    if lobby_id and players:
                        lobby_leaders[lobby_id] = players[0]['puuid']
                        full_lobby_data[lobby_id] = {
                            'id': lobby_id,
                            'players': players,
                            'size': len(players),
                            'average_elo': lobby.get('average_elo', 0),
                            'average_mmr': lobby.get('average_mmr', 0),
                            'map_preferences': match_data.get('map_pool', []),
                            'server_preferences': match_data.get('server_pool', []),
                            'queued_at': timezone.now().isoformat()
                        }
            
            # Store match data
            data_key = MatchConfirmationManager.MATCH_DATA_KEY.format(base=base_key)
            match_data['match_id'] = match_id
            match_data['initiated_at'] = timezone.now().isoformat()
            match_data['lobby_leaders'] = lobby_leaders  # For identifying leaders
            match_data['full_lobby_data'] = full_lobby_data  # For requeue without DB
            redis_conn.setex(
                data_key,
                MatchConfirmationManager.MATCH_DATA_TTL,
                json.dumps(match_data)
            )
            
            logger.debug(f"Stored complete data for {len(lobby_leaders)} lobbies (requeue ready, no DB needed)")
            
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
            
            # Ensure TTL is set (Redis doesn't preserve TTL when adding to empty set)
            redis_conn.expire(accepted_key, MatchConfirmationManager.MATCH_DATA_TTL)
            
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
            
            # Find all match confirmation data keys (search for :data suffix)
            base_pattern = MatchConfirmationManager.MATCH_KEY_TEMPLATE.format(match_id="*")
            data_pattern = MatchConfirmationManager.MATCH_DATA_KEY.format(base=base_pattern)
            # This creates: match_confirmation:*:data
            
            data_keys = redis_conn.keys(data_pattern)
            
            active_confirmations = []
            
            for data_key_bytes in data_keys:
                data_key = data_key_bytes.decode('utf-8')
                # Extract match_id from key like "match_confirmation:UUID:data"
                match_id = data_key.split(':')[1]
                
                # Get match data
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
            
            logger.info(f"[EXPIRATION CHECK] Match {match_id[:8]}...")
            
            if not match_data:
                logger.info(f"  No match data found - returning True (expired)")
                return True  # Match doesn't exist, consider it expired
            
            try:
                match_info = json.loads(match_data)
                initiated_at = match_info.get('initiated_at')  # Fixed: was 'created_at'
                
                logger.info(f"  initiated_at (from Redis): {initiated_at}")
                
                if initiated_at:
                    from datetime import datetime
                    initiated_time = datetime.fromisoformat(initiated_at.replace('Z', '+00:00'))
                    now = timezone.now()
                    
                    # Check if more than ACCEPTANCE_TIMEOUT seconds have passed
                    time_diff = (now - initiated_time).total_seconds()
                    
                    # DEBUG LOGGING
                    logger.info(f"  initiated_time (parsed): {initiated_time}")
                    logger.info(f"  initiated_time.tzinfo: {initiated_time.tzinfo}")
                    logger.info(f"  now: {now}")
                    logger.info(f"  now.tzinfo: {now.tzinfo}")
                    logger.info(f"  time_diff: {time_diff} seconds")
                    logger.info(f"  ACCEPTANCE_TIMEOUT: {MatchConfirmationManager.ACCEPTANCE_TIMEOUT}")
                    logger.info(f"  time_diff > ACCEPTANCE_TIMEOUT: {time_diff} > {MatchConfirmationManager.ACCEPTANCE_TIMEOUT} = {time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT}")
                    logger.info(f"  RESULT: {'EXPIRED' if time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT else 'NOT EXPIRED'}")
                    
                    return time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT
                
                logger.info(f"  No initiated_at field - returning True (expired)")
                return True  # No initiation time, consider expired
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"  Error parsing match data for {match_id}: {e} - returning True (expired)")
                return True
            
        except Exception as e:
            logger.error(f"  Error checking if match expired: {str(e)} - returning True (expired)")
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
            
            # Get affected lobbies and accepting players
            lobbies = await MatchConfirmationManager.get_match_lobbies(match_id)
            accepting_players = await MatchConfirmationManager.get_accepting_players(match_id)
            
            # Cancel the match
            cancel_result = await MatchConfirmationManager.cancel_match(match_id, 'Match confirmation timed out')
            
            if cancel_result['status'] == 'cancelled':
                # Get full lobby data from match confirmation
                full_lobby_data = match_data.get('full_lobby_data', {})
                
                if not full_lobby_data:
                    logger.warning(f"   No lobby data found in match confirmation, cannot requeue")
                else:
                    logger.info(f"   Found complete data for {len(full_lobby_data)} lobbies")
                    
                    # Determine which lobbies to requeue (only those with 100% acceptance)
                    lobbies_to_requeue = []
                    skipped_lobbies = []
                    
                    for lobby_id in lobbies:
                        lobby_data = full_lobby_data.get(lobby_id)
                        
                        if not lobby_data:
                            logger.warning(f"   No data for lobby {lobby_id[:8]}..., skipping")
                            skipped_lobbies.append(lobby_id)
                            continue
                        
                        # Get all players in this lobby
                        lobby_players = lobby_data.get('players', [])
                        lobby_player_puuids = [p['puuid'] for p in lobby_players]
                        
                        # Check if ALL players in this lobby accepted
                        all_players_accepted = all(puuid in accepting_players for puuid in lobby_player_puuids)
                        
                        if all_players_accepted:
                            lobbies_to_requeue.append(lobby_id)
                            logger.info(f"   ✅ Lobby {lobby_id[:8]}... - ALL {len(lobby_player_puuids)} player(s) accepted → Will requeue")
                        else:
                            accepting_count = sum(1 for puuid in lobby_player_puuids if puuid in accepting_players)
                            skipped_lobbies.append(lobby_id)
                            logger.info(f"   ❌ Lobby {lobby_id[:8]}... - Only {accepting_count}/{len(lobby_player_puuids)} player(s) accepted → Will NOT requeue")
                    
                    # Log summary
                    logger.info(f"🔄 Requeuing {len(lobbies_to_requeue)}/{len(lobbies)} lobbies (only those with 100% acceptance)")
                    if skipped_lobbies:
                        logger.info(f"   Skipped {len(skipped_lobbies)} lobbies due to incomplete acceptance")
                    
                    # Requeue only the qualifying lobbies
                    from .queue_manager import QueueManager
                    requeued_lobbies = []
                    
                    for lobby_id in lobbies_to_requeue:
                        try:
                            lobby_data = full_lobby_data.get(lobby_id)
                            
                            logger.debug(f"   Requeuing lobby {lobby_id[:8]}... with stored data")
                            
                            # Enqueue directly using Redis (NO DATABASE CALLS)
                            requeue_result = await QueueManager.enqueue_lobby(lobby_id, lobby_data, queue_type='pug')
                            
                            if requeue_result['status'] == 'success':
                                requeued_lobbies.append(lobby_id)
                                logger.info(f"   ✅ Lobby {lobby_id[:8]}... back in queue (position: {requeue_result.get('queue_position', 'N/A')})")
                                
                                # Queue background task to update database (non-blocking)
                                from .tasks import update_lobby_queue_status_task
                                update_lobby_queue_status_task.apply_async(
                                    args=[lobby_id, True],  # in_queue=True
                                    queue='celery'
                                )
                            else:
                                logger.warning(f"   ❌ Failed to requeue lobby {lobby_id[:8]}: {requeue_result.get('message')}")
                                
                        except Exception as e:
                            logger.error(f"   Error requeuing lobby {lobby_id[:8]}: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                
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

