"""
Match Manager - Handles post-acceptance match flow.

Manages the lifecycle of a match after all players have accepted:
1. Create Match instance from accepted match confirmation
2. Initialize map veto phase
3. Handle veto actions
4. Transition to side selection
5. Prepare for custom game creation
"""

from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
import logging
import random
from asgiref.sync import sync_to_async

from .models_match import Match, MatchPlayer, VetoAction
from .match_confirmation import MatchConfirmationManager

logger = logging.getLogger(__name__)


class MatchManager:
    """
    Manages match state transitions and veto logic.
    """
    
    # Veto timing constants
    VETO_TIMEOUT_SECONDS = 30
    SIDE_SELECTION_TIMEOUT_SECONDS = 15
    
    @staticmethod
    async def create_match_from_confirmation(match_confirmation_id: str) -> Optional[Match]:
        """
        Create a Match instance after all players have accepted.
        
        This transitions from the MatchConfirmation system to the Match system.
        
        Args:
            match_confirmation_id: ID of the confirmed match
            
        Returns:
            Match instance or None if creation failed
        """
        try:
            # Get match confirmation data
            confirmation_data = await MatchConfirmationManager.get_match_data(match_confirmation_id)
            
            if not confirmation_data:
                logger.error(f"No confirmation data found for {match_confirmation_id}")
                return None
            
            # The confirmation_data IS the match data (it contains all the match information)
            match_data = confirmation_data
            match_lobbies = match_data.get('match_lobbies', [])
            
            # Get team assignments
            team_a_lobbies, team_b_lobbies = MatchManager._extract_team_lobbies(match_data)
            team_a_players, team_b_players = MatchManager._extract_team_players(match_data)
            
            # Get captains from matchmaker data (if available) or determine by highest MMR
            if 'team_a' in match_data and 'team_b' in match_data:
                team_a_captain = match_data['team_a'].get('captain', max(team_a_players, key=lambda p: p.get('mmr', 0)))
                team_b_captain = match_data['team_b'].get('captain', max(team_b_players, key=lambda p: p.get('mmr', 0)))
            else:
                # Fallback: determine captains (highest MMR player on each team)
                team_a_captain = max(team_a_players, key=lambda p: p.get('mmr', 0))
                team_b_captain = max(team_b_players, key=lambda p: p.get('mmr', 0))
            
            # Get map pool and server region
            map_pool = match_data.get('map_pool', [])
            server_pool = match_data.get('server_pool', [])
            server_region = server_pool[0] if server_pool else 'na'
            
            # Calculate team averages
            team_a_avg_mmr = sum(p.get('mmr', 0) for p in team_a_players) / len(team_a_players)
            team_b_avg_mmr = sum(p.get('mmr', 0) for p in team_b_players) / len(team_b_players)
            
            # Create Match instance (using sync_to_async for Celery compatibility)
            match = await sync_to_async(Match.objects.create, thread_sensitive=False)(
                match_confirmation_id=match_confirmation_id,
                state=Match.STATE_CONFIRMED,
                team_a_lobbies=team_a_lobbies,
                team_b_lobbies=team_b_lobbies,
                team_a_players=team_a_players,
                team_b_players=team_b_players,
                team_a_captain_puuid=team_a_captain['puuid'],
                team_b_captain_puuid=team_b_captain['puuid'],
                map_pool=map_pool,
                server_region=server_region,
                match_quality=match_data.get('match_quality', 0.0),
                team_a_avg_mmr=team_a_avg_mmr,
                team_b_avg_mmr=team_b_avg_mmr,
            )
            
            # Create MatchPlayer entries for tracking
            await MatchManager._create_match_players(match, team_a_players, team_b_players)
            
            logger.info(f"Created match {match.id} from confirmation {match_confirmation_id}")
            
            return match
            
        except Exception as e:
            logger.error(f"Error creating match from confirmation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def _extract_team_lobbies(match_data: Dict) -> Tuple[List[str], List[str]]:
        """Extract lobby IDs for each team."""
        # Handle team_a/team_b format from matchmaker
        if 'team_a' in match_data and 'team_b' in match_data:
            # Extract lobby IDs from match_lobbies based on team assignments
            match_lobbies = match_data.get('match_lobbies', [])
            team_a_lobbies = []
            team_b_lobbies = []
            
            # Get team A and B player PUUIDs
            team_a_puuids = {p['puuid'] for p in match_data['team_a']['players']}
            team_b_puuids = {p['puuid'] for p in match_data['team_b']['players']}
            
            # Assign lobbies to teams based on which players are in them
            for lobby in match_lobbies:
                lobby_player_puuids = {p['puuid'] for p in lobby.get('players', [])}
                
                # Check if lobby players overlap more with team A or team B
                team_a_overlap = len(lobby_player_puuids.intersection(team_a_puuids))
                team_b_overlap = len(lobby_player_puuids.intersection(team_b_puuids))
                
                if team_a_overlap > team_b_overlap:
                    team_a_lobbies.append(lobby['id'])
                elif team_b_overlap > team_a_overlap:
                    team_b_lobbies.append(lobby['id'])
                else:
                    # Equal overlap - assign to team A by default
                    team_a_lobbies.append(lobby['id'])
            
            return team_a_lobbies, team_b_lobbies
        
        # Handle legacy lobby1/lobby2 format
        lobby1 = match_data.get('lobby1', {})
        lobby2 = match_data.get('lobby2', {})
        
        team_a_lobbies = [lobby1.get('id')] if lobby1.get('id') else []
        team_b_lobbies = [lobby2.get('id')] if lobby2.get('id') else []
        
        # Handle multiple lobbies per team (if any)
        lobbies = match_data.get('lobbies', [])
        if len(lobbies) > 2:
            # For now, assume first half go to team A, second half to team B
            mid = len(lobbies) // 2
            team_a_lobbies = lobbies[:mid]
            team_b_lobbies = lobbies[mid:]
        
        return team_a_lobbies, team_b_lobbies
    
    @staticmethod
    def _extract_team_players(match_data: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Extract player data for each team."""
        # Handle team_a/team_b format from matchmaker
        if 'team_a' in match_data and 'team_b' in match_data:
            team_a_players = match_data['team_a']['players']
            team_b_players = match_data['team_b']['players']
            return team_a_players, team_b_players
        
        # Handle legacy lobby1/lobby2 format
        lobby1 = match_data.get('lobby1', {})
        lobby2 = match_data.get('lobby2', {})
        
        team_a_players = lobby1.get('players', [])
        team_b_players = lobby2.get('players', [])
        
        return team_a_players, team_b_players
    
    @staticmethod
    async def _create_match_players(match: Match, team_a_players: List[Dict], team_b_players: List[Dict]):
        """Create MatchPlayer entries for all players."""
        match_players = []
        
        for player in team_a_players:
            match_players.append(MatchPlayer(
                match=match,
                player_puuid=player['puuid'],
                player_alias=player['alias'],
                player_elo=player.get('elo', 0),
                player_mmr=player.get('mmr', 0),
                team='team_a',
                is_captain=(player['puuid'] == match.team_a_captain_puuid)
            ))
        
        for player in team_b_players:
            match_players.append(MatchPlayer(
                match=match,
                player_puuid=player['puuid'],
                player_alias=player['alias'],
                player_elo=player.get('elo', 0),
                player_mmr=player.get('mmr', 0),
                team='team_b',
                is_captain=(player['puuid'] == match.team_b_captain_puuid)
            ))
        
        await sync_to_async(MatchPlayer.objects.bulk_create, thread_sensitive=False)(match_players)
        logger.info(f"Created {len(match_players)} MatchPlayer entries for match {match.id}")
    
    @staticmethod
    async def start_veto(match: Match) -> Dict:
        """
        Initialize the map veto phase.
        
        Higher MMR team bans first.
        
        Args:
            match: Match instance
            
        Returns:
            Dict with veto start data
        """
        try:
            # Determine which team bans first (higher MMR)
            starting_team = 'team_a' if match.team_a_avg_mmr >= match.team_b_avg_mmr else 'team_b'
            
            # Update match state
            match.state = Match.STATE_VETO
            match.veto_turn = starting_team
            match.veto_started_at = timezone.now()
            match.veto_deadline = timezone.now() + timedelta(seconds=MatchManager.VETO_TIMEOUT_SECONDS)
            await sync_to_async(match.save, thread_sensitive=False)(update_fields=['state', 'veto_turn', 'veto_started_at', 'veto_deadline'])
            
            logger.info(f"Match {match.id}: Veto started, {starting_team} bans first")
            
            return {
                'status': 'success',
                'match_id': str(match.id),
                'current_turn': starting_team,
                'available_maps': match.map_pool,
                'deadline': match.veto_deadline.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error starting veto for match {match.id}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    async def process_veto(match: Match, map_name: str, vetoing_team: str, player_puuid: str) -> Dict:
        """
        Process a map veto action.
        
        Args:
            match: Match instance
            map_name: Name of map being vetoed
            vetoing_team: 'team_a' or 'team_b'
            player_puuid: PUUID of player making veto
            
        Returns:
            Dict with veto result
        """
        try:
            # Validation
            if match.state != Match.STATE_VETO:
                return {
                    'status': 'error',
                    'message': 'Match is not in veto phase'
                }
            
            if match.veto_turn != vetoing_team:
                return {
                    'status': 'error',
                    'message': 'Not your turn to veto'
                }
            
            if map_name not in match.map_pool or map_name in match.vetoed_maps:
                return {
                    'status': 'error',
                    'message': 'Invalid map selection'
                }
            
            # Check if player is captain of their team
            if vetoing_team == 'team_a' and player_puuid != match.team_a_captain_puuid:
                return {
                    'status': 'error',
                    'message': 'Only team captain can veto'
                }
            if vetoing_team == 'team_b' and player_puuid != match.team_b_captain_puuid:
                return {
                    'status': 'error',
                    'message': 'Only team captain can veto'
                }
            
            # Add to vetoed list
            match.vetoed_maps.append(map_name)
            
            # Record veto action
            sequence_number = len(match.vetoed_maps)
            await sync_to_async(VetoAction.objects.create, thread_sensitive=False)(
                match=match,
                action_type=VetoAction.ACTION_BAN,
                map_name=map_name,
                team=vetoing_team,
                player_puuid=player_puuid,
                sequence_number=sequence_number,
                was_timeout=False
            )
            
            # Check if veto complete
            remaining_maps = match.get_remaining_maps()
            
            if len(remaining_maps) == 1:
                # Veto complete
                match.final_map = remaining_maps[0]
                match.state = Match.STATE_SIDE_SELECTION
                match.side_selector = vetoing_team  # Last team to veto gets side selection
                match.side_selection_deadline = timezone.now() + timedelta(seconds=MatchManager.SIDE_SELECTION_TIMEOUT_SECONDS)
                await sync_to_async(match.save, thread_sensitive=False)(update_fields=['vetoed_maps', 'final_map', 'state', 'side_selector', 'side_selection_deadline'])
                
                logger.info(f"Match {match.id}: Veto complete, final map is {match.final_map}")
                
                return {
                    'status': 'success',
                    'veto_complete': True,
                    'final_map': match.final_map,
                    'side_selector': match.side_selector,
                    'map_name': map_name,
                    'vetoed_by': vetoing_team
                }
            else:
                # Continue veto - switch turns
                next_turn = 'team_b' if vetoing_team == 'team_a' else 'team_a'
                match.veto_turn = next_turn
                match.veto_deadline = timezone.now() + timedelta(seconds=MatchManager.VETO_TIMEOUT_SECONDS)
                await sync_to_async(match.save, thread_sensitive=False)(update_fields=['vetoed_maps', 'veto_turn', 'veto_deadline'])
                
                logger.info(f"Match {match.id}: {vetoing_team} vetoed {map_name}, next turn: {next_turn}")
                
                return {
                    'status': 'success',
                    'veto_complete': False,
                    'map_name': map_name,
                    'vetoed_by': vetoing_team,
                    'next_turn': next_turn,
                    'remaining_maps': remaining_maps,
                    'deadline': match.veto_deadline.isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error processing veto for match {match.id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    async def handle_veto_timeout(match_id) -> Dict:
        """
        Handle timeout for veto action.
        Auto-veto a random available map.
        
        Args:
            match_id: Match ID (UUID or string)
            
        Returns:
            Dict with timeout result
        """
        try:
            # Fetch match in async context
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            
            if match.state != Match.STATE_VETO:
                return {'status': 'error', 'message': 'Not in veto phase'}
            
            # Get available maps
            remaining_maps = match.get_remaining_maps()
            
            if not remaining_maps:
                return {'status': 'error', 'message': 'No maps available'}
            
            # Auto-select random map
            auto_map = random.choice(remaining_maps)
            current_team = match.veto_turn
            
            # Add to vetoed list
            match.vetoed_maps.append(auto_map)
            
            # Record timeout veto
            sequence_number = len(match.vetoed_maps)
            await sync_to_async(VetoAction.objects.create, thread_sensitive=False)(
                match=match,
                action_type=VetoAction.ACTION_TIMEOUT,
                map_name=auto_map,
                team=current_team,
                player_puuid=None,
                sequence_number=sequence_number,
                was_timeout=True
            )
            
            logger.warning(f"Match {match.id}: {current_team} timed out, auto-vetoed {auto_map}")
            
            # Check if veto complete
            remaining_maps = match.get_remaining_maps()
            
            if len(remaining_maps) == 1:
                # Veto complete
                match.final_map = remaining_maps[0]
                match.state = Match.STATE_SIDE_SELECTION
                match.side_selector = current_team
                match.side_selection_deadline = timezone.now() + timedelta(seconds=MatchManager.SIDE_SELECTION_TIMEOUT_SECONDS)
                await sync_to_async(match.save, thread_sensitive=False)(update_fields=['vetoed_maps', 'final_map', 'state', 'side_selector', 'side_selection_deadline'])
                
                return {
                    'status': 'success',
                    'was_timeout': True,
                    'veto_complete': True,
                    'auto_vetoed_map': auto_map,
                    'final_map': match.final_map,
                    'side_selector': match.side_selector
                }
            else:
                # Continue veto
                next_turn = 'team_b' if current_team == 'team_a' else 'team_a'
                match.veto_turn = next_turn
                match.veto_deadline = timezone.now() + timedelta(seconds=MatchManager.VETO_TIMEOUT_SECONDS)
                await sync_to_async(match.save, thread_sensitive=False)(update_fields=['vetoed_maps', 'veto_turn', 'veto_deadline'])
                
                return {
                    'status': 'success',
                    'was_timeout': True,
                    'veto_complete': False,
                    'auto_vetoed_map': auto_map,
                    'next_turn': next_turn,
                    'remaining_maps': remaining_maps,
                    'deadline': match.veto_deadline.isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error handling veto timeout for match {match.id}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    async def get_match_data(match_id: str) -> Optional[Dict]:
        """
        Get complete match data for frontend.
        
        Args:
            match_id: Match UUID
            
        Returns:
            Dict with match data or None
        """
        try:
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            
            # Get all match players
            match_players = []
            players = await sync_to_async(list, thread_sensitive=False)(MatchPlayer.objects.filter(match=match))
            for player in players:
                match_players.append({
                    'puuid': player.player_puuid,
                    'alias': player.player_alias,
                    'elo': player.player_elo,
                    'mmr': player.player_mmr,
                    'team': player.team,
                    'is_captain': player.is_captain,
                    'is_ready': player.is_ready,
                    'joined_pregame': player.joined_pregame,
                })
            
            # Get veto history
            veto_history = []
            veto_actions = await sync_to_async(list, thread_sensitive=False)(VetoAction.objects.filter(match=match).order_by('sequence_number'))
            for veto in veto_actions:
                veto_history.append({
                    'action_type': veto.action_type,
                    'map_name': veto.map_name,
                    'team': veto.team,
                    'was_timeout': veto.was_timeout,
                    'sequence_number': veto.sequence_number,
                })
            
            return {
                'match_id': str(match.id),
                'state': match.state,
                'team_a_players': [p for p in match_players if p['team'] == 'team_a'],
                'team_b_players': [p for p in match_players if p['team'] == 'team_b'],
                'team_a_captain': match.team_a_captain_puuid,
                'team_b_captain': match.team_b_captain_puuid,
                'team_a_lobbies': match.team_a_lobbies,  # Lobby IDs for party information
                'team_b_lobbies': match.team_b_lobbies,  # Lobby IDs for party information
                'map_pool': match.map_pool,
                'vetoed_maps': match.vetoed_maps,
                'remaining_maps': match.get_remaining_maps(),
                'final_map': match.final_map,
                'veto_turn': match.veto_turn,
                'veto_deadline': match.veto_deadline.isoformat() if match.veto_deadline else None,
                'veto_history': veto_history,
                'side_selector': match.side_selector,
                'selected_side': match.selected_side,
                'match_quality': match.match_quality,
                'team_a_avg_mmr': match.team_a_avg_mmr,
                'team_b_avg_mmr': match.team_b_avg_mmr,
            }
            
        except Match.DoesNotExist:
            logger.error(f"Match {match_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting match data for {match_id}: {str(e)}")
            return None
    
    # ============================================================================
    # SYNCHRONOUS METHODS FOR CELERY TASKS
    # ============================================================================
    
    @staticmethod
    def handle_veto_timeout_sync(match_id) -> Dict:
        """
        Handle timeout for veto action - SYNC version for Celery tasks.
        Auto-veto a random available map.
        
        Args:
            match_id: Match ID (UUID or string)
            
        Returns:
            Dict with timeout result
        """
        from django.utils import timezone
        from datetime import timedelta
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        try:
            # Fetch match (direct ORM call - Celery best practice)
            match = Match.objects.get(id=match_id)
            
            if match.state != Match.STATE_VETO:
                return {'status': 'error', 'message': 'Not in veto phase'}
            
            # Get available maps
            remaining_maps = match.get_remaining_maps()
            
            if not remaining_maps:
                return {'status': 'error', 'message': 'No maps available'}
            
            # Auto-select random map
            auto_map = random.choice(remaining_maps)
            current_team = match.veto_turn
            
            # Add to vetoed list
            match.vetoed_maps.append(auto_map)
            
            # Record timeout veto
            sequence_number = len(match.vetoed_maps)
            VetoAction.objects.create(
                match=match,
                action_type=VetoAction.ACTION_TIMEOUT,
                map_name=auto_map,
                team=current_team,
                player_puuid=None,
                sequence_number=sequence_number,
                was_timeout=True
            )
            
            logger.warning(f"Match {match.id}: {current_team} timed out, auto-vetoed {auto_map}")
            
            # Check if veto complete
            remaining_maps = match.get_remaining_maps()
            
            if len(remaining_maps) == 1:
                # Veto complete
                match.final_map = remaining_maps[0]
                match.state = Match.STATE_SIDE_SELECTION
                match.side_selector = current_team
                match.side_selection_deadline = timezone.now() + timedelta(seconds=MatchManager.SIDE_SELECTION_TIMEOUT_SECONDS)
                match.save(update_fields=['vetoed_maps', 'final_map', 'state', 'side_selector', 'side_selection_deadline'])
                
                return {
                    'status': 'success',
                    'auto_vetoed_map': auto_map,
                    'veto_complete': True,
                    'final_map': match.final_map,
                    'side_selector': match.side_selector,
                    'deadline': match.side_selection_deadline.isoformat() if match.side_selection_deadline else None
                }
            else:
                # Continue veto
                next_turn = 'team_b' if current_team == 'team_a' else 'team_a'
                match.veto_turn = next_turn
                match.veto_deadline = timezone.now() + timedelta(seconds=MatchManager.VETO_TIMEOUT_SECONDS)
                match.save(update_fields=['vetoed_maps', 'veto_turn', 'veto_deadline'])
                
                return {
                    'status': 'success',
                    'auto_vetoed_map': auto_map,
                    'veto_complete': False,
                    'next_turn': next_turn,
                    'remaining_maps': remaining_maps,
                    'deadline': match.veto_deadline.isoformat()
                }
                
        except Match.DoesNotExist:
            logger.error(f"Match {match_id} not found")
            return {
                'status': 'error',
                'message': f'Match {match_id} not found'
            }
        except Exception as e:
            logger.error(f"Error handling veto timeout for match {match_id}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

