"""
TrueSkill Rating System Manager
Handles skill rating calculations, uncertainty management, and rating updates.
"""

from trueskill import TrueSkill, Rating, rate_1vs1
import time
import logging

logger = logging.getLogger(__name__)

# TrueSkill environment configuration (45-60 game convergence)
ts_env = TrueSkill(
    mu=25.0,              # Starting skill (maps to 4350 MMR)
    sigma=9.0,            # Initial uncertainty (settles in 45-60 games)
    beta=4.5,             # Skill variance
    tau=0.083,            # Dynamic factor (standard)
    draw_probability=0.0  # No draws in Valorant
)

# Configuration
TRUESKILL_CONFIG = {
    # TrueSkill parameters
    'mu': 25.0,
    'sigma': 9.0,
    'beta': 4.5,
    'tau': 0.083,
    'draw_probability': 0.0,
    
    # Convergence tracking
    'settled_sigma': 3.0,      # σ < 3.0 = settled
    'highly_confident': 2.0,   # σ < 2.0 = highly confident
    'expected_games_min': 45,  # Fast convergers
    'expected_games_avg': 52,  # Average convergers
    'expected_games_max': 60,  # Slow convergers
    
    # MMR scaling
    'default_mmr': 4350.0,     # Maps to mu=25.0
    'scaling_factor': 174.0,   # 4350 / 25 = 174
}

# Uncertainty decay configuration (returning players)
UNCERTAINTY_DECAY_CONFIG = {
    'min_days_for_decay': 14,      # 2 weeks (no decay below this)
    'max_days_for_decay': 60,      # 2 months (max decay at this point)
    'max_decay_multiplier': 1.5,   # 1.5x sigma increase
    'max_sigma_cap': 9.0,          # Don't exceed new player uncertainty
}


def trueskill_mu_to_mmr(mu):
    """Convert TrueSkill mu to MMR"""
    return mu * TRUESKILL_CONFIG['scaling_factor']


def mmr_to_trueskill_mu(mmr):
    """Convert MMR to TrueSkill mu"""
    return mmr / TRUESKILL_CONFIG['scaling_factor']


def get_conservative_rating(mu, sigma):
    """
    Get conservative rating (used for matchmaking).
    Conservative = mu - 3*sigma
    """
    return mu - (3 * sigma)


def is_settled(sigma):
    """Check if player rating has settled (σ < 3.0)"""
    return sigma < TRUESKILL_CONFIG['settled_sigma']


def get_confidence_level(sigma):
    """Get confidence level description"""
    if sigma < 2.0:
        return 'highly_confident'  # 70+ games
    elif sigma < 3.0:
        return 'confident'         # 45-60 games
    elif sigma < 5.0:
        return 'moderate'          # 20-40 games
    elif sigma < 7.0:
        return 'low'               # 5-15 games
    else:
        return 'very_uncertain'    # 0-5 games


def apply_uncertainty_decay(current_sigma, days_since_last):
    """
    Apply uncertainty decay for returning players.
    Linear scaling from 1.0x (14 days) to 1.5x (60+ days).
    
    Args:
        current_sigma: Current uncertainty value
        days_since_last: Days since last game
    
    Returns:
        (new_sigma, decay_multiplier)
    """
    config = UNCERTAINTY_DECAY_CONFIG
    
    MIN_DAYS = config['min_days_for_decay']
    MAX_DAYS = config['max_days_for_decay']
    MAX_MULT = config['max_decay_multiplier']
    
    if days_since_last <= MIN_DAYS:
        # No decay (recent activity)
        return current_sigma, 1.0
    
    elif days_since_last >= MAX_DAYS:
        # Max decay (2+ months)
        decay_multiplier = MAX_MULT
    
    else:
        # Linear interpolation between 1.0x and 1.5x
        days_in_range = days_since_last - MIN_DAYS
        total_range = MAX_DAYS - MIN_DAYS  # 46 days
        progress = days_in_range / total_range
        
        # Linear scale: 1.0 + (0.5 * progress)
        decay_multiplier = 1.0 + (0.5 * progress)
    
    # Apply decay
    new_sigma = current_sigma * decay_multiplier
    
    # Cap at max
    new_sigma = min(new_sigma, config['max_sigma_cap'])
    
    return new_sigma, decay_multiplier


