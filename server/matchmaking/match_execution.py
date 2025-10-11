"""
Match Execution Manager
Handles match transition from confirmed → starting → in_progress → completed
Uses WebSocket-only communication for all updates
Performance-optimized with minimal database queries
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from django.apps import apps
from django.utils import timezone
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class MatchExecutionManager:
    """
    Handles match execution flow with WebSocket-only communication.
    Optimized for performance with minimal overhead during gameplay.
    """
    
    @staticmethod
    async def initiate_match_start(match_id: str) -> Dict:
        """
        Called when all players have accepted the match.
        Selects constructor and initiates custom game creation.
        
        Performance: O(1) - single DB query
        
        Args:
            match_id: UUID of the match
            
        Returns:
            Dict with status and constructor information
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            # Fetch match data
            def get_match():
                return Match.objects.get(id=match_id)
            
            match = await sync_to_async(get_match)()
            
            # Select constructor (highest ELO player from team_a)
            constructor = await MatchExecutionManager._select_constructor(match)
            
            # Update match status
            def update_match():
                match.status = 'starting'
                match.constructor_puuid = constructor['puuid']
                match.confirmation_completed_at = timezone.now()
                match.save()
            
            await sync_to_async(update_match)()
            
            # Notify all players via WebSocket
            await MatchExecutionManager._broadcast_match_starting(match, constructor)
            
            logger.info(f"Match {match_id} starting - Constructor: {constructor['puuid']}")
            
            return {
                'status': 'success',
                'match_id': match_id,
                'constructor_puuid': constructor['puuid'],
                'message': 'Match starting - custom game creation initiated'
            }
            
        except Exception as e:
            logger.error(f"Error initiating match start: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def _select_constructor(match) -> Dict:
        """
        Select the constructor (party leader) for custom match creation.
        Strategy: Select team captain (highest ELO player) from team_a.
        
        Performance: O(n) where n = team size (max 5)
        
        Args:
            match: Match object
            
        Returns:
            Dict with constructor details
        """
        # Get team_a data from match
        team_a_data = match.team_a_data
        
        # Get captain from team_a (should be set during matchmaking)
        captain_data = team_a_data.get('captain', {})
        
        if captain_data and 'puuid' in captain_data:
            return {
                'puuid': captain_data['puuid'],
                'alias': captain_data.get('alias', 'Unknown'),
                'team': 'team_a'
            }
        
        # Fallback: Select highest ELO from team_a players
        team_a_players = team_a_data.get('players', [])
        if team_a_players:
            constructor = max(team_a_players, key=lambda p: p.get('elo', 0))
            return {
                'puuid': constructor['puuid'],
                'alias': constructor.get('alias', 'Unknown'),
                'team': 'team_a'
            }
        
        raise ValueError("No valid constructor found for match")
    
    
    @staticmethod
    async def _broadcast_match_starting(match, constructor: Dict):
        """
        Broadcast match starting event to all players via WebSocket.
        
        Performance: Single channel layer group_send per player (O(n))
        
        Args:
            match: Match object
            constructor: Dict with constructor details
        """
        channel_layer = get_channel_layer()
        
        # Get all player PUUIDs from both teams
        all_players = []
        team_a_players = match.team_a_data.get('players', [])
        team_b_players = match.team_b_data.get('players', [])
        
        all_players.extend([p['puuid'] for p in team_a_players])
        all_players.extend([p['puuid'] for p in team_b_players])
        
        # Broadcast to each player's WebSocket connection
        for puuid in all_players:
            # Determine player's team
            is_team_a = puuid in [p['puuid'] for p in team_a_players]
            team = 'team_a' if is_team_a else 'team_b'
            
            await channel_layer.group_send(
                f"player_{puuid}",
                {
                    'type': 'match_starting',
                    'match_id': str(match.id),
                    'constructor_puuid': constructor['puuid'],
                    'is_constructor': (puuid == constructor['puuid']),
                    'map': match.selected_map,
                    'server': match.game_server,
                    'team': team
                }
            )
        
        logger.info(f"Broadcast match_starting to {len(all_players)} players")
    
    
    @staticmethod
    async def handle_custom_game_created(match_id: str, pregame_id: str, constructor_puuid: str) -> Dict:
        """
        Called by constructor client after successfully creating custom game.
        Updates match status and notifies other players to join.
        
        Performance: O(1) - single update + broadcast
        
        Args:
            match_id: UUID of the match
            pregame_id: Valorant pregame ID
            constructor_puuid: PUUID of the constructor
            
        Returns:
            Dict with status
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            def update_match():
                match = Match.objects.get(id=match_id)
                match.pregame_id = pregame_id
                # Status remains 'starting' until all players join
                match.save()
                return match
            
            match = await sync_to_async(update_match)()
            
            # Broadcast to all non-constructor players to join
            await MatchExecutionManager._broadcast_join_custom_game(match, pregame_id, constructor_puuid)
            
            logger.info(f"Custom game created for match {match_id}: {pregame_id}")
            
            return {'status': 'success', 'pregame_id': pregame_id}
            
        except Exception as e:
            logger.error(f"Error handling custom game creation: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def _broadcast_join_custom_game(match, pregame_id: str, constructor_puuid: str):
        """
        Tell all non-constructor players to join the custom game.
        
        Performance: O(n) where n = players (max 10)
        
        Args:
            match: Match object
            pregame_id: Valorant pregame ID
            constructor_puuid: PUUID of the constructor
        """
        channel_layer = get_channel_layer()
        
        # Get all players
        team_a_players = match.team_a_data.get('players', [])
        team_b_players = match.team_b_data.get('players', [])
        
        all_players = []
        all_players.extend([p['puuid'] for p in team_a_players])
        all_players.extend([p['puuid'] for p in team_b_players])
        
        for puuid in all_players:
            if puuid == constructor_puuid:
                continue  # Skip constructor
            
            # Determine team
            is_team_a = puuid in [p['puuid'] for p in team_a_players]
            team = 'team_a' if is_team_a else 'team_b'
            
            await channel_layer.group_send(
                f"player_{puuid}",
                {
                    'type': 'join_custom_game',
                    'match_id': str(match.id),
                    'pregame_id': pregame_id,
                    'team': team
                }
            )
        
        logger.info(f"Broadcast join_custom_game to {len(all_players)-1} players")
    
    
    @staticmethod
    async def handle_match_started(match_id: str, coregame_id: str) -> Dict:
        """
        Called when the match actually starts (all players loaded in).
        Transitions match to 'in_progress' state.
        
        Performance: O(1)
        
        Args:
            match_id: UUID of the match
            coregame_id: Valorant coregame ID
            
        Returns:
            Dict with status
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            def update_match():
                match = Match.objects.get(id=match_id)
                match.coregame_id = coregame_id
                match.status = 'in_progress'
                match.started_at = timezone.now()
                match.save()
                return match
            
            match = await sync_to_async(update_match)()
            
            # Notify all players that match is live
            await MatchExecutionManager._broadcast_match_in_progress(match)
            
            logger.info(f"Match {match_id} now in progress: {coregame_id}")
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling match start: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def _broadcast_match_in_progress(match):
        """
        Notify all players and spectators that match is live.
        
        Args:
            match: Match object
        """
        channel_layer = get_channel_layer()
        
        # Broadcast to match group (for spectators and players)
        await channel_layer.group_send(
            f"match_{match.id}",
            {
                'type': 'match_in_progress',
                'match_id': str(match.id),
                'coregame_id': match.coregame_id,
                'map': match.selected_map,
                'server': match.game_server
            }
        )
        
        logger.info(f"Match {match.id} in_progress broadcast sent")
    
    
    @staticmethod
    async def handle_match_completion(match_id: str, final_data: Dict) -> Dict:
        """
        Handle match completion - process final results and update ELO.
        
        Args:
            match_id: UUID of the match
            final_data: Final match data from ValClient
            
        Returns:
            Dict with status
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            def update_match():
                match = Match.objects.get(id=match_id)
                match.status = 'completed'
                match.completed_at = timezone.now()
                match.finish_time = timezone.now()
                
                # Store final scores
                match.team_a_score = final_data.get('team_a_score', 0)
                match.team_b_score = final_data.get('team_b_score', 0)
                
                match.save()
                return match
            
            match = await sync_to_async(update_match)()
            
            # Notify all players and spectators
            await MatchExecutionManager._broadcast_match_completed(match, final_data)
            
            # Schedule background task for statistics processing
            # TODO: Implement process_match_completion task in tasks.py
            # from .tasks import process_match_completion
            # process_match_completion.apply_async((match_id,), countdown=5)
            
            logger.info(f"Match {match_id} completed: {match.team_a_score}-{match.team_b_score}")
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling match completion: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def _broadcast_match_completed(match, final_data: Dict):
        """
        Notify all players and spectators that match completed.
        
        Args:
            match: Match object
            final_data: Final match data
        """
        channel_layer = get_channel_layer()
        
        # Determine winner
        winner = None
        if match.team_a_score > match.team_b_score:
            winner = 'team_a'
        elif match.team_b_score > match.team_a_score:
            winner = 'team_b'
        
        await channel_layer.group_send(
            f"match_{match.id}",
            {
                'type': 'match_completed',
                'match_id': str(match.id),
                'team_a_score': match.team_a_score,
                'team_b_score': match.team_b_score,
                'winner': winner,
                'final_data': final_data
            }
        )
        
        logger.info(f"Match {match.id} completion broadcast sent")
    
    
    @staticmethod
    async def generate_rejoin_token(match_id: str, player_puuid: str) -> str:
        """
        Generate a rejoin token for a player who disconnected.
        Token expires after 5 minutes.
        
        Performance: O(1)
        
        Args:
            match_id: UUID of the match
            player_puuid: PUUID of the player
            
        Returns:
            Rejoin token string
        """
        MatchRejoinToken = apps.get_model('scrimgg', 'MatchRejoinToken')
        Match = apps.get_model('scrimgg', 'Match')
        Player = apps.get_model('scrimgg', 'Player')
        
        def create_token():
            match = Match.objects.get(id=match_id)
            player = Player.objects.get(puuid=player_puuid)
            
            # Delete old tokens
            MatchRejoinToken.objects.filter(match=match, player=player).delete()
            
            # Create new token
            token = MatchRejoinToken.objects.create(
                match=match,
                player=player,
                expires_at=timezone.now() + timedelta(minutes=5)
            )
            return str(token.token)
        
        token = await sync_to_async(create_token)()
        
        logger.info(f"Generated rejoin token for {player_puuid} in match {match_id}")
        
        return token
    
    
    @staticmethod
    async def validate_rejoin_token(token: str) -> Dict:
        """
        Validate a rejoin token and return match/player information.
        
        Args:
            token: Rejoin token string
            
        Returns:
            Dict with validation result
        """
        MatchRejoinToken = apps.get_model('scrimgg', 'MatchRejoinToken')
        
        def validate():
            try:
                token_obj = MatchRejoinToken.objects.select_related('match', 'player').get(
                    token=token,
                    used=False
                )
                
                # Check if expired
                if timezone.now() > token_obj.expires_at:
                    return {'valid': False, 'reason': 'Token expired'}
                
                # Check if match is still in progress
                if token_obj.match.status not in ['in_progress', 'paused']:
                    return {'valid': False, 'reason': 'Match is not active'}
                
                # Mark as used
                token_obj.used = True
                token_obj.used_at = timezone.now()
                token_obj.save()
                
                return {
                    'valid': True,
                    'match_id': str(token_obj.match.id),
                    'player_puuid': token_obj.player.puuid,
                    'pregame_id': token_obj.match.pregame_id
                }
                
            except MatchRejoinToken.DoesNotExist:
                return {'valid': False, 'reason': 'Invalid token'}
        
        result = await sync_to_async(validate)()
        
        return result

