"""
Test MMR/ELO System Implementation
Tests the dual rating system with adaptive weighting and TrueSkill.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

import asyncio
from scrimgg.models import Player, Lobby
from matchmaking.trueskill_manager import (
    trueskill_mu_to_mmr,
    mmr_to_trueskill_mu,
    apply_uncertainty_decay,
    update_ratings_after_match,
    is_settled,
    TRUESKILL_CONFIG
)
from matchmaking.adaptive_weighting import (
    calculate_adaptive_team_rating,
    get_convergence_state,
    validate_match_quality
)
from matchmaking.matchmaker_v2 import MatchmakerV2


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


async def test_model_defaults():
    """Test that model defaults are correct"""
    print_section("TEST 1: Model Defaults")
    
    # Create a test player
    test_player = Player.objects.create(
        username="test_mmr_player",
        alias="TestMMR",
        puuid="test-mmr-123",
        region="na"
    )
    
    print(f"[OK] Created test player: {test_player.alias}")
    print(f"  Display ELO: {test_player.elo} (expected: 2750)")
    print(f"  Hidden MMR: {test_player.mmr} (expected: 4350.0)")
    print(f"  TrueSkill mu: {test_player.trueskill_mu} (expected: 25.0)")
    print(f"  TrueSkill sigma: {test_player.trueskill_sigma} (expected: 9.0)")
    print(f"  Games played: {test_player.games_played} (expected: 0)")
    print(f"  In placement: {test_player.is_in_placement} (expected: True)")
    print(f"  Is settled: {test_player.is_settled} (expected: False)")
    
    # Verify values
    assert test_player.elo == 2750, f"Expected ELO 2750, got {test_player.elo}"
    assert test_player.mmr == 4350.0, f"Expected MMR 4350.0, got {test_player.mmr}"
    assert test_player.trueskill_mu == 25.0, f"Expected mu 25.0, got {test_player.trueskill_mu}"
    assert test_player.trueskill_sigma == 9.0, f"Expected sigma 9.0, got {test_player.trueskill_sigma}"
    
    print("\n[OK] All model defaults correct!")
    
    # Cleanup
    test_player.delete()
    return True


async def test_trueskill_conversion():
    """Test MMR <-> TrueSkill conversion"""
    print_section("TEST 2: MMR/TrueSkill Conversion")
    
    # Test conversions
    test_cases = [
        (25.0, 4350.0),   # Starting values
        (30.0, 5220.0),   # B+ rank
        (35.0, 6090.0),   # A- rank
        (40.0, 6960.0),   # A+ rank
        (45.0, 7830.0),   # G rank
    ]
    
    for mu, expected_mmr in test_cases:
        calculated_mmr = trueskill_mu_to_mmr(mu)
        back_to_mu = mmr_to_trueskill_mu(calculated_mmr)
        
        print(f"mu={mu:.1f} -> MMR={calculated_mmr:.0f} (expected {expected_mmr:.0f}) -> mu={back_to_mu:.1f}")
        
        assert abs(calculated_mmr - expected_mmr) < 1.0, f"Conversion error: {calculated_mmr} != {expected_mmr}"
        assert abs(back_to_mu - mu) < 0.01, f"Round-trip error: {back_to_mu} != {mu}"
    
    print("\n[OK] All conversions correct!")
    return True


async def test_uncertainty_decay():
    """Test uncertainty decay for returning players"""
    print_section("TEST 3: Uncertainty Decay")
    
    test_cases = [
        (3, 2.8, 1.0, "3 days (no decay)"),
        (14, 2.8, 1.0, "14 days (threshold, no decay)"),
        (21, 2.8, 1.076, "21 days (3 weeks)"),
        (30, 2.8, 1.174, "30 days (1 month)"),
        (45, 2.8, 1.337, "45 days (6+ weeks)"),
        (60, 2.8, 1.5, "60 days (2 months, max)"),
        (90, 2.8, 1.5, "90 days (3 months, capped)"),
    ]
    
    for days, sigma, expected_mult, description in test_cases:
        new_sigma, multiplier = apply_uncertainty_decay(sigma, days)
        expected_sigma = sigma * expected_mult
        
        print(f"{description}:")
        print(f"  Sigma: {sigma} -> {new_sigma:.2f} (expected {expected_sigma:.2f})")
        print(f"  Multiplier: {multiplier:.3f}x (expected {expected_mult:.3f}x)")
        
        assert abs(multiplier - expected_mult) < 0.01, f"Multiplier error: {multiplier} != {expected_mult}"
        assert abs(new_sigma - expected_sigma) < 0.05, f"Sigma error: {new_sigma} != {expected_sigma}"
    
    print("\n[OK] All decay calculations correct!")
    return True


async def test_adaptive_weighting():
    """Test adaptive weighting system"""
    print_section("TEST 4: Adaptive Weighting")
    
    # Create test players with different convergence states
    players_early = [
        Player(elo=2800, mmr=5200, alias=f"Smurf{i}") for i in range(5)
    ]  # Avg gap: 2400
    
    players_mid = [
        Player(elo=3500, mmr=4200, alias=f"Climbing{i}") for i in range(5)
    ]  # Avg gap: 700
    
    players_converged = [
        Player(elo=5200, mmr=5400, alias=f"Settled{i}") for i in range(5)
    ]  # Avg gap: 200
    
    # Test early convergence
    result_early = calculate_adaptive_team_rating(players_early)
    print(f"Early Convergence (avg gap {result_early['avg_gap']:.0f}):")
    print(f"  State: {result_early['convergence_state']} (expected: early)")
    print(f"  Weights: {result_early['mmr_weight']*100:.0f}% MMR / {result_early['display_weight']*100:.0f}% Display")
    print(f"  Team Rating: {result_early['team_rating']:.0f}")
    print(f"  Calculation: ({result_early['avg_mmr']:.0f} × 0.60) + ({result_early['avg_display']:.0f} × 0.40)")
    
    assert result_early['convergence_state'] == 'early'
    assert result_early['mmr_weight'] == 0.60
    assert result_early['display_weight'] == 0.40
    
    # Test mid convergence
    result_mid = calculate_adaptive_team_rating(players_mid)
    print(f"\nMid Convergence (avg gap {result_mid['avg_gap']:.0f}):")
    print(f"  State: {result_mid['convergence_state']} (expected: mid)")
    print(f"  Weights: {result_mid['mmr_weight']*100:.0f}% MMR / {result_mid['display_weight']*100:.0f}% Display")
    print(f"  Team Rating: {result_mid['team_rating']:.0f}")
    
    assert result_mid['convergence_state'] == 'mid'
    assert result_mid['mmr_weight'] == 0.75
    assert result_mid['display_weight'] == 0.25
    
    # Test converged
    result_conv = calculate_adaptive_team_rating(players_converged)
    print(f"\nConverged (avg gap {result_conv['avg_gap']:.0f}):")
    print(f"  State: {result_conv['convergence_state']} (expected: converged)")
    print(f"  Weights: {result_conv['mmr_weight']*100:.0f}% MMR / {result_conv['display_weight']*100:.0f}% Display")
    print(f"  Team Rating: {result_conv['team_rating']:.0f}")
    
    assert result_conv['convergence_state'] == 'converged'
    assert result_conv['mmr_weight'] == 0.85
    assert result_conv['display_weight'] == 0.15
    
    print("\n[OK] All adaptive weighting tests passed!")
    return True


async def test_tolerance_system():
    """Test rank-aware tolerance"""
    print_section("TEST 5: Rank-Aware Tolerance")
    
    test_cases = [
        (8000, 0, 'elite', 750),      # Elite, 0 min
        (8000, 300, 'elite', 1800),   # Elite, 5 min (capped)
        (6000, 0, 'high', 550),       # High, 0 min
        (6000, 360, 'high', 1450),    # High, 6 min
        (5000, 0, 'mid', 450),        # Mid, 0 min
        (5000, 420, 'mid', 1300),     # Mid, 7 min (capped)
        (3500, 0, 'low', 400),        # Low, 0 min
        (2000, 0, 'entry', 500),      # Entry, 0 min
        (2000, 360, 'entry', 1400),   # Entry, 6 min (capped)
    ]
    
    for mmr, time_sec, expected_tier, expected_tol in test_cases:
        tier = MatchmakerV2.get_mmr_tier(mmr)
        tolerance = MatchmakerV2.calculate_hybrid_tolerance(mmr, time_sec)
        
        print(f"MMR {mmr}, {time_sec//60} min:")
        print(f"  Tier: {tier} (expected: {expected_tier})")
        print(f"  Tolerance: ±{tolerance:.0f} (expected: ±{expected_tol})")
        
        assert tier == expected_tier, f"Tier mismatch: {tier} != {expected_tier}"
        assert abs(tolerance - expected_tol) < 10, f"Tolerance mismatch: {tolerance} != {expected_tol}"
    
    print("\n[OK] All tolerance calculations correct!")
    return True


async def test_match_quality_validation():
    """Test match quality validation"""
    print_section("TEST 6: Match Quality Validation")
    
    # Test valid match
    lobby1_data = {
        'team_rating': 5000,
        'avg_mmr': 5200,
        'avg_display': 4600,
    }
    
    lobby2_data = {
        'team_rating': 5100,
        'avg_mmr': 5300,
        'avg_display': 4700,
    }
    
    is_valid, reason = validate_match_quality(lobby1_data, lobby2_data)
    print(f"Valid Match Test:")
    print(f"  Lobby 1: Team Rating {lobby1_data['team_rating']}, MMR {lobby1_data['avg_mmr']}, Display {lobby1_data['avg_display']}")
    print(f"  Lobby 2: Team Rating {lobby2_data['team_rating']}, MMR {lobby2_data['avg_mmr']}, Display {lobby2_data['avg_display']}")
    print(f"  Result: {is_valid} (expected: True)")
    print(f"  Reason: {reason}")
    
    assert is_valid, "Valid match rejected!"
    
    # Test invalid match (MMR diff too large)
    lobby3_data = {
        'team_rating': 5000,
        'avg_mmr': 5000,
        'avg_display': 4800,
    }
    
    lobby4_data = {
        'team_rating': 6000,
        'avg_mmr': 6000,
        'avg_display': 5800,
    }
    
    is_valid, reason = validate_match_quality(lobby3_data, lobby4_data)
    print(f"\nInvalid Match Test (MMR diff: 1000):")
    print(f"  Result: {is_valid} (expected: False)")
    print(f"  Reason: {reason}")
    
    assert not is_valid, "Invalid match accepted!"
    
    print("\n[OK] Match quality validation working!")
    return True


async def simulate_player_journey(player_name, win_rate, games=20):
    """Simulate a player's journey through placement"""
    print_section(f"SIMULATION: {player_name} ({win_rate*100:.0f}% WR)")
    
    player = Player.objects.create(
        username=player_name.lower().replace(" ", "_"),
        alias=player_name,
        puuid=f"sim-{player_name}-{id(player_name)}",
        region="na"
    )
    
    print(f"Starting Stats:")
    print(f"  Display ELO: {player.elo}")
    print(f"  Hidden MMR: {player.mmr:.0f}")
    print(f"  TrueSkill: μ={player.trueskill_mu:.2f}, σ={player.trueskill_sigma:.2f}")
    print(f"  Gap: {abs(player.mmr - player.elo):.0f}")
    
    # Simulate games
    for i in range(games):
        # Create dummy opponent at similar MMR
        opponent = Player(
            elo=player.elo,
            mmr=player.mmr,
            trueskill_mu=player.trueskill_mu,
            trueskill_sigma=player.trueskill_sigma
        )
        
        # Determine win/loss
        import random
        won = random.random() < win_rate
        
        # Update ratings
        if won:
            update_ratings_after_match(player, opponent)
        else:
            update_ratings_after_match(opponent, player)
            # Reload player since opponent was updated
            player.refresh_from_db()
    
    print(f"\nAfter {games} games:")
    print(f"  Display ELO: {player.elo} (change: {player.elo - 2750:+d})")
    print(f"  Hidden MMR: {player.mmr:.0f} (change: {player.mmr - 4350:+.0f})")
    print(f"  TrueSkill: μ={player.trueskill_mu:.2f}, σ={player.trueskill_sigma:.2f}")
    print(f"  Gap: {abs(player.mmr - player.elo):.0f}")
    print(f"  In placement: {player.is_in_placement}")
    print(f"  Is settled: {player.is_settled}")
    
    convergence_state = get_convergence_state(abs(player.mmr - player.elo))
    print(f"  Convergence: {convergence_state}")
    
    # Cleanup
    player.delete()
    return True


