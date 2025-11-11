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
# Match models moved to match_system app
from match_system.models import Match
from match_system.managers.match_manager import MatchManager

logger = get_task_logger(__name__)

@shared_task(bind=True, name='matchmaking.tasks.periodic_matchmaking')
def periodic_matchmaking(self):
    """
    Periodic task to find matches for lobbies in queue.
    Runs every 30 seconds.
    
    SYNC TASK: Uses direct ORM/Redis calls following Celery best practices.
    """
    try:
        logger.info("="*70)
        logger.info("PERIODIC MATCHMAKING STARTED")
        logger.info("="*70)
        
        # Get queue statistics (SYNC)
        queue_stats = QueueManager.get_queue_stats_sync()
        total_lobbies = queue_stats.get('total_lobbies', 0)
        total_players = queue_stats.get('total_players', 0)
        
        logger.info(f"Queue Status: {total_lobbies} lobbies, {total_players} players")
        
        if total_lobbies < 2:
            logger.info("Not enough lobbies in queue for matchmaking (need 2+)")
            return {
                'status': 'success',
                'message': 'Not enough lobbies in queue',
                'lobbies_in_queue': total_lobbies,
                'matches_found': 0
            }
        
        # Run matchmaking algorithm (using MMR-based matchmaker) - SYNC
        logger.info("Running MMR-based matchmaker (MatchmakerV2)...")
        matchmaking_result = MatchmakerV2.find_matches_sync()
        
        if matchmaking_result['status'] == 'success':
            matches_found = matchmaking_result.get('matches_found', 0)
            logger.info(f"Matchmaking completed: {matches_found} matches found")
            
            # If matches were found, create match confirmations
            if matches_found > 0:
                logger.info(f"Processing {matches_found} match(es)...")
                matches = matchmaking_result.get('matches', [])
                confirmations_created = 0
                
                for idx, match in enumerate(matches, 1):
                    try:
                        logger.info(f"Match {idx}/{len(matches)}:")
                        logger.info(f"   Match data keys: {list(match.keys())}")
                        
                        # Log team info
                        if 'lobby1' in match and 'lobby2' in match:
                            logger.info(f"   Lobby 1: {len(match['lobby1'].get('players', []))} players")
                            logger.info(f"   Lobby 2: {len(match['lobby2'].get('players', []))} players")
                        
                        # Create match confirmation (SYNC)
                        logger.info(f"   Creating match confirmation...")
                        confirmation_id = MatchConfirmationManager.initiate_confirmation_sync(match)
                        
                        if confirmation_id:
                            confirmations_created += 1
                            logger.info(f"   Created confirmation: {confirmation_id[:8]}...")
                            
                            # Send match found notifications to ALL lobbies in the match
                            all_lobby_ids = match.get('lobbies', [])
                            
                            if not all_lobby_ids:
                                # Fallback to lobby1/lobby2 if 'lobbies' field not present
                                all_lobby_ids = [match['lobby1']['id'], match['lobby2']['id']]
                                logger.info(f"   Using lobby1/lobby2 format: {all_lobby_ids}")
                            
                            logger.info(f"   Notifying {len(all_lobby_ids)} lobbies...")
                            
                            # Spawn async notification tasks for each lobby (non-blocking)
                            for i, lobby_id in enumerate(all_lobby_ids, 1):
                                logger.info(f"   Spawning notification task for lobby {i}/{len(all_lobby_ids)}: {lobby_id}")
                                notify_match_found_task.apply_async(
                                    args=[lobby_id, confirmation_id],
                                    queue='celery'  # Use default queue for fast dispatch
                                )
                            
                            logger.info(f"   All notification tasks spawned for match {confirmation_id[:8]}")
                            
                    except Exception as e:
                        logger.error(f"   Error creating match confirmation: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
                
                logger.info(f"MATCHMAKING SUCCESS: {confirmations_created} confirmations created")
                logger.info("="*70)
                return {
                    'status': 'success',
                    'message': f'Matchmaking completed successfully',
                    'lobbies_in_queue': total_lobbies,
                    'matches_found': matches_found,
                    'confirmations_created': confirmations_created
                }
            else:
                logger.info("No matches found this cycle")
                logger.info("="*70)
                return {
                    'status': 'success',
                    'message': 'No suitable matches found',
                    'lobbies_in_queue': total_lobbies,
                    'matches_found': 0
                }
        else:
            logger.error(f"Matchmaking failed: {matchmaking_result.get('message')}")
            logger.info("="*70)
            return {
                'status': 'error',
                'message': matchmaking_result.get('message', 'Matchmaking failed'),
                'lobbies_in_queue': total_lobbies,
                'matches_found': 0
            }
            
    except Exception as e:
        logger.error(f"ERROR in periodic matchmaking: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("="*70)
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
    
    SYNC TASK: Uses direct Redis calls following Celery best practices.
    """
    try:
        logger.info("Starting cleanup of expired queue entries...")
        
        # Clean up expired lobbies from queue (SYNC)
        cleaned_count = QueueManager.cleanup_expired_lobbies_sync()
        
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
    Runs asynchronously to avoid blocking the matchmaker.
    """
    try:
        logger.info(f"Notifying lobby {lobby_id[:8]}... about match {match_confirmation_id[:8]}...")
        _notify_match_found(lobby_id, match_confirmation_id)
        logger.info(f"Successfully sent match found to lobby {lobby_id[:8]}...")
        return {'status': 'success', 'lobby_id': lobby_id}
    except Exception as e:
        logger.error(f"Error sending match found notification to {lobby_id[:8]}...: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': str(e), 'lobby_id': lobby_id}

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
        
        # Send match found notification (SYNC -> ASYNC bridge)
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
        
        # Send match timeout notification (SYNC -> ASYNC bridge)
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

@shared_task(bind=True, name='matchmaking.tasks.update_lobby_queue_status')
def update_lobby_queue_status_task(self, lobby_id, in_queue):
    """
    Background task to update lobby queue status in database.
    Non-blocking, runs separately from matchmaking flow.
    Synchronous task - safe in Celery context.
    """
    try:
        from django.apps import apps
        from django.utils import timezone
        Lobby = apps.get_model('scrimgg', 'Lobby')
        
        # Regular synchronous Django ORM (safe in Celery task)
        try:
            lobby = Lobby.objects.get(id=lobby_id)
            lobby.in_queue = in_queue
            lobby.queued_at = timezone.now() if in_queue else None
            lobby.save()
            
            logger.debug(f"Updated lobby {lobby_id[:8]}... DB: in_queue={in_queue}")
            return {'status': 'success', 'lobby_id': lobby_id}
        except Lobby.DoesNotExist:
            logger.warning(f"Lobby {lobby_id[:8]}... not found for DB update (may be deleted)")
            return {'status': 'error', 'message': 'Lobby not found'}
            
    except Exception as e:
        logger.error(f"Error updating lobby queue status in DB: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': str(e)}

@shared_task(bind=True, name='matchmaking.tasks.health_check')
def health_check(self):
    """
    Health check task to monitor system status.
    
    SYNC TASK: Uses direct Redis/ORM calls following Celery best practices.
    """
    try:
        # Check Redis connection (SYNC)
        queue_stats = QueueManager.get_queue_stats_sync()
        
        # Check active match confirmations (SYNC)
        active_confirmations = MatchConfirmationManager.get_all_active_confirmations_sync()
        
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


@shared_task(bind=True, name='matchmaking.tasks.check_veto_timeouts')
def check_map_veto_timeouts(self):
    """
    Check for matches with expired deadlines and auto-handle.
    Handles server veto, map veto, and side selection timeouts.
    Runs every 5 seconds.
    
    SYNC TASK: Uses direct ORM calls following Celery best practices.
    """
    from django.utils import timezone
    from django.db import models
    
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
                    
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"match_{match.id}",
                        {
                            'type': event_type,
                            'match_id': str(match.id),
                            # Server veto fields
                            'auto_vetoed_server': result.get('auto_vetoed_server'),
                            'server_veto_complete': result.get('server_veto_complete', False),
                            'final_server': result.get('final_server'),
                            'map_veto_started': result.get('map_veto_started', False),
                            # Map veto fields
                            'auto_vetoed_map': result.get('auto_vetoed_map'),
                            'veto_complete': result.get('veto_complete', False),
                            'final_map': result.get('final_map'),
                            'side_selector': result.get('side_selector'),
                            'side_selection_deadline': result.get('side_selection_deadline'),
                            # Side selection fields
                            'auto_selected_side': result.get('auto_selected_side'),
                            'side_selection_complete': result.get('side_selection_complete', False),
                            'match_ready': result.get('match_ready', False),
                            # Common fields
                            'next_turn': result.get('next_turn'),
                            'remaining_servers': result.get('remaining_servers', []),
                            'remaining_maps': result.get('remaining_maps', []),
                            'deadline': result.get('deadline'),
                        }
                    )

                    # Broadcast fresh snapshot if state changed
                    try:
                        updated_match_data = MatchManager.get_match_data_sync(str(match.id))
                        if updated_match_data:
                            async_to_sync(channel_layer.group_send)(
                                f"match_{match.id}",
                                {
                                    'type': 'match_data',
                                    'match_id': str(match.id),
                                    'payload': updated_match_data
                                }
                            )
                    except Exception as snapshot_error:
                        logger.warning(f"Match {match.id}: Failed to broadcast updated match_data after {event_type}: {snapshot_error}")
                    
                    logger.info(f"Match {match.id}: {event_type} handled successfully")

                    if result.get('veto_complete'):
                        async_to_sync(channel_layer.group_send)(
                            f"match_{match.id}",
                            {
                                'type': 'side_selection_started',
                                'match_id': str(match.id),
                                'side_selector': result.get('side_selector'),
                                'deadline': result.get('side_selection_deadline')
                            }
                        )
                else:
                    logger.error(f"Match {match.id}: Timeout handling failed - {result.get('message')}")
                    
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