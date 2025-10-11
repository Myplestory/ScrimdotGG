"""
Celery tasks for Scrim.GG matchmaking system
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from .queue_manager import QueueManager
from .matchmaker import Matchmaker
from .matchmaker_v2 import MatchmakerV2  # New MMR-based matchmaker
from .match_confirmation import MatchConfirmationManager

logger = get_task_logger(__name__)

@shared_task(bind=True, name='matchmaking.tasks.periodic_matchmaking')
def periodic_matchmaking(self):
    """
    Periodic task to find matches for lobbies in queue.
    Runs every 30 seconds.
    """
    try:
        logger.info("Starting periodic matchmaking...")
        
        # Get queue statistics
        queue_stats = async_to_sync(QueueManager.get_queue_stats)()
        total_lobbies = queue_stats.get('total_lobbies', 0)
        total_players = queue_stats.get('total_players', 0)
        
        logger.info(f"Queue status: {total_lobbies} lobbies, {total_players} players")
        
        if total_lobbies < 2:
            logger.info("Not enough lobbies in queue for matchmaking")
            return {
                'status': 'success',
                'message': 'Not enough lobbies in queue',
                'lobbies_in_queue': total_lobbies,
                'matches_found': 0
            }
        
        # Run matchmaking algorithm (using MMR-based matchmaker)
        matchmaking_result = async_to_sync(MatchmakerV2.find_matches)()
        
        if matchmaking_result['status'] == 'success':
            matches_found = matchmaking_result.get('matches_found', 0)
            logger.info(f"Matchmaking completed: {matches_found} matches found")
            
            # If matches were found, create match confirmations
            if matches_found > 0:
                matches = matchmaking_result.get('matches', [])
                confirmations_created = 0
                
                for match in matches:
                    try:
                        # Create match confirmation
                        confirmation_id = async_to_sync(
                            MatchConfirmationManager.initiate_confirmation
                        )(match)
                        
                        if confirmation_id:
                            confirmations_created += 1
                            logger.info(f"Created match confirmation: {confirmation_id}")
                            
                            # Send match found notifications to ALL lobbies in the match
                            # (could be 2-10 lobbies depending on party sizes)
                            all_lobby_ids = match.get('lobbies', [])
                            
                            logger.debug(f"Match data keys: {match.keys()}")
                            logger.debug(f"Lobbies field: {all_lobby_ids}")
                            
                            if not all_lobby_ids:
                                # Fallback to lobby1/lobby2 if 'lobbies' field not present
                                all_lobby_ids = [match['lobby1']['id'], match['lobby2']['id']]
                                logger.warning(f"'lobbies' field missing or empty, using fallback: {all_lobby_ids}")
                            
                            logger.info(f"Notifying {len(all_lobby_ids)} lobbies about match {confirmation_id}")
                            
                            for i, lobby_id in enumerate(all_lobby_ids):
                                logger.info(f"Notifying lobby {i+1}/{len(all_lobby_ids)}: {lobby_id}")
                                _notify_match_found(lobby_id, confirmation_id)
                            
                    except Exception as e:
                        logger.error(f"Error creating match confirmation: {str(e)}")
                
                return {
                    'status': 'success',
                    'message': f'Matchmaking completed successfully',
                    'lobbies_in_queue': total_lobbies,
                    'matches_found': matches_found,
                    'confirmations_created': confirmations_created
                }
            else:
                return {
                    'status': 'success',
                    'message': 'No suitable matches found',
                    'lobbies_in_queue': total_lobbies,
                    'matches_found': 0
                }
        else:
            logger.error(f"Matchmaking failed: {matchmaking_result.get('message')}")
            return {
                'status': 'error',
                'message': matchmaking_result.get('message', 'Matchmaking failed'),
                'lobbies_in_queue': total_lobbies,
                'matches_found': 0
            }
            
    except Exception as e:
        logger.error(f"Error in periodic matchmaking: {str(e)}")
        return {
            'status': 'error',
            'message': f'Matchmaking task failed: {str(e)}',
            'lobbies_in_queue': 0,
            'matches_found': 0
        }

@shared_task(bind=True, name='matchmaking.tasks.cleanup_expired_matches')
def cleanup_expired_matches(self):
    """
    Clean up expired match confirmations.
    Runs every 60 seconds.
    """
    try:
        logger.info("Starting cleanup of expired matches...")
        
        # Get all active match confirmations
        active_confirmations = async_to_sync(
            MatchConfirmationManager.get_all_active_confirmations
        )()
        
        expired_count = 0
        processed_count = 0
        
        for confirmation in active_confirmations:
            try:
                processed_count += 1
                
                # Check if match confirmation has expired
                is_expired = async_to_sync(
                    MatchConfirmationManager.is_match_expired
                )(confirmation['id'])
                
                if is_expired:
                    # Handle expired match
                    result = async_to_sync(
                        MatchConfirmationManager.handle_expired_match
                    )(confirmation['id'])
                    
                    if result['status'] == 'success':
                        expired_count += 1
                        logger.info(f"Handled expired match: {confirmation['id']}")
                        
                        # Notify affected lobbies
                        for lobby_id in result.get('affected_lobbies', []):
                            _notify_match_timeout(lobby_id, 'Match confirmation timed out')
                    else:
                        logger.error(f"Failed to handle expired match {confirmation['id']}: {result.get('message')}")
                        
            except Exception as e:
                logger.error(f"Error processing confirmation {confirmation.get('id', 'unknown')}: {str(e)}")
        
        logger.info(f"Cleanup completed: {expired_count} expired matches handled out of {processed_count} processed")
        
        return {
            'status': 'success',
            'message': f'Cleanup completed: {expired_count} expired matches handled',
            'processed_confirmations': processed_count,
            'expired_matches': expired_count
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_matches: {str(e)}")
        return {
            'status': 'error',
            'message': f'Cleanup task failed: {str(e)}',
            'processed_confirmations': 0,
            'expired_matches': 0
        }

@shared_task(bind=True, name='matchmaking.tasks.cleanup_expired_queues')
def cleanup_expired_queues(self):
    """
    Clean up expired lobbies from queue.
    Runs every 5 minutes.
    """
    try:
        logger.info("Starting cleanup of expired queue entries...")
        
        # Clean up expired lobbies from queue
        cleaned_count = async_to_sync(QueueManager.cleanup_expired_lobbies)()
        
        logger.info(f"Queue cleanup completed: {cleaned_count} expired lobbies removed")
        
        return {
            'status': 'success',
            'message': f'Queue cleanup completed: {cleaned_count} expired lobbies removed',
            'cleaned_lobbies': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_queues: {str(e)}")
        return {
            'status': 'error',
            'message': f'Queue cleanup task failed: {str(e)}',
            'cleaned_lobbies': 0
        }

@shared_task(bind=True, name='matchmaking.tasks.manual_matchmaking')
def manual_matchmaking(self):
    """
    Manual matchmaking task that can be triggered on demand.
    """
    logger.info("Manual matchmaking triggered")
    return periodic_matchmaking.delay()

@shared_task(bind=True, name='matchmaking.tasks.notify_match_found')
def notify_match_found_task(self, lobby_id, match_confirmation_id):
    """
    Task to send match found notifications to a specific lobby.
    """
    try:
        _notify_match_found(lobby_id, match_confirmation_id)
        logger.info(f"Sent match found notification to lobby {lobby_id}")
        return {'status': 'success', 'lobby_id': lobby_id}
    except Exception as e:
        logger.error(f"Error sending match found notification: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task(bind=True, name='matchmaking.tasks.notify_match_timeout')
def notify_match_timeout_task(self, lobby_id, reason):
    """
    Task to send match timeout notifications to a specific lobby.
    """
    try:
        _notify_match_timeout(lobby_id, reason)
        logger.info(f"Sent match timeout notification to lobby {lobby_id}")
        return {'status': 'success', 'lobby_id': lobby_id}
    except Exception as e:
        logger.error(f"Error sending match timeout notification: {str(e)}")
        return {'status': 'error', 'message': str(e)}

# Helper functions for WebSocket notifications

def _notify_match_found(lobby_id, match_confirmation_id):
    """
    Send match found notification to lobby via WebSocket.
    """
    try:
        logger.info(f"Attempting to notify lobby {lobby_id} about match {match_confirmation_id}")
        channel_layer = get_channel_layer()
        
        if not channel_layer:
            logger.error("Channel layer is None!")
            return
        
        logger.info(f"Channel layer obtained, sending to group lobby_{lobby_id}")
        
        # Send match found notification
        async_to_sync(channel_layer.group_send)(
            f"lobby_{lobby_id}",
            {
                'type': 'match_found',
                'match_id': match_confirmation_id,  # Add match_id field
                'match_confirmation_id': match_confirmation_id,
                'timeout_seconds': 30,  # 30 second timeout
                'message': 'Match found! Please accept to continue.'
            }
        )
        
        logger.info(f"Sent match found notification to lobby {lobby_id}")
        
    except Exception as e:
        logger.error(f"Error sending match found notification to lobby {lobby_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def _notify_match_timeout(lobby_id, reason):
    """
    Send match timeout notification to lobby via WebSocket.
    """
    try:
        channel_layer = get_channel_layer()
        
        # Send match timeout notification
        async_to_sync(channel_layer.group_send)(
            f"lobby_{lobby_id}",
            {
                'type': 'match_timeout',
                'message': reason,
                'reason': 'timeout'
            }
        )
        
        logger.info(f"Sent match timeout notification to lobby {lobby_id}")
        
    except Exception as e:
        logger.error(f"Error sending match timeout notification: {str(e)}")

# Task monitoring and health check

@shared_task(bind=True, name='matchmaking.tasks.health_check')
def health_check(self):
    """
    Health check task to monitor system status.
    """
    try:
        # Check Redis connection
        queue_stats = async_to_sync(QueueManager.get_queue_stats)()
        
        # Check active match confirmations
        active_confirmations = async_to_sync(
            MatchConfirmationManager.get_all_active_confirmations
        )()
        
        health_status = {
            'status': 'healthy',
            'timestamp': self.request.utc_time,
            'redis_connected': True,
            'queue_stats': queue_stats,
            'active_confirmations': len(active_confirmations),
            'worker_info': {
                'hostname': self.request.hostname,
                'task_id': self.request.id,
                'retries': self.request.retries
            }
        }
        
        logger.info(f"Health check passed: {health_status}")
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'timestamp': self.request.utc_time,
            'error': str(e),
            'redis_connected': False
        }