def update_ratings_after_match(winner, loser, winner_performance=None, loser_performance=None):
    """
    Update both players' ratings after a match using TrueSkill.
    
    Args:
        winner: Player object (Django model)
        loser: Player object (Django model)
        winner_performance: Optional performance stats dict
        loser_performance: Optional performance stats dict
    
    Returns:
        Dict with rating changes
    """
    # Create TrueSkill Rating objects
    winner_rating = Rating(mu=winner.trueskill_mu, sigma=winner.trueskill_sigma)
    loser_rating = Rating(mu=loser.trueskill_mu, sigma=loser.trueskill_sigma)
    
    # Calculate new ratings (TrueSkill does the math)
    new_winner_rating, new_loser_rating = rate_1vs1(
        winner_rating, 
        loser_rating,
        env=ts_env
    )
    
    # Calculate MMR changes
    old_winner_mmr = winner.mmr
    old_loser_mmr = loser.mmr
    
    # Update TrueSkill components
    winner.trueskill_mu = new_winner_rating.mu
    winner.trueskill_sigma = new_winner_rating.sigma
    loser.trueskill_mu = new_loser_rating.mu
    loser.trueskill_sigma = new_loser_rating.sigma
    
    # Convert TrueSkill mu to MMR (our scale)
    winner.mmr = trueskill_mu_to_mmr(new_winner_rating.mu)
    loser.mmr = trueskill_mu_to_mmr(new_loser_rating.mu)
    
    # Calculate ELO changes (with gap multipliers)
    winner_elo_change = calculate_elo_change(winner, 'win', winner_performance)
    loser_elo_change = calculate_elo_change(loser, 'loss', loser_performance)
    
    # Update display ELO
    winner.elo += winner_elo_change
    loser.elo += loser_elo_change
    
    # Update game counts
    winner.games_played += 1
    loser.games_played += 1
    
    # Update activity timestamp
    winner.last_game_timestamp = time.time()
    loser.last_game_timestamp = time.time()
    
    # Check placement status
    if winner.games_played >= 10:
        winner.is_in_placement = False
    if loser.games_played >= 10:
        loser.is_in_placement = False
    
    # Check settled status
    winner.is_settled = is_settled(new_winner_rating.sigma)
    loser.is_settled = is_settled(new_loser_rating.sigma)
    
    # Save both players
    winner.save()
    loser.save()
    
    logger.info(f"[TRUESKILL] Winner {winner.alias}: μ={winner.trueskill_mu:.2f}, σ={winner.trueskill_sigma:.2f}, MMR={winner.mmr:.0f}, ELO={winner.elo}")
    logger.info(f"[TRUESKILL] Loser {loser.alias}: μ={loser.trueskill_mu:.2f}, σ={loser.trueskill_sigma:.2f}, MMR={loser.mmr:.0f}, ELO={loser.elo}")
    
    return {
        'winner': {
            'mmr_change': winner.mmr - old_winner_mmr,
            'elo_change': winner_elo_change,
            'new_mmr': winner.mmr,
            'new_elo': winner.elo,
            'new_sigma': winner.trueskill_sigma,
        },
        'loser': {
            'mmr_change': loser.mmr - old_loser_mmr,
            'elo_change': loser_elo_change,
            'new_mmr': loser.mmr,
            'new_elo': loser.elo,
            'new_sigma': loser.trueskill_sigma,
        }
    }


def calculate_elo_change(player, result, performance=None):
    """
    Calculate ELO change based on MMR-ELO gap.
    Larger gaps = faster convergence.
    
    Args:
        player: Player object
        result: 'win' or 'loss'
        performance: Optional performance stats
    
    Returns:
        int: ELO change amount
    """
    base_change = 25  # Base ±25 ELO per game
    
    # Calculate MMR-ELO gap
    mmr_elo_gap = player.mmr - player.elo
    
    # Calculate gap multiplier
    abs_gap = abs(mmr_elo_gap)
    if abs_gap > 500:
        gap_multiplier = 3.0  # 3x gains/losses
    elif abs_gap > 300:
        gap_multiplier = 2.5  # 2.5x
    elif abs_gap > 150:
        gap_multiplier = 2.0  # 2x
    else:
        gap_multiplier = 1.0  # Normal (aligned)
    
    # Placement bonus
    if player.is_in_placement:
        gap_multiplier *= 1.5  # Extra 1.5x during first 10 games
    
    # Performance bonus (if provided)
    if performance and performance.get('exceptional', False):
        gap_multiplier *= 1.3  # Extra 1.3x for exceptional play
    
    # Calculate final change
    if result == 'win':
        elo_change = base_change * gap_multiplier
    else:
        elo_change = -base_change * gap_multiplier
    
    return int(elo_change)


def get_expected_games_to_settle(current_sigma):
    """
    Estimate games remaining until settlement (σ < 3.0).
    
    Args:
        current_sigma: Current uncertainty value
    
    Returns:
        int: Estimated games remaining
    """
    if current_sigma <= 3.0:
        return 0  # Already settled
    
    # Rough approximation: σ decreases by ~0.12 per game on average
    sigma_decrease_rate = 0.12
    sigma_remaining = current_sigma - 3.0
    games_remaining = int(sigma_remaining / sigma_decrease_rate)
    
    return games_remaining

