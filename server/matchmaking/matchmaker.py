"""
Matchmaker Algorithm
Finds compatible lobbies and balances them into fair 5v5 teams.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from django.utils import timezone
import logging
import random

from .queue_manager import QueueManager

logger = logging.getLogger(__name__)


class Matchmaker:
    """
    Core matchmaking logic for finding and balancing matches.
    """
    
    # Matchmaking constants
    PLAYERS_PER_MATCH = 10
    PLAYERS_PER_TEAM = 5
    
    # ELO tolerance settings
    ELO_TOLERANCE_START = 100  # Initial ELO range
    ELO_TOLERANCE_MAX = 400    # Maximum ELO range
    ELO_TOLERANCE_INCREMENT = 50  # Increase per 30 seconds
    ELO_TOLERANCE_TIME_STEP = 30  # Seconds between increments
    
    # Match quality thresholds
    MIN_MATCH_QUALITY = 0.5  # Minimum acceptable match quality (0-1)
    MAX_TEAM_ELO_DIFFERENCE = 100  # Max ELO diff between teams
    
    @staticmethod
    async def find_match(queue_type: str = 'pug') -> Optional[Dict]:
        """
        Main matchmaking function - finds 10 players and creates a match.
        
        Args:
            queue_type: Type of queue to search
            
        Returns:
            Match data dict or None if no match found
        """
        try:
            # Get all lobbies in queue
            queued_lobbies = await QueueManager.get_all_queued_lobbies(queue_type)
            
            if not queued_lobbies:
                logger.debug("No lobbies in queue")
                return None
            
            # Count total players
            total_players = sum(lobby['size'] for lobby in queued_lobbies)
            
            if total_players < Matchmaker.PLAYERS_PER_MATCH:
                logger.debug(f"Not enough players in queue: {total_players}/10")
                return None
            
            logger.info(f"Attempting matchmaking with {len(queued_lobbies)} lobbies ({total_players} players)")
            
            # Try to find compatible lobby combinations
            match_lobbies = await Matchmaker._find_compatible_lobbies(queued_lobbies)
            
            if not match_lobbies:
                logger.debug("No compatible lobby combinations found")
                return None
            
            # Extract all players from matched lobbies
            all_players = []
            for lobby in match_lobbies:
                all_players.extend(lobby['players'])
            
            # Balance players into teams
            team_a, team_b = await Matchmaker._balance_teams(all_players)
            
            # Calculate match quality
            match_quality = await Matchmaker._calculate_match_quality(team_a, team_b)
            
            if match_quality < Matchmaker.MIN_MATCH_QUALITY:
                logger.debug(f"Match quality too low: {match_quality:.2f}")
                return None
            
            # Determine map pool (intersection of preferences)
            map_pool = await Matchmaker._determine_map_pool(match_lobbies)
            
            # Determine server pool
            server_pool = await Matchmaker._determine_server_pool(match_lobbies)
            
            # Create match data
            match_data = {
                'lobbies': [lobby['id'] for lobby in match_lobbies],
                'team_a': {
                    'players': team_a,
                    'average_elo': sum(p['elo'] for p in team_a) / len(team_a),
                    'captain': await Matchmaker._select_captain(team_a)
                },
                'team_b': {
                    'players': team_b,
                    'average_elo': sum(p['elo'] for p in team_b) / len(team_b),
                    'captain': await Matchmaker._select_captain(team_b)
                },
                'match_quality': match_quality,
                'map_pool': map_pool,
                'server_pool': server_pool,
                'queue_type': queue_type,
                'created_at': timezone.now().isoformat()
            }
            
            logger.info(f"Match found! Quality: {match_quality:.2f}, "
                       f"Team A: {match_data['team_a']['average_elo']:.0f} ELO, "
                       f"Team B: {match_data['team_b']['average_elo']:.0f} ELO")
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error in matchmaking: {str(e)}")
            return None
    
    @staticmethod
    async def _find_compatible_lobbies(lobbies: List[Dict]) -> Optional[List[Dict]]:
        """
        Find a combination of lobbies that total 10 players.
        
        Args:
            lobbies: List of lobby data dicts
            
        Returns:
            List of compatible lobbies or None
        """
        # Sort lobbies by queue time (oldest first - fairness)
        lobbies_sorted = sorted(
            lobbies,
            key=lambda l: l.get('queued_at', '')
        )
        
        # Try to find combination that equals 10 players
        # Start with longest-waiting lobby
        for i, base_lobby in enumerate(lobbies_sorted):
            combination = [base_lobby]
            players_count = base_lobby['size']
            
            # Try to add more lobbies to reach 10 players
            for other_lobby in lobbies_sorted[i+1:]:
                if players_count + other_lobby['size'] <= Matchmaker.PLAYERS_PER_MATCH:
                    # Check ELO compatibility
                    if await Matchmaker._check_elo_compatibility(combination + [other_lobby]):
                        combination.append(other_lobby)
                        players_count += other_lobby['size']
                        
                        if players_count == Matchmaker.PLAYERS_PER_MATCH:
                            logger.info(f"Found combination: {len(combination)} lobbies, 10 players")
                            return combination
        
        logger.debug("No valid combination found for 10 players")
        return None
    
    @staticmethod
    async def _check_elo_compatibility(lobbies: List[Dict]) -> bool:
        """
        Check if lobbies are within acceptable ELO range.
        
        Args:
            lobbies: List of lobby data dicts
            
        Returns:
            True if compatible, False otherwise
        """
        elos = [lobby['average_elo'] for lobby in lobbies]
        min_elo = min(elos)
        max_elo = max(elos)
        
        # Calculate ELO tolerance based on oldest lobby's wait time
        oldest_queue_time = min(
            datetime.fromisoformat(lobby.get('queued_at', timezone.now().isoformat()))
            for lobby in lobbies
        )
        
        wait_time_seconds = (timezone.now() - oldest_queue_time).total_seconds()
        wait_time_steps = int(wait_time_seconds / Matchmaker.ELO_TOLERANCE_TIME_STEP)
        
        # Expand tolerance over time
        tolerance = min(
            Matchmaker.ELO_TOLERANCE_START + (wait_time_steps * Matchmaker.ELO_TOLERANCE_INCREMENT),
            Matchmaker.ELO_TOLERANCE_MAX
        )
        
        elo_range = max_elo - min_elo
        compatible = elo_range <= tolerance
        
        if not compatible:
            logger.debug(f"ELO range {elo_range:.0f} exceeds tolerance {tolerance:.0f}")
        
        return compatible
    
    @staticmethod
    async def _balance_teams(players: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Balance players into two teams of 5.
        Uses snake draft algorithm for fairness.
        
        Args:
            players: List of player dicts
            
        Returns:
            Tuple of (team_a, team_b) player lists
        """
        # Sort players by ELO (highest first)
        players_sorted = sorted(players, key=lambda p: p['elo'], reverse=True)
        
        team_a = []
        team_b = []
        
        # Snake draft: A, B, B, A, A, B, B, A, A, B
        for i, player in enumerate(players_sorted):
            if i % 4 in [0, 3]:
                team_a.append(player)
            else:
                team_b.append(player)
        
        # Calculate team averages
        team_a_avg = sum(p['elo'] for p in team_a) / len(team_a)
        team_b_avg = sum(p['elo'] for p in team_b) / len(team_b)
        
        logger.debug(f"Teams balanced: Team A={team_a_avg:.0f}, Team B={team_b_avg:.0f}, "
                    f"Diff={abs(team_a_avg - team_b_avg):.0f}")
        
        return team_a, team_b
    
    @staticmethod
    async def _calculate_match_quality(team_a: List[Dict], team_b: List[Dict]) -> float:
        """
        Calculate match quality score (0-1).
        Based on team ELO difference - closer is better.
        
        Args:
            team_a: List of player dicts
            team_b: List of player dicts
            
        Returns:
            Quality score from 0 (poor) to 1 (perfect)
        """
        team_a_avg = sum(p['elo'] for p in team_a) / len(team_a)
        team_b_avg = sum(p['elo'] for p in team_b) / len(team_b)
        
        elo_difference = abs(team_a_avg - team_b_avg)
        
        # Quality score: 1.0 for perfect balance, decreases with ELO difference
        # At MAX_TEAM_ELO_DIFFERENCE, quality = 0.5
        quality = max(0.0, 1.0 - (elo_difference / (Matchmaker.MAX_TEAM_ELO_DIFFERENCE * 2)))
        
        return quality
    
    @staticmethod
    async def _determine_map_pool(lobbies: List[Dict]) -> List[str]:
        """
        Determine map pool from lobby preferences.
        Uses intersection if possible, union otherwise.
        
        Args:
            lobbies: List of lobby data dicts
            
        Returns:
            List of map names
        """
        all_preferences = [
            set(lobby.get('map_preferences', []))
            for lobby in lobbies
            if lobby.get('map_preferences')
        ]
        
        if not all_preferences:
            # Default map pool if no preferences
            return ['Ascent', 'Bind', 'Haven', 'Icebox', 'Pearl', 'Split']
        
        # Try intersection first
        common_maps = set.intersection(*all_preferences)
        
        if len(common_maps) >= 3:
            return list(common_maps)
        
        # Use union if intersection too small
        all_maps = set.union(*all_preferences)
        return list(all_maps)
    
    @staticmethod
    async def _determine_server_pool(lobbies: List[Dict]) -> List[str]:
        """
        Determine server pool from lobby preferences.
        Uses intersection if possible, union otherwise.
        
        Args:
            lobbies: List of lobby data dicts
            
        Returns:
            List of server names
        """
        all_preferences = [
            set(lobby.get('server_preferences', []))
            for lobby in lobbies
            if lobby.get('server_preferences')
        ]
        
        if not all_preferences:
            # Default to first lobby's region servers
            return ['Virginia', 'Illinois']  # Default NA servers
        
        # Try intersection first
        common_servers = set.intersection(*all_preferences)
        
        if common_servers:
            return list(common_servers)
        
        # Use union if no common servers
        all_servers = set.union(*all_preferences)
        return list(all_servers)
    
    @staticmethod
    async def _select_captain(team: List[Dict]) -> Dict:
        """
        Select team captain (highest ELO player).
        Captain will handle veto phase.
        
        Args:
            team: List of player dicts
            
        Returns:
            Captain player dict
        """
        captain = max(team, key=lambda p: p['elo'])
        return {
            'puuid': captain['puuid'],
            'alias': captain['alias'],
            'elo': captain['elo']
        }
    
    @staticmethod
    async def calculate_estimated_wait_time(lobby_data: Dict, queue_type: str = 'pug') -> int:
        """
        Calculate estimated wait time for a lobby.
        
        Args:
            lobby_data: Lobby data dict
            queue_type: Type of queue
            
        Returns:
            Estimated wait time in seconds
        """
        try:
            queue_stats = await QueueManager.get_queue_stats(queue_type)
            
            # Base estimate on players needed
            lobby_size = lobby_data.get('size', 1)
            players_needed = Matchmaker.PLAYERS_PER_MATCH - lobby_size
            
            players_in_queue = queue_stats['total_players']
            
            if players_in_queue >= players_needed:
                # Enough players, should match soon
                return 30  # 30 seconds
            else:
                # Need more players
                # Estimate: 1 player joins every 15 seconds
                players_to_wait_for = players_needed - players_in_queue
                return players_to_wait_for * 15
            
        except Exception as e:
            logger.error(f"Error calculating wait time: {str(e)}")
            return 60  # Default 1 minute
    
    @staticmethod
    async def find_matches(queue_type: str = 'pug') -> Dict:
        """
        Find multiple matches from the queue.
        
        Args:
            queue_type: Type of queue to search
            
        Returns:
            Dict with status and matches found
        """
        try:
            matches_found = []
            max_iterations = 10  # Prevent infinite loops
            
            for iteration in range(max_iterations):
                # Try to find a match
                match = await Matchmaker.find_match(queue_type)
                
                if match:
                    # Convert match format to be compatible with Celery tasks
                    converted_match = Matchmaker._convert_match_format(match)
                    matches_found.append(converted_match)
                    logger.info(f"Found match {len(matches_found)}: {converted_match['lobby1']['id'][:8]}... vs {converted_match['lobby2']['id'][:8]}...")
                    
                    # CRITICAL: Remove matched lobbies from queue to prevent duplicate matches
                    # Get ALL lobby IDs (could be 2-10 lobbies depending on party sizes)
                    lobby_ids = converted_match.get('lobbies', [])
                    for lobby_id in lobby_ids:
                        try:
                            # Get lobby leader to call leave_queue
                            from django.apps import apps
                            from asgiref.sync import sync_to_async
                            
                            Lobby = apps.get_model('scrimgg', 'Lobby')
                            
                            def get_lobby_leader():
                                lobby = Lobby.objects.select_related('lobby_leader').get(id=lobby_id)
                                return lobby.lobby_leader.puuid if lobby.lobby_leader else None
                            
                            leader_puuid = await sync_to_async(get_lobby_leader)()
                            
                            if leader_puuid:
                                # Remove from Redis queue using leave_queue
                                result = await QueueManager.leave_queue(lobby_id, leader_puuid, queue_type)
                                if result.get('status') == 'success':
                                    logger.info(f"Removed lobby {lobby_id} from queue after match found")
                                else:
                                    logger.warning(f"Failed to remove lobby {lobby_id}: {result.get('message')}")
                            else:
                                logger.error(f"Could not find lobby leader for {lobby_id}")
                        except Exception as e:
                            logger.error(f"Error removing lobby {lobby_id} from queue: {str(e)}")
                else:
                    # No more matches possible
                    break
            
            return {
                'status': 'success',
                'message': f'Found {len(matches_found)} matches',
                'matches_found': len(matches_found),
                'matches': matches_found
            }
            
        except Exception as e:
            logger.error(f"Error finding matches: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to find matches: {str(e)}',
                'matches_found': 0,
                'matches': []
            }
    
    @staticmethod
    def _convert_match_format(match: Dict) -> Dict:
        """
        Convert match format from team-based to lobby-based for Celery compatibility.
        This format is used by the match confirmation system.
        
        Args:
            match: Original match data with team_a/team_b
            
        Returns:
            Converted match data with lobby1/lobby2 representing the two teams
        """
        try:
            # Get ALL lobby IDs from the match
            all_lobby_ids = match.get('lobbies', [])
            
            if not all_lobby_ids:
                raise ValueError("Match must have at least one lobby")
            
            # Create lobby-based format where lobby1 = team_a, lobby2 = team_b
            # Note: lobby1 and lobby2 are just team identifiers, not actual single lobbies
            # They contain all players that were matched, regardless of original lobby count
            converted_match = {
                'lobby1': {
                    'id': all_lobby_ids[0] if len(all_lobby_ids) > 0 else 'team_a',
                    'players': match['team_a']['players'],
                    'average_elo': match['team_a']['average_elo'],
                    'captain': match['team_a']['captain']
                },
                'lobby2': {
                    'id': all_lobby_ids[1] if len(all_lobby_ids) > 1 else 'team_b',
                    'players': match['team_b']['players'],
                    'average_elo': match['team_b']['average_elo'],
                    'captain': match['team_b']['captain']
                },
                'lobbies': all_lobby_ids,  # Preserve ALL lobby IDs for removal from queue
                'match_quality': match.get('match_quality', 0.0),
                'map_pool': match.get('map_pool', []),
                'server_pool': match.get('server_pool', []),
                'queue_type': match.get('queue_type', 'pug'),
                'created_at': match.get('created_at')
            }
            
            return converted_match
            
        except Exception as e:
            logger.error(f"Error converting match format: {str(e)}")
            raise