async def test_rank_tier_detection():
    """Test MMR tier detection"""
    print_section("TEST 7: MMR Tier Detection")
    
    test_cases = [
        (9000, 'elite'),   # S rank
        (8000, 'elite'),   # G rank
        (7000, 'elite'),   # A+ rank
        (6500, 'high'),    # A rank
        (6000, 'high'),    # A- rank
        (5500, 'mid'),     # B+ rank
        (5000, 'mid'),     # B rank
        (4500, 'mid'),     # B- rank
        (4000, 'low'),     # C+ rank
        (3500, 'low'),     # C rank
        (3000, 'low'),     # C- rank
        (2500, 'entry'),   # D+ rank
        (2000, 'entry'),   # D rank
        (1000, 'entry'),   # D- rank
    ]
    
    for mmr, expected_tier in test_cases:
        tier = MatchmakerV2.get_mmr_tier(mmr)
        status = "[OK]" if tier == expected_tier else "[FAIL]"
        print(f"{status} MMR {mmr}: {tier} (expected: {expected_tier})")
        
        assert tier == expected_tier, f"Tier detection failed for MMR {mmr}"
    
    print("\n[OK] All tier detections correct!")
    return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("  MMR/ELO SYSTEM TEST SUITE")
    print("="*70)
    
    try:
        await test_model_defaults()
        await test_trueskill_conversion()
        await test_uncertainty_decay()
        await test_adaptive_weighting()
        await test_tolerance_system()
        await test_match_quality_validation()
        await test_rank_tier_detection()
        
        # Player journey simulations
        await simulate_player_journey("Average Player", 0.50, games=20)
        await simulate_player_journey("Good Player", 0.70, games=20)
        await simulate_player_journey("Smurf", 0.90, games=10)
        
        print_section("ALL TESTS PASSED!")
        print("The MMR/ELO system is ready for production use.\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)

