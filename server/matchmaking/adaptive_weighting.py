"""
Adaptive Weighting System for Matchmaking
Balances MMR (true skill) and Display ELO (perception) based on convergence state.
"""

import logging

logger = logging.getLogger(__name__)

# Adaptive weighting configuration
ADAPTIVE_WEIGHTING_CONFIG = {
    # Early convergence (large gaps, games 1-20)
    'early': {
        'gap_threshold': 1000,
        'mmr_weight': 0.60,      # 60% skill
        'display_weight': 0.40,  # 40% perception
        'typical_games': '1-20',
        'handles': 'Smurfs, bought accounts, new players'
    },
    
    # Mid convergence (moderate gaps, games 20-45)
    'mid': {
        'gap_threshold': 500,
        'mmr_weight': 0.75,      # 75% skill
        'display_weight': 0.25,  # 25% perception
        'typical_games': '20-45',
        'handles': 'Climbing/falling players, partial convergence'
    },
    
    # Converged (small/no gaps, games 45+)
    'converged': {
        'gap_threshold': 0,
        'mmr_weight': 0.85,      # 85% skill
        'display_weight': 0.15,  # 15% perception
        'typical_games': '45+',
        'handles': 'Settled players, highest game quality'
    },
}

# Matchmaking constraints (quality safeguards)
MATCHMAKING_CONSTRAINTS = {
    'max_mmr_diff': 800,         # Max MMR difference between teams
    'max_display_diff': 1200,    # Max display difference (perception)
    'max_team_balance': 400,     # Max team A vs B imbalance
    'max_individual_gap': 2000,  # Max gap between any 2 players in match
}


def get_convergence_state(avg_gap):
    """
    Determine convergence state based on average MMR-ELO gap.
    
    Args:
        avg_gap: Average absolute difference between MMR and ELO
    
    Returns:
        str: 'early', 'mid', or 'converged'
    """
    if avg_gap > ADAPTIVE_WEIGHTING_CONFIG['early']['gap_threshold']:
        return 'early'      # First 10-20 games
    elif avg_gap > ADAPTIVE_WEIGHTING_CONFIG['mid']['gap_threshold']:
        return 'mid'        # Games 20-45
    else:
        return 'converged'  # Games 45+


def calculate_adaptive_team_rating(players):
    """
    Calculate team rating using adaptive weighting.
    Weights shift from 60/40 → 75/25 → 85/15 as players converge.
    
    Args:
        players: List of Player objects
    
    Returns:
        dict: {
            'team_rating': float,
            'avg_mmr': float,
            'avg_display': float,
            'avg_gap': float,
            'mmr_weight': float,
            'display_weight': float,
            'convergence_state': str
        }
    """
    if not players:
        return {
            'team_rating': 0,
            'avg_mmr': 0,
            'avg_display': 0,
            'avg_gap': 0,
            'mmr_weight': 0,
            'display_weight': 0,
            'convergence_state': 'unknown'
        }
    
    # Calculate totals
    total_mmr = sum(p.mmr for p in players)
    total_display = sum(p.elo for p in players)
    total_gap = sum(abs(p.mmr - p.elo) for p in players)
    
    # Calculate averages
    avg_mmr = total_mmr / len(players)
    avg_display = total_display / len(players)
    avg_gap = total_gap / len(players)
    
    # Determine weights based on convergence state
    convergence_state = get_convergence_state(avg_gap)
    config = ADAPTIVE_WEIGHTING_CONFIG[convergence_state]
    
    mmr_weight = config['mmr_weight']
    display_weight = config['display_weight']
    
    # Calculate weighted team rating
    team_rating = (avg_mmr * mmr_weight) + (avg_display * display_weight)
    
    logger.debug(f"[ADAPTIVE] Avg gap: {avg_gap:.1f}, State: {convergence_state}, "
                f"Weights: {mmr_weight*100:.0f}% MMR / {display_weight*100:.0f}% Display, "
                f"Team Rating: {team_rating:.0f}")
    
    return {
        'team_rating': team_rating,
        'avg_mmr': avg_mmr,
        'avg_display': avg_display,
        'avg_gap': avg_gap,
        'mmr_weight': mmr_weight,
        'display_weight': display_weight,
        'convergence_state': convergence_state
    }


def calculate_lobby_team_rating(lobby):
    """
    Calculate lobby's team rating using adaptive weighting.
    
    Args:
        lobby: Lobby object (Django model)
    
    Returns:
        float: Team rating
    """
    from asgiref.sync import sync_to_async
    
    # Get all players in lobby (sync operation)
    def get_players():
        return list(lobby.players.all())
    
    # For now, call synchronously (will be wrapped in async context)
    try:
        players = get_players()
    except:
        # If called from async context, return 0
        return 0
    
    result = calculate_adaptive_team_rating(players)
    return result['team_rating']


def validate_match_quality(lobby1_data, lobby2_data):
    """
    Validate match quality using both MMR and Display constraints.
    
    Args:
        lobby1_data: Dict with team rating data from calculate_adaptive_team_rating
        lobby2_data: Dict with team rating data from calculate_adaptive_team_rating
    
    Returns:
        (bool, str): (is_valid, reason)
    """
    constraints = MATCHMAKING_CONSTRAINTS
    
    # Constraint 1: MMR difference (primary skill check)
    mmr_diff = abs(lobby1_data['avg_mmr'] - lobby2_data['avg_mmr'])
    if mmr_diff > constraints['max_mmr_diff']:
        return False, f"MMR difference too large: {mmr_diff:.0f} > {constraints['max_mmr_diff']}"
    
    # Constraint 2: Display ELO difference (perception check)
    display_diff = abs(lobby1_data['avg_display'] - lobby2_data['avg_display'])
    if display_diff > constraints['max_display_diff']:
        return False, f"Display ELO difference too large: {display_diff:.0f} > {constraints['max_display_diff']}"
    
    # Constraint 3: Team rating balance
    team_rating_diff = abs(lobby1_data['team_rating'] - lobby2_data['team_rating'])
    if team_rating_diff > constraints['max_team_balance']:
        return False, f"Team balance poor: {team_rating_diff:.0f} > {constraints['max_team_balance']}"
    
    return True, "Match quality acceptable"


def get_lobby_rating_info(lobby):
    """
    Get detailed rating information for a lobby.
    Includes adaptive weighting data.
    
    Args:
        lobby: Lobby object
    
    Returns:
        dict: Rating information
    """
    try:
        players = list(lobby.players.all())
        rating_data = calculate_adaptive_team_rating(players)
        
        return {
            'lobby_id': str(lobby.id),
            'team_rating': rating_data['team_rating'],
            'avg_mmr': rating_data['avg_mmr'],
            'avg_display_elo': rating_data['avg_display'],
            'avg_gap': rating_data['avg_gap'],
            'convergence_state': rating_data['convergence_state'],
            'mmr_weight': rating_data['mmr_weight'],
            'display_weight': rating_data['display_weight'],
            'player_count': len(players),
        }
    except Exception as e:
        logger.error(f"Error getting lobby rating info: {e}")
        return None

