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
import json
import time

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
            logger.info(f"   Step 1: Enriching {len(queued_lobbies)} lobbies with adaptive ratings...")
            lobbies_with_ratings = await MatchmakerV2._enrich_lobbies_with_ratings(queued_lobbies)
            logger.info(f"   Step 1 complete: {len(lobbies_with_ratings)} lobbies enriched")
            
            # Try to find compatible lobby combinations
            logger.info(f"   Step 2: Finding compatible lobby combinations...")
            match_lobbies = await MatchmakerV2._find_compatible_lobbies(lobbies_with_ratings)
            logger.info(f"   Step 2 complete: Found {len(match_lobbies) if match_lobbies else 0} matching lobbies")
            
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
                'match_lobbies': match_lobbies,  # Store full lobby data for later use
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
        Uses data already in lobby_data (from queue_manager serialization).
        """
        logger.info(f"      Enriching {len(lobbies)} lobbies with adaptive ratings...")
        
        enriched_lobbies = []
        
        for idx, lobby_data in enumerate(lobbies, 1):
            try:
                logger.debug(f"      Processing lobby {idx}/{len(lobbies)}: {lobby_data['id'][:8]}...")
                
                # Use player data already in lobby_data (includes ELO and MMR)
                players = lobby_data.get('players', [])
                
                if not players:
                    logger.warning(f"      Lobby {lobby_data['id'][:8]} has no players!")
                    continue
                
                logger.debug(f"      Lobby has {len(players)} players with MMR data")
                
                # Calculate adaptive team rating using the player dicts
                # convert Player objects to dicts if needed
                player_dicts = []
                for p in players:
                    if isinstance(p, dict):
                        player_dicts.append(p)
                    else:
                        # It's a Player model object
                        player_dicts.append({
                            'elo': p.elo,
                            'mmr': p.mmr,
                            'puuid': p.puuid,
                            'alias': p.alias
                        })
                
                # Calculate team rating manually (adaptive weighting logic inline)
                if not player_dicts:
                    continue
                
                total_mmr = sum(p['mmr'] for p in player_dicts)
                total_display = sum(p['elo'] for p in player_dicts)
                total_gap = sum(abs(p['mmr'] - p['elo']) for p in player_dicts)
                
                avg_mmr = total_mmr / len(player_dicts)
                avg_display = total_display / len(player_dicts)
                avg_gap = total_gap / len(player_dicts)
                
                # Determine convergence state and weights
                from .adaptive_weighting import get_convergence_state, ADAPTIVE_WEIGHTING_CONFIG
                convergence_state = get_convergence_state(avg_gap)
                config = ADAPTIVE_WEIGHTING_CONFIG[convergence_state]
                
                mmr_weight = config['mmr_weight']
                display_weight = config['display_weight']
                
                team_rating = (avg_mmr * mmr_weight) + (avg_display * display_weight)
                
                rating_data = {
                    'team_rating': team_rating,
                    'avg_mmr': avg_mmr,
                    'avg_display': avg_display,
                    'avg_gap': avg_gap,
                    'mmr_weight': mmr_weight,
                    'display_weight': display_weight,
                    'convergence_state': convergence_state
                }
                
                # Add rating data to lobby
                lobby_enriched = lobby_data.copy()
                lobby_enriched['team_rating'] = rating_data['team_rating']
                lobby_enriched['avg_mmr'] = rating_data['avg_mmr']
                lobby_enriched['avg_display'] = rating_data['avg_display']
                lobby_enriched['avg_gap'] = rating_data.get('avg_gap', 0)
                lobby_enriched['convergence_state'] = rating_data['convergence_state']
                
                enriched_lobbies.append(lobby_enriched)
                logger.debug(f"      Lobby {idx} enriched: Rating={rating_data['team_rating']:.0f}, State={rating_data['convergence_state']}")
                
            except Exception as e:
                logger.error(f"      Error enriching lobby {lobby_data.get('id', 'unknown')[:8]}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        logger.info(f"      ✅ Enriched {len(enriched_lobbies)}/{len(lobbies)} lobbies successfully")
        return enriched_lobbies
    
    @staticmethod
    async def _find_compatible_lobbies(lobbies: List[Dict]) -> Optional[List[Dict]]:
        """
        Find compatible lobbies using adaptive team ratings and tolerance.
        Supports any combination of 2-10 lobbies that sum to exactly 10 players.
        """
        # Sort by team rating (descending)
        lobbies.sort(key=lambda l: l.get('team_rating', 0), reverse=True)
        
        logger.debug(f"      Searching through {len(lobbies)} lobbies for combinations...")
        
        # Use first lobby as reference for tolerance
        if not lobbies:
            return None
        
        reference_lobby = lobbies[0]
        queued_at = reference_lobby.get('queued_at')
        if isinstance(queued_at, str):
            queued_at = timezone.datetime.fromisoformat(queued_at)
        if not queued_at:
            queued_at = timezone.now()
        
        time_in_queue = (timezone.now() - queued_at).total_seconds()
        tolerance = MatchmakerV2.calculate_hybrid_tolerance(
            reference_lobby.get('avg_mmr', 4350),
            time_in_queue
        )
        
        logger.debug(f"      Reference lobby MMR: {reference_lobby.get('avg_mmr', 0):.0f}, Tolerance: ±{tolerance:.0f}")
        
        # Try to find any combination that sums to 10 players
        # Use recursive backtracking to find valid combinations
        def find_combination(start_idx, current_lobbies, current_size):
            """Recursively find lobby combinations that sum to 10 players"""
            
            # Base case: Found exact match
            if current_size == MatchmakerV2.PLAYERS_PER_MATCH:
                return current_lobbies
            
            # Base case: Exceeded target
            if current_size > MatchmakerV2.PLAYERS_PER_MATCH:
                return None
            
            # Base case: No more lobbies to try
            if start_idx >= len(lobbies):
                return None
            
            # Try adding each remaining lobby
            for i in range(start_idx, len(lobbies)):
                candidate = lobbies[i]
                
                # Check if adding this lobby keeps us compatible
                if not current_lobbies:
                    # First lobby in combination
                    new_lobbies = [candidate]
                    new_size = candidate['size']
                else:
                    # Check if candidate is within tolerance of reference
                    rating_diff = abs(reference_lobby['team_rating'] - candidate['team_rating'])
                    if rating_diff > tolerance:
                        continue  # Skip incompatible lobbies
                    
                    new_lobbies = current_lobbies + [candidate]
                    new_size = current_size + candidate['size']
                
                # Recursively try to complete the combination
                result = find_combination(i + 1, new_lobbies, new_size)
                if result:
                    return result
            
            return None
        
        # Find combination starting from first lobby
        matched_lobbies = find_combination(0, [], 0)
        
        if matched_lobbies:
            lobby_count = len(matched_lobbies)
            total_players = sum(l['size'] for l in matched_lobbies)
            logger.info(f"      ✅ Found {lobby_count}-lobby match (total: {total_players} players)")
            
            # Log the combination
            for idx, lobby in enumerate(matched_lobbies, 1):
                logger.debug(f"         Lobby {idx}: {lobby['id'][:8]}... ({lobby['size']} players, Rating: {lobby['team_rating']:.0f})")
            
            # Validate overall match quality
            if await MatchmakerV2._validate_lobby_compatibility_multi(matched_lobbies):
                return matched_lobbies
            else:
                logger.debug(f"      Match quality validation failed for {lobby_count}-lobby combination")
                return None
        
        logger.debug(f"      No valid combination found within tolerance ±{tolerance:.0f}")
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
        For simplicity with many lobbies, just check overall MMR spread.
        """
        if len(lobbies) <= 1:
            return True
        
        # Get all lobby MMRs
        all_mmrs = [lobby.get('avg_mmr', 0) for lobby in lobbies]
        
        # Check spread
        mmr_spread = max(all_mmrs) - min(all_mmrs)
        max_spread = 1500  # Allow wider spread for multi-lobby matches
        
        if mmr_spread > max_spread:
            logger.debug(f"      MMR spread too large: {mmr_spread:.0f} > {max_spread}")
            return False
        
        logger.debug(f"      MMR spread acceptable: {mmr_spread:.0f} <= {max_spread}")
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
                    logger.info(f"   Step 3: Converting match format...")
                    # Convert to format expected by confirmation system
                    converted_match = MatchmakerV2._convert_match_format(match)
                    matches_found.append(converted_match)
                    logger.info(f"   ✅ Found match {len(matches_found)}, converted successfully")
                    
                    # Remove matched lobbies from queue
                    lobby_ids = converted_match.get('lobbies', [])
                    logger.info(f"   Step 4: Removing {len(lobby_ids)} lobbies from queue...")
                    
                    # Get all match lobbies with their player data
                    match_lobbies_data = match.get('match_lobbies', [])
                    
                    for idx, lobby_id in enumerate(lobby_ids, 1):
                        try:
                            # Get leader PUUID from the match_lobbies data (no database call)
                            leader_puuid = None
                            
                            # Find the lobby in match_lobbies to get its leader
                            for lobby in match_lobbies_data:
                                if lobby.get('id') == lobby_id:
                                    # Get first player as leader
                                    if lobby.get('players'):
                                        leader_puuid = lobby['players'][0]['puuid']
                                    break
                            
                            if leader_puuid:
                                logger.debug(f"      Removing lobby {idx}/{len(lobby_ids)}: {lobby_id[:8]}... (leader: {leader_puuid[:12]}...)")
                                
                                # Use dequeue_lobby directly (Redis only, no DB calls)
                                result = await QueueManager.dequeue_lobby(lobby_id, queue_type)
                                
                                if result.get('status') == 'success':
                                    logger.debug(f"      ✅ Lobby {lobby_id[:8]}... removed from Redis queue")
                                    
                                    # Queue a background task to update database (non-blocking)
                                    from .tasks import update_lobby_queue_status_task
                                    update_lobby_queue_status_task.apply_async(
                                        args=[lobby_id, False],  # in_queue=False
                                        queue='celery'
                                    )
                                else:
                                    logger.warning(f"      Failed to remove lobby {lobby_id[:8]}: {result.get('message')}")
                            else:
                                logger.warning(f"      Could not find leader for lobby {lobby_id[:8]}...")
                        except Exception as e:
                            logger.error(f"      Error removing lobby {lobby_id[:8]}: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                    
                    logger.info(f"   ✅ Step 4 complete: Lobbies removed from queue")
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
        Preserves match_lobbies for proper requeueing.
        """
        all_lobby_ids = match.get('lobbies', [])
        match_lobbies = match.get('match_lobbies', [])
        
        # For multi-lobby matches, we need to create lobby1/lobby2 format
        # by combining all lobbies into two teams
        if len(all_lobby_ids) > 2:
            # Multi-lobby match - combine all lobbies into two teams
            team_a_players = match['team_a']['players']
            team_b_players = match['team_b']['players']
            
            # Create virtual lobby1 and lobby2 from the teams
            lobby1 = {
                'id': 'team_a_combined',
                'players': team_a_players,
                'average_elo': match['team_a']['average_elo'],
                'average_mmr': match['team_a'].get('average_mmr', 0),
                'captain': match['team_a']['captain']
            }
            
            lobby2 = {
                'id': 'team_b_combined',
                'players': team_b_players,
                'average_elo': match['team_b']['average_elo'],
                'average_mmr': match['team_b'].get('average_mmr', 0),
                'captain': match['team_b']['captain']
            }
        else:
            # Standard 2-lobby match
            lobby1 = {
                'id': all_lobby_ids[0] if len(all_lobby_ids) > 0 else 'team_a',
                'players': match['team_a']['players'],
                'average_elo': match['team_a']['average_elo'],
                'average_mmr': match['team_a'].get('average_mmr', 0),
                'captain': match['team_a']['captain']
            }
            
            lobby2 = {
                'id': all_lobby_ids[1] if len(all_lobby_ids) > 1 else 'team_b',
                'players': match['team_b']['players'],
                'average_elo': match['team_b']['average_elo'],
                'average_mmr': match['team_b'].get('average_mmr', 0),
                'captain': match['team_b']['captain']
            }
        
        return {
            'lobby1': lobby1,
            'lobby2': lobby2,
            'lobbies': all_lobby_ids,
            'match_lobbies': match_lobbies,  # Preserve original match_lobbies for requeueing!
            'match_quality': match.get('match_quality', 0.0),
            'map_pool': match.get('map_pool', []),
            'server_pool': match.get('server_pool', []),
            'queue_type': match.get('queue_type', 'pug'),
            'created_at': match.get('created_at')
        }
    
    # ============================================================================
    # SYNCHRONOUS METHODS FOR CELERY TASKS
    # ============================================================================
    
    @staticmethod
    def find_matches_sync(queue_type: str = 'pug') -> Dict:
        """
        Find multiple matches in queue - SYNC version for Celery tasks.
        Mirrors async version but uses sync Redis operations.
        
        Returns:
            Dict with matches found or error
        """
        from django_redis import get_redis_connection
        
        try:
            matches_found = []
            max_iterations = 10  # Prevent infinite loops
            
            for iteration in range(max_iterations):
                match = MatchmakerV2.find_match_sync(queue_type)
                
                if match:
                    logger.info(f"   Step 3: Converting match format...")
                    # Convert to format expected by confirmation system
                    converted_match = MatchmakerV2._convert_match_format(match)
                    matches_found.append(converted_match)
                    logger.info(f"   ✅ Found match {len(matches_found)}, converted successfully")
                    
                    # Remove matched lobbies from queue
                    lobby_ids = converted_match.get('lobbies', [])
                    logger.info(f"   Step 4: Removing {len(lobby_ids)} lobbies from queue...")
                    
                    redis_conn = get_redis_connection("default")
                    queue_key = f"matchmaking:queue:{queue_type}"
                    
                    for lobby_id in lobby_ids:
                        redis_conn.zrem(queue_key, lobby_id)
                        redis_conn.delete(f"matchmaking:lobby_data:{lobby_id}")
                        redis_conn.delete(f"matchmaking:queue_time:{lobby_id}")
                    
                    logger.info(f"   Step 4 complete: Removed {len(lobby_ids)} lobbies from queue")
                else:
                    # No more matches possible
                    break
            
            if matches_found:
                logger.info(f"✅ Matchmaking complete: Found {len(matches_found)} match(es)")
            else:
                logger.debug("No matches found this cycle")
            
            return {
                'status': 'success',
                'matches_found': len(matches_found),
                'matches': matches_found
            }
            
        except Exception as e:
            logger.error(f"Error in find_matches (sync): {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': f'Matchmaking failed: {str(e)}',
                'matches_found': 0,
                'matches': []
            }
    
    @staticmethod
    def find_match_sync(queue_type: str = 'pug') -> Optional[Dict]:
        """
        Find a single match from queue - SYNC version for Celery tasks.
        Main matchmaking function using MMR and adaptive weighting.
        
        Returns:
            Match data dict or None
        """
        try:
            # Get all lobbies in queue
            queued_lobbies = QueueManager.get_all_queued_lobbies_sync(queue_type)
            
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
            logger.info(f"   Step 1: Enriching {len(queued_lobbies)} lobbies with adaptive ratings...")
            lobbies_with_ratings = MatchmakerV2._enrich_lobbies_with_ratings_sync(queued_lobbies)
            logger.info(f"   Step 1 complete: {len(lobbies_with_ratings)} lobbies enriched")
            
            # Try to find compatible lobby combinations
            logger.info(f"   Step 2: Finding compatible lobby combinations...")
            match_lobbies = MatchmakerV2._find_compatible_lobbies_sync(lobbies_with_ratings)
            logger.info(f"   Step 2 complete: Found {len(match_lobbies) if match_lobbies else 0} matching lobbies")
            
            if not match_lobbies:
                logger.debug("No compatible combinations found")
                return None
            
            # Extract all players
            all_players = []
            for lobby in match_lobbies:
                all_players.extend(lobby['players'])
            
            # Balance teams using MMR
            team_a, team_b = MatchmakerV2._balance_teams_mmr_sync(all_players)
            
            # Calculate match quality
            match_quality = MatchmakerV2._calculate_match_quality_mmr_sync(team_a, team_b)
            
            # Determine map and server pools
            map_pool = MatchmakerV2._determine_map_pool_sync(match_lobbies)
            server_pool = MatchmakerV2._determine_server_pool_sync(match_lobbies)
            
            # Create match data
            match_data = {
                'lobbies': [lobby['id'] for lobby in match_lobbies],
                'match_lobbies': match_lobbies,  # Store full lobby data for later use
                'team_a': {
                    'players': team_a,
                    'average_elo': sum(p['elo'] for p in team_a) / len(team_a),
                    'average_mmr': sum(p['mmr'] for p in team_a) / len(team_a),
                    'captain': MatchmakerV2._select_captain_sync(team_a)
                },
                'team_b': {
                    'players': team_b,
                    'average_elo': sum(p['elo'] for p in team_b) / len(team_b),
                    'average_mmr': sum(p['mmr'] for p in team_b) / len(team_b),
                    'captain': MatchmakerV2._select_captain_sync(team_b)
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
            logger.error(f"Error in find_match (sync): {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _enrich_lobbies_with_ratings_sync(lobbies: List[Dict]) -> List[Dict]:
        """
        Add adaptive rating data to each lobby - SYNC version.
        Uses data already in lobby_data (from queue_manager serialization).
        """
        logger.info(f"      Enriching {len(lobbies)} lobbies with adaptive ratings...")
        
        enriched_lobbies = []
        
        for idx, lobby_data in enumerate(lobbies, 1):
            try:
                logger.debug(f"      Processing lobby {idx}/{len(lobbies)}: {lobby_data['id'][:8]}...")
                
                # Use player data already in lobby_data (includes ELO and MMR)
                players = lobby_data.get('players', [])
                
                if not players:
                    logger.warning(f"      Lobby {lobby_data['id'][:8]} has no players!")
                    continue
                
                logger.debug(f"      Lobby has {len(players)} players with MMR data")
                
                # Calculate adaptive team rating using the player dicts
                player_dicts = []
                for p in players:
                    if isinstance(p, dict):
                        player_dicts.append(p)
                    else:
                        # It's a Player model object (shouldn't happen in queue data)
                        player_dicts.append({
                            'elo': p.elo,
                            'mmr': p.mmr,
                            'puuid': p.puuid,
                            'alias': p.alias
                        })
                
                # Calculate team rating manually (adaptive weighting logic inline)
                if not player_dicts:
                    continue
                
                total_mmr = sum(p['mmr'] for p in player_dicts)
                total_display = sum(p['elo'] for p in player_dicts)
                total_gap = sum(abs(p['mmr'] - p['elo']) for p in player_dicts)
                
                avg_mmr = total_mmr / len(player_dicts)
                avg_display = total_display / len(player_dicts)
                avg_gap = total_gap / len(player_dicts)
                
                # Determine convergence state and weights
                from .adaptive_weighting import get_convergence_state, ADAPTIVE_WEIGHTING_CONFIG
                convergence_state = get_convergence_state(avg_gap)
                config = ADAPTIVE_WEIGHTING_CONFIG[convergence_state]
                
                mmr_weight = config['mmr_weight']
                display_weight = config['display_weight']
                
                team_rating = (avg_mmr * mmr_weight) + (avg_display * display_weight)
                
                rating_data = {
                    'team_rating': team_rating,
                    'avg_mmr': avg_mmr,
                    'avg_display': avg_display,
                    'avg_gap': avg_gap,
                    'mmr_weight': mmr_weight,
                    'display_weight': display_weight,
                    'convergence_state': convergence_state
                }
                
                # Add rating data to lobby
                lobby_enriched = lobby_data.copy()
                lobby_enriched['team_rating'] = rating_data['team_rating']
                lobby_enriched['avg_mmr'] = rating_data['avg_mmr']
                lobby_enriched['avg_display'] = rating_data['avg_display']
                lobby_enriched['avg_gap'] = rating_data.get('avg_gap', 0)
                lobby_enriched['convergence_state'] = rating_data['convergence_state']
                
                enriched_lobbies.append(lobby_enriched)
                logger.debug(f"      Lobby {idx} enriched: Rating={rating_data['team_rating']:.0f}, State={rating_data['convergence_state']}")
                
            except Exception as e:
                logger.error(f"      Error enriching lobby {lobby_data.get('id', 'unknown')[:8]}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        logger.info(f"      ✅ Enriched {len(enriched_lobbies)}/{len(lobbies)} lobbies successfully")
        return enriched_lobbies
    
    @staticmethod
    def _find_compatible_lobbies_sync(lobbies: List[Dict]) -> Optional[List[Dict]]:
        """
        Find compatible lobbies using adaptive team ratings and tolerance - SYNC version.
        Supports any combination of 2-10 lobbies that sum to exactly 10 players.
        """
        # Sort by team rating (descending)
        lobbies.sort(key=lambda l: l.get('team_rating', 0), reverse=True)
        
        logger.debug(f"      Searching through {len(lobbies)} lobbies for combinations...")
        
        # Use first lobby as reference for tolerance
        if not lobbies:
            return None
        
        reference_lobby = lobbies[0]
        queued_at = reference_lobby.get('queued_at')
        if isinstance(queued_at, str):
            queued_at = timezone.datetime.fromisoformat(queued_at)
        if not queued_at:
            queued_at = timezone.now()
        
        time_in_queue = (timezone.now() - queued_at).total_seconds()
        tolerance = MatchmakerV2.calculate_hybrid_tolerance(
            reference_lobby.get('avg_mmr', 4350),
            time_in_queue
        )
        
        logger.debug(f"      Reference lobby MMR: {reference_lobby.get('avg_mmr', 0):.0f}, Tolerance: ±{tolerance:.0f}")
        
        # Try to find any combination that sums to 10 players
        # Use recursive backtracking to find valid combinations
        def find_combination(start_idx, current_lobbies, current_size):
            """Recursively find lobby combinations that sum to 10 players"""
            
            # Base case: Found exact match
            if current_size == MatchmakerV2.PLAYERS_PER_MATCH:
                return current_lobbies
            
            # Base case: Exceeded target
            if current_size > MatchmakerV2.PLAYERS_PER_MATCH:
                return None
            
            # Base case: No more lobbies to try
            if start_idx >= len(lobbies):
                return None
            
            # Try adding each remaining lobby
            for i in range(start_idx, len(lobbies)):
                candidate = lobbies[i]
                
                # Check if adding this lobby keeps us compatible
                if not current_lobbies:
                    # First lobby in combination
                    new_lobbies = [candidate]
                    new_size = candidate['size']
                else:
                    # Check if candidate is within tolerance of reference
                    rating_diff = abs(reference_lobby['team_rating'] - candidate['team_rating'])
                    if rating_diff > tolerance:
                        continue  # Skip incompatible lobbies
                    
                    new_lobbies = current_lobbies + [candidate]
                    new_size = current_size + candidate['size']
                
                # Recursively try to complete the combination
                result = find_combination(i + 1, new_lobbies, new_size)
                if result:
                    return result
            
            return None
        
        # Find combination starting from first lobby
        matched_lobbies = find_combination(0, [], 0)
        
        if matched_lobbies:
            lobby_count = len(matched_lobbies)
            total_players = sum(l['size'] for l in matched_lobbies)
            logger.info(f"      ✅ Found {lobby_count}-lobby match (total: {total_players} players)")
            
            # Log the combination
            for idx, lobby in enumerate(matched_lobbies, 1):
                logger.debug(f"         Lobby {idx}: {lobby['id'][:8]}... ({lobby['size']} players, Rating: {lobby['team_rating']:.0f})")
            
            # Validate overall match quality
            if MatchmakerV2._validate_lobby_compatibility_multi_sync(matched_lobbies):
                return matched_lobbies
            else:
                logger.debug(f"      Match quality validation failed for {lobby_count}-lobby combination")
                return None
        
        logger.debug(f"      No valid combination found within tolerance ±{tolerance:.0f}")
        return None
    
    @staticmethod
    def _validate_lobby_compatibility_multi_sync(lobbies: List[Dict]) -> bool:
        """
        Validate multiple lobbies are compatible - SYNC version.
        For simplicity with many lobbies, just check overall MMR spread.
        """
        if len(lobbies) <= 1:
            return True
        
        # Get all lobby MMRs
        all_mmrs = [lobby.get('avg_mmr', 0) for lobby in lobbies]
        
        # Check spread
        mmr_spread = max(all_mmrs) - min(all_mmrs)
        max_spread = 1500  # Allow wider spread for multi-lobby matches
        
        if mmr_spread > max_spread:
            logger.debug(f"      MMR spread too large: {mmr_spread:.0f} > {max_spread}")
            return False
        
        logger.debug(f"      MMR spread acceptable: {mmr_spread:.0f} <= {max_spread}")
        return True
    
    @staticmethod
    def _balance_teams_mmr_sync(players: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Balance players into two teams using MMR - SYNC version.
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
    def _calculate_match_quality_mmr_sync(team_a: List[Dict], team_b: List[Dict]) -> float:
        """
        Calculate match quality using MMR difference - SYNC version.
        """
        team_a_mmr = sum(p.get('mmr', p.get('elo', 0)) for p in team_a) / len(team_a)
        team_b_mmr = sum(p.get('mmr', p.get('elo', 0)) for p in team_b) / len(team_b)
        
        mmr_diff = abs(team_a_mmr - team_b_mmr)
        
        # Quality score: 1.0 = perfect, decreases with larger difference
        # Max diff of 400 MMR = 0.5 quality
        quality = max(0.5, 1.0 - (mmr_diff / 800))
        
        return quality
    
    @staticmethod
    def _determine_map_pool_sync(lobbies: List[Dict]) -> List[str]:
        """
        Determine map pool from lobby preferences - SYNC version.
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
    def _determine_server_pool_sync(lobbies: List[Dict]) -> List[str]:
        """
        Determine server pool from lobby preferences - SYNC version.
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
        
        # Intersection
        common_servers = set.intersection(*server_sets) if server_sets else set()
        
        return list(common_servers) if common_servers else []
    
    @staticmethod
    def _select_captain_sync(team: List[Dict]) -> Dict:
        """
        Select team captain (highest MMR player) - SYNC version.
        """
        if not team:
            return None
        return max(team, key=lambda p: p.get('mmr', p.get('elo', 0)))
    