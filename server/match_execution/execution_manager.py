"""
Match Execution Manager - Handles custom game creation and player joins.

MOVED FROM: matchmaking/match_execution.py
"""

import logging
from typing import Dict, Optional
from asgiref.sync import sync_to_async

from match_system.models import Match, MatchPlayer

logger = logging.getLogger(__name__)


class MatchExecutionManager:
    """
    Manages the execution phase of a match after veto/side selection is complete.
    Handles custom game creation, player joins, and transition to live state.
    """
    
    # Timing constants
    JOIN_TIMEOUT_SECONDS = 300  # 5 minutes to join
    
    @staticmethod
    async def assign_constructor(match_id: str) -> Optional[Dict]:
        """
        Assign a player to construct the custom game.
        Typically selects a captain or high MMR player.
        
        Args:
            match_id: Match ID
            
        Returns:
            Dict with constructor info or None if failed
        """
        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)
            
            # Prefer team A captain as constructor
            constructor_puuid = match.team_a_captain_puuid
            
            # Update match
            match.constructor_puuid = constructor_puuid
            await sync_to_async(match.save)(update_fields=['constructor_puuid'])
            
            logger.info(f"Match {match_id}: Constructor assigned to {constructor_puuid[:8]}...")
            
            return {
                'status': 'success',
                'constructor_puuid': constructor_puuid,
                'match_id': str(match_id)
            }
            
        except Match.DoesNotExist:
            logger.error(f"Match {match_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error assigning constructor for match {match_id}: {e}")
            return None
    
    @staticmethod
    async def handle_custom_game_created(match_id: str, pregame_id: str, constructor_puuid: str) -> Dict:
        """
        Handle notification that custom game has been created.
        
        Args:
            match_id: Match ID
            pregame_id: Valorant pregame ID
            constructor_puuid: Player who created the game
            
        Returns:
            Dict with status and match data
        """
        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)
            
            # Update match with pregame ID
            match.pregame_id = pregame_id
            match.state = Match.STATE_READY
            await sync_to_async(match.save)(update_fields=['pregame_id', 'state'])
            
            logger.info(f"Match {match_id}: Custom game created with pregame_id {pregame_id}")
            
            return {
                'status': 'success',
                'message': 'Custom game created successfully',
                'match_id': str(match_id),
                'pregame_id': pregame_id,
                'state': match.state
            }
            
        except Match.DoesNotExist:
            logger.error(f"Match {match_id} not found")
            return {
                'status': 'error',
                'message': 'Match not found'
            }
        except Exception as e:
            logger.error(f"Error handling custom game creation: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    async def handle_player_joined(match_id: str, player_puuid: str) -> Dict:
        """
        Handle notification that a player has joined the custom game.
        
        Args:
            match_id: Match ID
            player_puuid: Player PUUID
            
        Returns:
            Dict with status and player count
        """
        try:
            match = await sync_to_async(Match.objects.get)(id=match_id)
            
            # Get or create MatchPlayer record
            def get_or_create_match_player():
                match_player, created = MatchPlayer.objects.get_or_create(
                    match=match,
                    player_puuid=player_puuid,
                    defaults={
                        'player_alias': 'Unknown',  # Should be set properly
                        'player_elo': 0,
                        'player_mmr': 0.0,
                        'team': match.get_player_team(player_puuid) or 'team_a'
                    }
                )
                return match_player
            
            match_player = await sync_to_async(get_or_create_match_player)()
            
            # Mark player as joined
            await sync_to_async(match_player.mark_joined)()
            
            # Count how many players have joined
            def count_joined_players():
                return MatchPlayer.objects.filter(match=match, joined_pregame=True).count()
            
            joined_count = await sync_to_async(count_joined_players)()
            total_players = len(match.get_all_player_puuids())
            
            logger.info(f"Match {match_id}: Player {player_puuid[:8]}... joined ({joined_count}/{total_players})")
            
            # Check if all players have joined
            all_joined = joined_count >= total_players
            
            if all_joined:
                match.state = Match.STATE_IN_PROGRESS
                await sync_to_async(match.save)(update_fields=['state'])
                logger.info(f"Match {match_id}: All players joined, match starting")
            
            return {
                'status': 'success',
                'message': 'Player joined successfully',
                'match_id': str(match_id),
                'player_puuid': player_puuid,
                'joined_count': joined_count,
                'total_players': total_players,
                'all_joined': all_joined
            }
            
        except Match.DoesNotExist:
            logger.error(f"Match {match_id} not found")
            return {
                'status': 'error',
                'message': 'Match not found'
            }
        except Exception as e:
            logger.error(f"Error handling player join: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    async def handle_match_started(match_id: str, coregame_id: str) -> Dict:
        """
        Handle notification that the match has started.
        
        Args:
            match_id: Match ID
            coregame_id: Valorant coregame ID
            
        Returns:
            Dict with status
        """
        try:
            from django.utils import timezone
            
            match = await sync_to_async(Match.objects.get)(id=match_id)
            
            match.coregame_id = coregame_id
            match.state = Match.STATE_IN_PROGRESS
            match.game_started_at = timezone.now()
            await sync_to_async(match.save)(
                update_fields=['coregame_id', 'state', 'game_started_at']
            )
            
            logger.info(f"Match {match_id}: Match started with coregame_id {coregame_id}")
            
            return {
                'status': 'success',
                'message': 'Match started successfully',
                'match_id': str(match_id),
                'coregame_id': coregame_id
            }
            
        except Match.DoesNotExist:
            logger.error(f"Match {match_id} not found")
            return {
                'status': 'error',
                'message': 'Match not found'
            }
        except Exception as e:
            logger.error(f"Error handling match start: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

