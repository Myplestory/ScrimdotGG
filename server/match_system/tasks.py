"""
Celery tasks for Match System.
Handles match confirmation, veto timeouts, and state transitions.

MOVED FROM: matchmaking/tasks.py (match-related tasks only)
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import models

from core.websocket_utils import WebSocketBroadcaster
from .models import Match
from .managers import MatchManager, MatchConfirmationManager

logger = get_task_logger(__name__)


@shared_task(bind=True, name='match_system.tasks.cleanup_expired_matches')
def cleanup_expired_matches(self):
    """
    Clean up expired match confirmations.
    Runs every 60 seconds.
    
    SYNC TASK: Uses direct Redis/ORM calls following Celery best practices.
    """
    try:
        logger.info("Starting cleanup of expired matches...")
        
        # Get all active match confirmations (SYNC)
        active_confirmations = MatchConfirmationManager.get_all_active_confirmations_sync()
        
        expired_count = 0
        processed_count = 0
        
        for confirmation in active_confirmations:
            try:
                processed_count += 1
                
                # Check if match confirmation has expired (SYNC)
                is_expired = MatchConfirmationManager.is_match_expired_sync(confirmation['id'])
                
                if is_expired:
                    # Handle expired match (SYNC)
                    result = MatchConfirmationManager.handle_expired_match_sync(confirmation['id'])
                    
                    if result['status'] == 'success':
                        expired_count += 1
                        logger.info(f"Handled expired match: {confirmation['id']}")
                        
                        # Notify affected lobbies
                        for lobby_id in result.get('affected_lobbies', []):
                            WebSocketBroadcaster.broadcast_to_lobby(
                                lobby_id,
                                'match_timeout',
                                {'message': 'Match confirmation timed out', 'reason': 'timeout'}
                            )
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


@shared_task(bind=True, name='match_system.tasks.check_veto_timeouts')
def check_veto_timeouts(self):
    """
    Check for matches with expired deadlines and auto-handle.
    Handles server veto, map veto, and side selection timeouts.
    Runs every 5 seconds.
    
    SYNC TASK: Uses direct ORM calls following Celery best practices.
    """
    try:
        logger.debug("Checking for expired deadlines...")
        
        # Find matches with expired deadlines
        expired_matches = list(Match.objects.filter(
            models.Q(
                state=Match.STATE_SERVER_VETO,
                server_veto_deadline__lt=timezone.now()
            ) | models.Q(
                state=Match.STATE_MAP_VETO,
                veto_deadline__lt=timezone.now()
            ) | models.Q(
                state=Match.STATE_SIDE_SELECTION,
                side_selection_deadline__lt=timezone.now()
            )
        ))
        
        count = len(expired_matches)
        
        if count == 0:
            logger.debug("No expired deadlines found")
            return {
                'status': 'success',
                'expired_count': 0
            }
        
        logger.info(f"Found {count} match(es) with expired deadlines")
        
        processed = 0
        for match in expired_matches:
            try:
                logger.info(f"Processing timeout for match {match.id} (state: {match.state})")
                
                # Handle timeout based on match state
                if match.state == Match.STATE_SERVER_VETO:
                    # Server veto timeout
                    result = MatchManager.handle_server_veto_timeout_sync(match.id)
                    event_type = 'server_veto_timeout'
                elif match.state == Match.STATE_MAP_VETO:
                    # Map veto timeout
                    result = MatchManager.handle_map_veto_timeout_sync(match.id)
                    event_type = 'map_veto_timeout'
                elif match.state == Match.STATE_SIDE_SELECTION:
                    # Side selection timeout
                    result = MatchManager.handle_side_selection_timeout_sync(match.id)
                    event_type = 'side_selection_timeout'
                else:
                    logger.warning(f"Match {match.id} in unexpected state for timeout: {match.state}")
                    continue
                
                if result['status'] == 'success':
                    processed += 1
                    logger.info(f"Match {match.id}: {event_type} handled successfully")
                else:
                    error_msg = result.get('message', 'Unknown error')
                    logger.error(f"Match {match.id}: Timeout handling failed - {error_msg}")
                    
            except Exception as e:
                logger.error(f"Error processing timeout for match {match.id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info(f"Processed {processed}/{count} timeouts")
        
        return {
            'status': 'success',
            'expired_count': count,
            'processed': processed
        }
            
    except Exception as e:
        logger.error(f"Error in check_veto_timeouts: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'status': 'error',
            'message': str(e)
        }

