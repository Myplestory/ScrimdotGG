"""
Matchmaker Algorithm V2 - With MMR and Adaptive Weighting
Finds compatible lobbies using MMR-based matching and adaptive weighting.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async
import logging
import random

from .queue_manager import QueueManager
from .adaptive_weighting import calculate_adaptive_team_rating, validate_match_quality, ADAPTIVE_WEIGHTING_CONFIG
from .trueskill_manager import TRUESKILL_CONFIG

logger = logging.getLogger(__name__)


class MatchmakerV2:
    """
    Enhanced matchmaking using MMR and adaptive weighting.
    """
    
    # Constants
    PLAYERS_PER_MATCH = 10
    PLAYERS_PER_TEAM = 5
    
    # Rank-aware tolerance (uses MMR tiers from approved distribution)
    HYBRID_TOLERANCE_CONFIG = {
        'elite': {      # MMR 6750+
            'base': 750,
            'per_minute': 210,
            'max': 1800,
        },
        'high': {       # MMR 5750-6749
            'base': 550,
            'per_minute': 150,
            'max': 1500,
        },
        'mid': {        # MMR 4250-5749
            'base': 450,
            'per_minute': 125,
            'max': 1300,
        },
        'low': {        # MMR 2750-4249
            'base': 400,
            'per_minute': 125,
            'max': 1200,
        },
        'entry': {      # MMR 0-2749
            'base': 500,
            'per_minute': 150,
            'max': 1400,
        },
    }
    
    # MMR Distribution thresholds
    MMR_TIERS = {
        'elite': (6750, float('inf')),
        'high': (5750, 6749),
        'mid': (4250, 5749),
        'low': (2750, 4249),
        'entry': (0, 2749),
    }
    
    @staticmethod
    def get_mmr_tier(mmr):
        """Determine MMR tier for tolerance calculations"""
        for tier, (min_mmr, max_mmr) in MatchmakerV2.MMR_TIERS.items():
            if min_mmr <= mmr <= max_mmr:
                return tier
        return 'entry'
    
    @staticmethod
    def calculate_hybrid_tolerance(base_mmr, time_in_queue_seconds):
        """
        Calculate rank-aware tolerance based on MMR tier and time in queue.
        
        Args:
            base_mmr: Average MMR of the lobby
            time_in_queue_seconds: Time spent in queue
        
        Returns:
            float: Tolerance value
        """
        minutes = time_in_queue_seconds / 60
        tier = MatchmakerV2.get_mmr_tier(base_mmr)
        config = MatchmakerV2.HYBRID_TOLERANCE_CONFIG[tier]
        
        tolerance = config['base'] + (config['per_minute'] * minutes)
        return min(tolerance, config['max'])
    
    @staticmethod
    async def find_match(queue_type: str = 'pug') -> Optional[Dict]:
        """
        Main matchmaking function using MMR and adaptive weighting.
        
        Args:
            queue_type: Type of queue
        
        Returns:
            Match data dict or None
        """
        try:
            # Get all lobbies in queue
            queued_lobbies = await QueueManager.get_all_queued_lobbies(queue_type)
            
            if not queued_lobbies:
                logger.debug("No lobbies in queue")
                return None
            
            # Count total players
            total_players = sum(lobby['size'] for lobby in queued_lobbies)
            
            if total_players < MatchmakerV2.PLAYERS_PER_MATCH:
                logger.debug(f"Not enough players: {total_players}/10")
                return None
            
            logger.info(f"Attempting matchmaking with {len(queued_lobbies)} lobbies ({total_players} players)")
            
            # Calculate adaptive team ratings for all lobbies
            lobbies_with_ratings = await MatchmakerV2._enrich_lobbies_with_ratings(queued_lobbies)
            
            # Try to find compatible lobby combinations
            match_lobbies = await MatchmakerV2._find_compatible_lobbies(lobbies_with_ratings)
            
            if not match_lobbies:
                logger.debug("No compatible combinations found")
                return None
            
            # Extract all players
            all_players = []
            for lobby in match_lobbies:
                all_players.extend(lobby['players'])
            
            # Balance teams using MMR
            team_a, team_b = await MatchmakerV2._balance_teams_mmr(all_players)
            
            # Calculate match quality
            match_quality = await MatchmakerV2._calculate_match_quality_mmr(team_a, team_b)
            
            # Determine map and server pools
            map_pool = await MatchmakerV2._determine_map_pool(match_lobbies)
            server_pool = await MatchmakerV2._determine_server_pool(match_lobbies)
            
            # Create match data
            match_data = {
                'lobbies': [lobby['id'] for lobby in match_lobbies],
                'team_a': {
                    'players': team_a,
                    'average_elo': sum(p['elo'] for p in team_a) / len(team_a),
                    'average_mmr': sum(p['mmr'] for p in team_a) / len(team_a),
                    'captain': await MatchmakerV2._select_captain(team_a)
                },
                'team_b': {
                    'players': team_b,
                    'average_elo': sum(p['elo'] for p in team_b) / len(team_b),
                    'average_mmr': sum(p['mmr'] for p in team_b) / len(team_b),
                    'captain': await MatchmakerV2._select_captain(team_b)
                },
                'match_quality': match_quality,
                'map_pool': map_pool,
                'server_pool': server_pool,
                'queue_type': queue_type,
                'created_at': timezone.now().isoformat()
            }
            
            logger.info(f"Match found! Quality: {match_quality:.2f}, "
                       f"Team A MMR: {match_data['team_a']['average_mmr']:.0f}, "
                       f"Team B MMR: {match_data['team_b']['average_mmr']:.0f}")
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error in find_match: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    async def _enrich_lobbies_with_ratings(lobbies: List[Dict]) -> List[Dict]:
        """
        Add adaptive rating data to each lobby.
        """
        from django.apps import apps
        
        Lobby = apps.get_model('scrimgg', 'Lobby')
        
        enriched_lobbies = []
        
        for lobby_data in lobbies:
            try:
                # Get lobby object
                def get_lobby():
                    lobby = Lobby.objects.prefetch_related('players').get(id=lobby_data['id'])
                    players = list(lobby.players.all())
                    return players
                
                players = await sync_to_async(get_lobby)()
                
                # Calculate adaptive team rating
                rating_data = calculate_adaptive_team_rating(players)
                
                # Add rating data to lobby
                lobby_enriched = lobby_data.copy()
                lobby_enriched['team_rating'] = rating_data['team_rating']
                lobby_enriched['avg_mmr'] = rating_data['avg_mmr']
                lobby_enriched['avg_display'] = rating_data['avg_display']
                lobby_enriched['avg_gap'] = rating_data['avg_gap']
                lobby_enriched['convergence_state'] = rating_data['convergence_state']
                
                enriched_lobbies.append(lobby_enriched)
                
            except Exception as e:
                logger.error(f"Error enriching lobby {lobby_data['id']}: {e}")
                continue
        
        return enriched_lobbies
    
    @staticmethod
    async def _find_compatible_lobbies(lobbies: List[Dict]) -> Optional[List[Dict]]:
        """
        Find compatible lobbies using adaptive team ratings and tolerance.
        """
        # Sort by team rating (descending)
        lobbies.sort(key=lambda l: l.get('team_rating', 0), reverse=True)
        
        # Try to find combination that equals 10 players
        for i in range(len(lobbies)):
            lobby1 = lobbies[i]
            
            # Calculate tolerance based on time in queue
            time_in_queue = (timezone.now() - lobby1.get('queued_at', timezone.now())).total_seconds()
            tolerance = MatchmakerV2.calculate_hybrid_tolerance(
                lobby1.get('avg_mmr', 4350),
                time_in_queue
            )
            
            # Try to find complementary lobbies
            for j in range(i + 1, len(lobbies)):
                lobby2 = lobbies[j]
                
                # Check if team ratings are within tolerance
                rating_diff = abs(lobby1['team_rating'] - lobby2['team_rating'])
                
                if rating_diff > tolerance:
                    continue
                
                # Check if player count matches
                total_size = lobby1['size'] + lobby2['size']
                
                if total_size == MatchmakerV2.PLAYERS_PER_MATCH:
                    # Exact match (2 lobbies = 10 players)
                    if await MatchmakerV2._validate_lobby_compatibility(lobby1, lobby2):
                        logger.info(f"Found 2-lobby match: {lobby1['id'][:8]}... + {lobby2['id'][:8]}...")
                        return [lobby1, lobby2]
                
                elif total_size < MatchmakerV2.PLAYERS_PER_MATCH:
                    # Need more lobbies
                    remaining_needed = MatchmakerV2.PLAYERS_PER_MATCH - total_size
                    
                    # Try to find additional lobbies
                    for k in range(j + 1, len(lobbies)):
                        lobby3 = lobbies[k]
                        
                        if lobby3['size'] == remaining_needed:
                            # Check if all three are compatible
                            rating_diff_3 = abs(lobby1['team_rating'] - lobby3['team_rating'])
                            
                            if rating_diff_3 <= tolerance:
                                if await MatchmakerV2._validate_lobby_compatibility_multi([lobby1, lobby2, lobby3]):
                                    logger.info(f"Found 3-lobby match")
                                    return [lobby1, lobby2, lobby3]
        
        return None
    
    @staticmethod
    async def _validate_lobby_compatibility(lobby1: Dict, lobby2: Dict) -> bool:
        """
        Validate that two lobbies are compatible for matching.
        Uses adaptive weighting constraints.
        """
        # Create rating data dicts
        lobby1_data = {
            'team_rating': lobby1.get('team_rating', 0),
            'avg_mmr': lobby1.get('avg_mmr', 0),
            'avg_display': lobby1.get('avg_display', 0),
        }
        
        lobby2_data = {
            'team_rating': lobby2.get('team_rating', 0),
            'avg_mmr': lobby2.get('avg_mmr', 0),
            'avg_display': lobby2.get('avg_display', 0),
        }
        
        is_valid, reason = validate_match_quality(lobby1_data, lobby2_data)
        
        if not is_valid:
            logger.debug(f"Lobby compatibility failed: {reason}")
        
        return is_valid
    
    @staticmethod
    async def _validate_lobby_compatibility_multi(lobbies: List[Dict]) -> bool:
        """
        Validate multiple lobbies are compatible.
        """
        # Check each pair
        for i in range(len(lobbies)):
            for j in range(i + 1, len(lobbies)):
                if not await MatchmakerV2._validate_lobby_compatibility(lobbies[i], lobbies[j]):
                    return False
        return True
    
    @staticmethod
    async def _balance_teams_mmr(players: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Balance players into two teams using MMR.
        Uses snake draft for fairness.
        """
        # Sort by MMR (descending)
        sorted_players = sorted(players, key=lambda p: p.get('mmr', p.get('elo', 0)), reverse=True)
        
        team_a = []
        team_b = []
        
        # Snake draft
        for i, player in enumerate(sorted_players):
            if i % 4 < 2:
                team_a.append(player)
            else:
                team_b.append(player)
        
        return team_a, team_b
    
    @staticmethod
    async def _calculate_match_quality_mmr(team_a: List[Dict], team_b: List[Dict]) -> float:
        """
        Calculate match quality using MMR difference.
        """
        team_a_mmr = sum(p.get('mmr', p.get('elo', 0)) for p in team_a) / len(team_a)
        team_b_mmr = sum(p.get('mmr', p.get('elo', 0)) for p in team_b) / len(team_b)
        
        mmr_diff = abs(team_a_mmr - team_b_mmr)
        
        # Quality score: 1.0 = perfect, decreases with larger difference
        # Max diff of 400 MMR = 0.5 quality
        quality = max(0.5, 1.0 - (mmr_diff / 800))
        
        return quality
    
    @staticmethod
    async def _determine_map_pool(lobbies: List[Dict]) -> List[str]:
        """
        Determine map pool from lobby preferences.
        """
        if not lobbies:
            return []
        
        # Get intersection of all preferences
        map_sets = []
        for lobby in lobbies:
            maps = lobby.get('map_preferences', [])
            if maps:
                map_sets.append(set(maps))
        
        if not map_sets:
            return []
        
        # Intersection
        common_maps = set.intersection(*map_sets) if map_sets else set()
        
        return list(common_maps) if common_maps else []
    
    @staticmethod
    async def _determine_server_pool(lobbies: List[Dict]) -> List[str]:
        """
        Determine server pool from lobby preferences.
        """
        if not lobbies:
            return []
        
        # Get intersection
        server_sets = []
        for lobby in lobbies:
            servers = lobby.get('server_preferences', [])
            if servers:
                server_sets.append(set(servers))
        
        if not server_sets:
            return []
        
        common_servers = set.intersection(*server_sets) if server_sets else set()
        
        return list(common_servers) if common_servers else []
    
    @staticmethod
    async def _select_captain(team: List[Dict]) -> Dict:
        """
        Select team captain (highest MMR player).
        """
        return max(team, key=lambda p: p.get('mmr', p.get('elo', 0)))
    
    @staticmethod
    async def find_matches(queue_type: str = 'pug') -> Dict:
        """
        Find multiple matches in queue (for Celery task).
        """
        try:
            matches_found = []
            max_iterations = 10  # Prevent infinite loops
            
            for iteration in range(max_iterations):
                match = await MatchmakerV2.find_match(queue_type)
                
                if match:
                    # Convert to format expected by confirmation system
                    converted_match = MatchmakerV2._convert_match_format(match)
                    matches_found.append(converted_match)
                    logger.info(f"Found match {len(matches_found)}")
                    
                    # Remove matched lobbies from queue
                    lobby_ids = converted_match.get('lobbies', [])
                    for lobby_id in lobby_ids:
                        try:
                            from django.apps import apps
                            Lobby = apps.get_model('scrimgg', 'Lobby')
                            
                            def get_lobby_leader():
                                lobby = Lobby.objects.select_related('lobby_leader').get(id=lobby_id)
                                return lobby.lobby_leader.puuid if lobby.lobby_leader else None
                            
                            leader_puuid = await sync_to_async(get_lobby_leader)()
                            
                            if leader_puuid:
                                result = await QueueManager.leave_queue(lobby_id, leader_puuid, queue_type)
                                if result.get('status') == 'success':
                                    logger.info(f"Removed lobby {lobby_id} from queue")
                        except Exception as e:
                            logger.error(f"Error removing lobby {lobby_id}: {e}")
                else:
                    break
            
            return {
                'status': 'success',
                'message': f'Found {len(matches_found)} matches',
                'matches_found': len(matches_found),
                'matches': matches_found
            }
            
        except Exception as e:
            logger.error(f"Error finding matches: {e}")
            return {
                'status': 'error',
                'message': f'Failed: {str(e)}',
                'matches_found': 0,
                'matches': []
            }
    
    @staticmethod
    def _convert_match_format(match: Dict) -> Dict:
        """
        Convert match format for confirmation system.
        """
        all_lobby_ids = match.get('lobbies', [])
        
        return {
            'lobby1': {
                'id': all_lobby_ids[0] if len(all_lobby_ids) > 0 else 'team_a',
                'players': match['team_a']['players'],
                'average_elo': match['team_a']['average_elo'],
                'average_mmr': match['team_a'].get('average_mmr', 0),
                'captain': match['team_a']['captain']
            },
            'lobby2': {
                'id': all_lobby_ids[1] if len(all_lobby_ids) > 1 else 'team_b',
                'players': match['team_b']['players'],
                'average_elo': match['team_b']['average_elo'],
                'average_mmr': match['team_b'].get('average_mmr', 0),
                'captain': match['team_b']['captain']
            },
            'lobbies': all_lobby_ids,
            'match_quality': match.get('match_quality', 0.0),
            'map_pool': match.get('map_pool', []),
            'server_pool': match.get('server_pool', []),
            'queue_type': match.get('queue_type', 'pug'),
            'created_at': match.get('created_at')
        }

