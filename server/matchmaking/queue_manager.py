"""
Queue Manager Service
Handles all matchmaking queue operations using Redis sorted sets.
"""

from django_redis import get_redis_connection
from django.apps import apps
from django.utils import timezone
from asgiref.sync import sync_to_async
from typing import Dict, List, Tuple, Optional
import logging
import json

from .match_state_validator import MatchStateValidator

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages matchmaking queue using Redis sorted sets.
    Lobbies are scored by average ELO for efficient range queries.
    """
    
    # Redis keys
    QUEUE_KEY_TEMPLATE = "matchmaking:queue:{queue_type}"
    LOBBY_DATA_KEY_TEMPLATE = "matchmaking:lobby_data:{lobby_id}"
    QUEUE_TIME_KEY_TEMPLATE = "matchmaking:queue_time:{lobby_id}"
    
    # Queue settings
    DEFAULT_QUEUE_TYPE = 'pug'
    QUEUE_TTL = 3600  # 1 hour max queue time
    LOBBY_DATA_TTL = 3600  # 1 hour
    
    @staticmethod
    def get_redis():
        """Get Redis connection"""
        return get_redis_connection("default")
    
    @staticmethod
    async def enqueue_lobby(lobby_id: str, lobby_data: Dict, queue_type: str = DEFAULT_QUEUE_TYPE) -> Dict:
        """
        Add a lobby to the matchmaking queue.
        
        Args:
            lobby_id: UUID of the lobby
            lobby_data: Lobby information (from LobbyManager.serialize_lobby)
            queue_type: Type of queue ('pug', 'scrim', etc.)
            
        Returns:
            Dict with status and queue information
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Validate lobby data
            if not lobby_data.get('average_elo'):
                return {
                    'status': 'error',
                    'message': 'Lobby must have average ELO calculated'
                }
            
            # Check if lobby is already in queue
            if redis_conn.zscore(queue_key, lobby_id):
                return {
                    'status': 'error',
                    'message': 'Lobby is already in queue'
                }
            
            # Validate that all players in lobby can queue (not in active matches)
            validation_result = await MatchStateValidator.can_lobby_queue(lobby_id)
            if not validation_result['can_queue']:
                blocked_players = validation_result['blocked_players']
                reasons = validation_result['reasons']
                
                # Create detailed error message
                player_details = []
                for puuid in blocked_players:
                    reason = reasons.get(puuid, 'Unknown reason')
                    player_details.append(f"{puuid}: {reason}")
                
                return {
                    'status': 'error',
                    'message': 'Some players are in active matches and cannot queue',
                    'blocked_players': blocked_players,
                    'reasons': reasons,
                    'active_matches': validation_result['active_matches'],
                    'details': player_details
                }
            
            # Add lobby to sorted set with ELO as score
            average_elo = lobby_data['average_elo']
            redis_conn.zadd(queue_key, {lobby_id: average_elo})
            
            # Store lobby data
            lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
            redis_conn.setex(
                lobby_data_key,
                QueueManager.LOBBY_DATA_TTL,
                json.dumps(lobby_data)
            )
            
            # Store queue entry time
            queue_time_key = QueueManager.QUEUE_TIME_KEY_TEMPLATE.format(lobby_id=lobby_id)
            redis_conn.setex(
                queue_time_key,
                QueueManager.QUEUE_TTL,
                timezone.now().isoformat()
            )
            
            # Get queue stats
            queue_stats = await QueueManager.get_queue_stats(queue_type)
            
            logger.info(f"Lobby {lobby_id} added to {queue_type} queue at ELO {average_elo}")
            
            return {
                'status': 'success',
                'message': 'Lobby added to queue',
                'queue_type': queue_type,
                'queue_position': queue_stats['total_lobbies'],
                'estimated_wait': queue_stats['estimated_wait'],
                'players_in_queue': queue_stats['total_players']
            }
            
        except Exception as e:
            logger.error(f"Error enqueueing lobby: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to enqueue lobby: {str(e)}'
            }
    
    @staticmethod
    async def dequeue_lobby(lobby_id: str, queue_type: str = DEFAULT_QUEUE_TYPE) -> Dict:
        """
        Remove a lobby from the matchmaking queue.
        
        Args:
            lobby_id: UUID of the lobby
            queue_type: Type of queue
            
        Returns:
            Dict with status
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Remove from queue
            removed = redis_conn.zrem(queue_key, lobby_id)
            
            if not removed:
                return {
                    'status': 'error',
                    'message': 'Lobby not found in queue'
                }
            
            # Clean up lobby data
            lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
            queue_time_key = QueueManager.QUEUE_TIME_KEY_TEMPLATE.format(lobby_id=lobby_id)
            redis_conn.delete(lobby_data_key, queue_time_key)
            
            logger.info(f"Lobby {lobby_id} removed from {queue_type} queue")
            
            return {
                'status': 'success',
                'message': 'Lobby removed from queue'
            }
            
        except Exception as e:
            logger.error(f"Error dequeuing lobby: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to dequeue lobby: {str(e)}'
            }
    
    @staticmethod
    async def get_queue_stats(queue_type: str = DEFAULT_QUEUE_TYPE) -> Dict:
        """
        Get current queue statistics.
        
        Args:
            queue_type: Type of queue
            
        Returns:
            Dict with queue statistics
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Get number of lobbies in queue
            total_lobbies = redis_conn.zcard(queue_key)
            
            # Get all lobbies to count total players
            lobby_ids = redis_conn.zrange(queue_key, 0, -1)
            total_players = 0
            
            for lobby_id in lobby_ids:
                lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(
                    lobby_id=lobby_id.decode()
                )
                lobby_data_json = redis_conn.get(lobby_data_key)
                if lobby_data_json:
                    lobby_data = json.loads(lobby_data_json)
                    total_players += lobby_data.get('size', 0)
            
            # Estimate wait time based on queue size
            # Rough estimate: 1 match every 30 seconds with full queue
            estimated_wait = min(total_lobbies * 15, 300)  # Max 5 minutes estimate
            
            return {
                'total_lobbies': total_lobbies,
                'total_players': total_players,
                'estimated_wait': estimated_wait,
                'queue_type': queue_type
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            return {
                'total_lobbies': 0,
                'total_players': 0,
                'estimated_wait': 0,
                'queue_type': queue_type
            }
    
    @staticmethod
    async def get_lobbies_in_range(
        target_elo: float,
        elo_range: int,
        queue_type: str = DEFAULT_QUEUE_TYPE,
        exclude_ids: List[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Get lobbies within ELO range of target.
        
        Args:
            target_elo: Target ELO to search around
            elo_range: +/- range from target
            queue_type: Type of queue
            exclude_ids: Lobby IDs to exclude from results
            
        Returns:
            List of (lobby_id, elo) tuples
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            min_elo = target_elo - elo_range
            max_elo = target_elo + elo_range
            
            # Get lobbies in range
            lobbies = redis_conn.zrangebyscore(
                queue_key,
                min_elo,
                max_elo,
                withscores=True
            )
            
            # Filter out excluded IDs
            if exclude_ids:
                exclude_set = set(exclude_ids)
                lobbies = [
                    (lobby_id, elo)
                    for lobby_id, elo in lobbies
                    if lobby_id.decode() not in exclude_set
                ]
            else:
                lobbies = [(lobby_id.decode(), elo) for lobby_id, elo in lobbies]
            
            return lobbies
            
        except Exception as e:
            logger.error(f"Error getting lobbies in range: {str(e)}")
            return []
    
    @staticmethod
    async def get_lobby_data(lobby_id: str) -> Optional[Dict]:
        """
        Get stored lobby data from Redis.
        
        Args:
            lobby_id: UUID of the lobby
            
        Returns:
            Lobby data dict or None if not found
        """
        try:
            redis_conn = QueueManager.get_redis()
            lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
            
            lobby_data_json = redis_conn.get(lobby_data_key)
            if not lobby_data_json:
                return None
            
            return json.loads(lobby_data_json)
            
        except Exception as e:
            logger.error(f"Error getting lobby data: {str(e)}")
            return None
    
    @staticmethod
    async def get_lobby_queue_time(lobby_id: str) -> Optional[str]:
        """
        Get when lobby joined queue.
        
        Args:
            lobby_id: UUID of the lobby
            
        Returns:
            ISO format timestamp or None
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_time_key = QueueManager.QUEUE_TIME_KEY_TEMPLATE.format(lobby_id=lobby_id)
            
            queue_time = redis_conn.get(queue_time_key)
            if not queue_time:
                return None
            
            return queue_time.decode()
            
        except Exception as e:
            logger.error(f"Error getting lobby queue time: {str(e)}")
            return None
    
    @staticmethod
    async def get_all_queued_lobbies(queue_type: str = DEFAULT_QUEUE_TYPE) -> List[Dict]:
        """
        Get all lobbies in queue with their data.
        
        Args:
            queue_type: Type of queue
            
        Returns:
            List of lobby data dicts with queue info
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Get all lobbies with scores
            lobbies_with_scores = redis_conn.zrange(queue_key, 0, -1, withscores=True)
            
            result = []
            for lobby_id_bytes, elo in lobbies_with_scores:
                lobby_id = lobby_id_bytes.decode()
                
                # Get lobby data
                lobby_data = await QueueManager.get_lobby_data(lobby_id)
                if not lobby_data:
                    continue
                
                # Get queue time
                queue_time = await QueueManager.get_lobby_queue_time(lobby_id)
                
                # Add queue metadata
                lobby_data['queue_elo'] = elo
                lobby_data['queued_at'] = queue_time
                
                result.append(lobby_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all queued lobbies: {str(e)}")
            return []
    
    @staticmethod
    async def join_queue(lobby_id: str, requester_puuid: str, queue_type: str = DEFAULT_QUEUE_TYPE) -> Dict:
        """
        Join a lobby to the matchmaking queue (high-level method).
        Applies uncertainty decay for returning players.
        
        Args:
            lobby_id: UUID of the lobby
            requester_puuid: PUUID of the player requesting to join queue
            queue_type: Type of queue ('pug', 'scrim', etc.)
            
        Returns:
            Dict with status and queue information
        """
        try:
            # Get lobby data from database
            Lobby = apps.get_model('scrimgg', 'Lobby')
            Player = apps.get_model('scrimgg', 'Player')
            
            def get_lobby_and_leader():
                lobby = Lobby.objects.select_related('lobby_leader').get(id=lobby_id)
                leader = Player.objects.get(puuid=requester_puuid)
                return lobby, leader
            
            lobby, leader = await sync_to_async(get_lobby_and_leader)()
            
            # Apply uncertainty decay for returning player
            await sync_to_async(QueueManager._apply_player_uncertainty_decay)(leader)
            
            # Validate requester is lobby leader
            if lobby.lobby_leader.puuid != requester_puuid:
                return {
                    'status': 'error',
                    'message': 'Only lobby leader can join queue'
                }
            
            # Validate lobby is eligible for queue
            from .lobby_manager import LobbyManager
            validation = await LobbyManager.validate_queue_eligibility(lobby_id)
            
            if not validation.get('eligible', False):
                return {
                    'status': 'error',
                    'message': validation.get('reason', 'Lobby not eligible for queue')
                }
            
            # Serialize lobby data
            lobby_data = await LobbyManager._serialize_lobby(lobby)
            
            # Add to queue
            result = await QueueManager.enqueue_lobby(lobby_id, lobby_data, queue_type)
            
            if result['status'] == 'success':
                # Update lobby in database
                def update_lobby():
                    lobby.in_queue = True
                    lobby.queued_at = timezone.now()
                    lobby.save()
                
                await sync_to_async(update_lobby)()
                
                logger.info(f"Lobby {lobby_id} joined {queue_type} queue")
            
            return result
            
        except Exception as e:
            logger.error(f"Error joining queue: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to join queue: {str(e)}'
            }
    
    @staticmethod
    async def leave_queue(lobby_id: str, requester_puuid: str, queue_type: str = DEFAULT_QUEUE_TYPE) -> Dict:
        """
        Remove a lobby from the matchmaking queue (high-level method).
        
        Args:
            lobby_id: UUID of the lobby
            requester_puuid: PUUID of the player requesting to leave queue
            queue_type: Type of queue ('pug', 'scrim', etc.)
            
        Returns:
            Dict with status information
        """
        try:
            # Get lobby data from database
            Lobby = apps.get_model('scrimgg', 'Lobby')
            
            def get_lobby():
                return Lobby.objects.select_related('lobby_leader').get(id=lobby_id)
            
            lobby = await sync_to_async(get_lobby)()
            
            # Validate requester is lobby leader
            if lobby.lobby_leader.puuid != requester_puuid:
                return {
                    'status': 'error',
                    'message': 'Only lobby leader can leave queue'
                }
            
            # Remove from queue
            result = await QueueManager.dequeue_lobby(lobby_id, queue_type)
            
            if result['status'] == 'success':
                # Update lobby in database
                def update_lobby():
                    lobby.in_queue = False
                    lobby.queued_at = None
                    lobby.save()
                
                await sync_to_async(update_lobby)()
                
                logger.info(f"Lobby {lobby_id} left {queue_type} queue")
            
            return result
            
        except Exception as e:
            logger.error(f"Error leaving queue: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to leave queue: {str(e)}'
            }
    
    @staticmethod
    async def get_queue_status(lobby_id: str, queue_type: str = DEFAULT_QUEUE_TYPE) -> Dict:
        """
        Get queue status for a specific lobby.
        
        Args:
            lobby_id: UUID of the lobby
            queue_type: Type of queue ('pug', 'scrim', etc.)
            
        Returns:
            Dict with queue status information
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Check if lobby is in queue
            score = redis_conn.zscore(queue_key, lobby_id)
            in_queue = score is not None
            
            # Get queue stats
            queue_stats = await QueueManager.get_queue_stats(queue_type)
            
            # Get lobby position if in queue
            position = None
            if in_queue:
                position = redis_conn.zrevrank(queue_key, lobby_id) + 1
            
            # Get queue time
            queue_time = await QueueManager.get_lobby_queue_time(lobby_id)
            
            return {
                'status': 'success',
                'lobby_id': lobby_id,
                'in_queue': in_queue,
                'queue_position': position,
                'queue_size': queue_stats['total_lobbies'],
                'estimated_wait': queue_stats['estimated_wait'],
                'queue_time': queue_time
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to get queue status: {str(e)}'
            }
    
    @staticmethod
    async def cleanup_expired_lobbies(queue_type: str = DEFAULT_QUEUE_TYPE) -> int:
        """
        Remove lobbies that have expired from queue.
        
        Args:
            queue_type: Type of queue
            
        Returns:
            Number of lobbies removed
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Get all lobby IDs
            lobby_ids = redis_conn.zrange(queue_key, 0, -1)
            
            removed = 0
            for lobby_id_bytes in lobby_ids:
                lobby_id = lobby_id_bytes.decode()
                
                # Check if lobby data still exists (has TTL)
                lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
                if not redis_conn.exists(lobby_data_key):
                    # Lobby data expired, remove from queue
                    redis_conn.zrem(queue_key, lobby_id)
                    removed += 1
                    logger.info(f"Removed expired lobby {lobby_id} from queue")
            
            return removed
            
        except Exception as e:
            logger.error(f"Error cleaning up expired lobbies: {str(e)}")
            return 0
    
    @staticmethod
    async def _clear_queue(queue_type: str = DEFAULT_QUEUE_TYPE) -> int:
        """
        Clear all lobbies from queue (for testing purposes).
        
        Args:
            queue_type: Type of queue to clear
            
        Returns:
            Number of lobbies removed
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Get all lobby IDs in queue
            lobby_ids = redis_conn.zrange(queue_key, 0, -1)
            
            if not lobby_ids:
                return 0
            
            # Remove all lobby data and queue entries
            removed_count = 0
            
            for lobby_id_bytes in lobby_ids:
                lobby_id = lobby_id_bytes.decode('utf-8')
                
                # Remove lobby data
                lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
                redis_conn.delete(lobby_data_key)
                
                # Remove queue time
                queue_time_key = QueueManager.QUEUE_TIME_KEY_TEMPLATE.format(lobby_id=lobby_id)
                redis_conn.delete(queue_time_key)
                
                removed_count += 1
            
            # Clear the queue
            redis_conn.delete(queue_key)
            
            logger.info(f"Cleared {removed_count} lobbies from {queue_type} queue")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error clearing queue: {str(e)}")
            return 0
    
    @staticmethod
    def _apply_player_uncertainty_decay(player):
        """
        Apply uncertainty decay for returning players.
        Called when player joins queue after absence.
        
        Args:
            player: Player object (Django model)
        """
        import time
        from .trueskill_manager import apply_uncertainty_decay
        
        if player.last_game_timestamp == 0:
            # First time playing, set timestamp
            player.last_game_timestamp = time.time()
            player.save()
            return
        
        # Calculate days since last game
        current_time = time.time()
        seconds_since_last = current_time - player.last_game_timestamp
        days_since_last = seconds_since_last / 86400
        
        # Apply decay if needed (>= 14 days)
        if days_since_last >= 14:
            old_sigma = player.trueskill_sigma
            new_sigma, multiplier = apply_uncertainty_decay(player.trueskill_sigma, days_since_last)
            
            player.trueskill_sigma = new_sigma
            player.is_settled = new_sigma < 3.0
            
            logger.info(f"[DECAY] Player {player.alias} returned after {days_since_last:.1f} days")
            logger.info(f"[DECAY] Sigma: {old_sigma:.2f} -> {new_sigma:.2f} (x{multiplier:.2f})")
            
            player.save()
    
    # ============================================================================
    # SYNCHRONOUS METHODS FOR CELERY TASKS
    # ============================================================================
    
    @staticmethod
    def get_queue_stats_sync(queue_type: str = DEFAULT_QUEUE_TYPE) -> Dict:
        """
        Get current queue statistics - SYNC version for Celery tasks.
        
        Returns:
            Dict with queue stats
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Get total lobbies
            total_lobbies = redis_conn.zcard(queue_key)
            
            # Get all lobby data to count players
            total_players = 0
            lobby_ids = redis_conn.zrange(queue_key, 0, -1)
            
            for lobby_id_bytes in lobby_ids:
                lobby_id = lobby_id_bytes.decode('utf-8') if isinstance(lobby_id_bytes, bytes) else lobby_id_bytes
                lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
                lobby_data_json = redis_conn.get(lobby_data_key)
                
                if lobby_data_json:
                    # Decode if bytes
                    data_str = lobby_data_json.decode('utf-8') if isinstance(lobby_data_json, bytes) else lobby_data_json
                    lobby_data = json.loads(data_str)
                    total_players += len(lobby_data.get('players', []))
            
            return {
                'total_lobbies': total_lobbies,
                'total_players': total_players,
                'queue_type': queue_type
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats (sync): {str(e)}")
            return {
                'total_lobbies': 0,
                'total_players': 0,
                'queue_type': queue_type
            }
    
    @staticmethod
    def get_all_queued_lobbies_sync(queue_type: str = DEFAULT_QUEUE_TYPE) -> List[Dict]:
        """
        Get all lobbies currently in queue - SYNC version for Celery tasks.
        
        Returns:
            List of lobby data dicts
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Get all lobby IDs from sorted set
            lobby_ids = redis_conn.zrange(queue_key, 0, -1, withscores=True)
            
            lobbies = []
            for lobby_id_bytes, queue_time in lobby_ids:
                lobby_id = lobby_id_bytes.decode('utf-8') if isinstance(lobby_id_bytes, bytes) else lobby_id_bytes
                
                # Get lobby data
                lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
                lobby_data_json = redis_conn.get(lobby_data_key)
                
                if lobby_data_json:
                    # Decode if bytes
                    data_str = lobby_data_json.decode('utf-8') if isinstance(lobby_data_json, bytes) else lobby_data_json
                    lobby_data = json.loads(data_str)
                    lobby_data['queue_time'] = queue_time
                    lobbies.append(lobby_data)
            
            return lobbies
            
        except Exception as e:
            logger.error(f"Error getting queued lobbies (sync): {str(e)}")
            return []
    
    @staticmethod
    def cleanup_expired_lobbies_sync() -> int:
        """
        Remove expired lobbies from all queues - SYNC version for Celery tasks.
        
        Returns:
            Number of lobbies cleaned up
        """
        try:
            redis_conn = QueueManager.get_redis()
            cleaned = 0
            
            # Check all queue types
            for queue_type in [QueueManager.DEFAULT_QUEUE_TYPE]:
                queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
                current_time = timezone.now().timestamp()
                
                # Get all lobbies in queue
                lobby_entries = redis_conn.zrange(queue_key, 0, -1)
                
                for lobby_id_bytes in lobby_entries:
                    lobby_id = lobby_id_bytes.decode('utf-8') if isinstance(lobby_id_bytes, bytes) else lobby_id_bytes
                    
                    # Get the actual queue time for this lobby
                    queue_time_key = QueueManager.QUEUE_TIME_KEY_TEMPLATE.format(lobby_id=lobby_id)
                    queue_time_str = redis_conn.get(queue_time_key)
                    
                    if not queue_time_str:
                        # No queue time found, consider it expired
                        queue_time = 0
                    else:
                        queue_time = float(queue_time_str)
                    
                    # Check if lobby is expired (> 1 hour in queue)
                    if current_time - queue_time > QueueManager.QUEUE_TTL:
                        # Remove from queue
                        redis_conn.zrem(queue_key, lobby_id)
                        
                        # Remove lobby data
                        lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
                        redis_conn.delete(lobby_data_key)
                        
                        # Remove queue time
                        queue_time_key = QueueManager.QUEUE_TIME_KEY_TEMPLATE.format(lobby_id=lobby_id)
                        redis_conn.delete(queue_time_key)
                        
                        cleaned += 1
                        logger.info(f"Cleaned up expired lobby {lobby_id} from queue")
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired lobbies")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning expired lobbies (sync): {str(e)}")
            return 0
    
    @staticmethod
    def enqueue_lobby_sync(lobby_id: str, lobby_data: Dict, queue_type: str = DEFAULT_QUEUE_TYPE) -> Dict:
        """
        Add a lobby to the matchmaking queue - SYNC version.
        
        Args:
            lobby_id: UUID of the lobby
            lobby_data: Lobby information (from LobbyManager.serialize_lobby)
            queue_type: Type of queue ('pug', 'scrim', etc.)
            
        Returns:
            Dict with status and queue information
        """
        try:
            redis_conn = QueueManager.get_redis()
            queue_key = QueueManager.QUEUE_KEY_TEMPLATE.format(queue_type=queue_type)
            
            # Validate lobby data
            if not lobby_data.get('average_elo'):
                return {
                    'status': 'error',
                    'message': 'Lobby must have average ELO calculated'
                }
            
            # Check if lobby is already in queue
            if redis_conn.zscore(queue_key, lobby_id):
                return {
                    'status': 'error',
                    'message': 'Lobby is already in queue'
                }
            
            # Validate that all players in lobby can queue (not in active matches)
            validation_result = MatchStateValidator.can_lobby_queue_sync(lobby_id)
            if not validation_result['can_queue']:
                blocked_players = validation_result['blocked_players']
                reasons = validation_result['reasons']
                
                # Create detailed error message
                player_details = []
                for puuid in blocked_players:
                    reason = reasons.get(puuid, 'Unknown reason')
                    player_details.append(f"{puuid}: {reason}")
                
                return {
                    'status': 'error',
                    'message': 'Some players are in active matches and cannot queue',
                    'blocked_players': blocked_players,
                    'reasons': reasons,
                    'active_matches': validation_result['active_matches'],
                    'details': player_details
                }
            
            # Add lobby to sorted set with ELO as score
            average_elo = lobby_data['average_elo']
            redis_conn.zadd(queue_key, {lobby_id: average_elo})
            
            # Store lobby data
            lobby_data_key = QueueManager.LOBBY_DATA_KEY_TEMPLATE.format(lobby_id=lobby_id)
            redis_conn.setex(lobby_data_key, QueueManager.LOBBY_DATA_TTL, json.dumps(lobby_data))
            
            # Store queue time
            queue_time_key = QueueManager.QUEUE_TIME_KEY_TEMPLATE.format(lobby_id=lobby_id)
            current_time = timezone.now().timestamp()
            redis_conn.setex(queue_time_key, QueueManager.QUEUE_TTL, str(current_time))
            
            # Get queue position
            queue_position = redis_conn.zrevrank(queue_key, lobby_id) + 1
            total_lobbies = redis_conn.zcard(queue_key)
            
            logger.info(f"Lobby {lobby_id} added to {queue_type} queue (position {queue_position}/{total_lobbies})")
            
            return {
                'status': 'success',
                'message': f'Lobby added to {queue_type} queue',
                'queue_position': queue_position,
                'total_lobbies': total_lobbies,
                'average_elo': average_elo,
                'queue_type': queue_type
            }
            
        except Exception as e:
            logger.error(f"Error adding lobby to queue (sync): {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to add lobby to queue: {str(e)}'
            }

