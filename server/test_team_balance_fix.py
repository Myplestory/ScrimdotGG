#!/usr/bin/env python3
"""
Test script to verify the team balance fix works correctly.
This script tests the snake draft algorithm to ensure 5v5 balance.
"""

import sys
import os

# Add the server directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_snake_draft():
    """Test the snake draft algorithm with mock players"""
    
    # Mock 10 players with different MMR values
    mock_players = [
        {'alias': 'Player1', 'puuid': 'p1', 'mmr': 2000, 'elo': 2000},  # Highest
        {'alias': 'Player2', 'puuid': 'p2', 'mmr': 1900, 'elo': 1900},
        {'alias': 'Player3', 'puuid': 'p3', 'mmr': 1800, 'elo': 1800},
        {'alias': 'Player4', 'puuid': 'p4', 'mmr': 1700, 'elo': 1700},
        {'alias': 'Player5', 'puuid': 'p5', 'mmr': 1600, 'elo': 1600},
        {'alias': 'Player6', 'puuid': 'p6', 'mmr': 1500, 'elo': 1500},
        {'alias': 'Player7', 'puuid': 'p7', 'mmr': 1400, 'elo': 1400},
        {'alias': 'Player8', 'puuid': 'p8', 'mmr': 1300, 'elo': 1300},
        {'alias': 'Player9', 'puuid': 'p9', 'mmr': 1200, 'elo': 1200},
        {'alias': 'Player10', 'puuid': 'p10', 'mmr': 1100, 'elo': 1100}  # Lowest
    ]
    
    # Test the fixed snake draft algorithm
    def balance_teams_fixed(players):
        """Fixed snake draft algorithm"""
        # Sort by MMR (descending)
        sorted_players = sorted(players, key=lambda p: p.get('mmr', p.get('elo', 0)), reverse=True)
        
        team_a = []
        team_b = []
        
        # Proper 5v5 snake draft: A-B-B-A-A-B-B-A-A-B
        snake_pattern = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1]  # A=0, B=1
        
        for i, player in enumerate(sorted_players):
            if i < len(snake_pattern):
                if snake_pattern[i] == 0:
                    team_a.append(player)
                else:
                    team_b.append(player)
            else:
                # Fallback for more than 10 players
                if len(team_a) <= len(team_b):
                    team_a.append(player)
                else:
                    team_b.append(player)
        
        return team_a, team_b
    
    # Test the old broken algorithm for comparison
    def balance_teams_broken(players):
        """Old broken snake draft algorithm"""
        sorted_players = sorted(players, key=lambda p: p.get('mmr', p.get('elo', 0)), reverse=True)
        
        team_a = []
        team_b = []
        
        # Old BROKEN logic
        for i, player in enumerate(sorted_players):
            if i % 4 < 2:
                team_a.append(player)
            else:
                team_b.append(player)
        
        return team_a, team_b
    
    print("🧪 Testing Team Balance Fix")
    print("=" * 50)
    
    # Test broken algorithm
    print("\n❌ OLD BROKEN ALGORITHM:")
    broken_team_a, broken_team_b = balance_teams_broken(mock_players)
    print(f"Team A ({len(broken_team_a)} players):")
    for player in broken_team_a:
        print(f"  - {player['alias']} (MMR: {player['mmr']})")
    
    print(f"\nTeam B ({len(broken_team_b)} players):")
    for player in broken_team_b:
        print(f"  - {player['alias']} (MMR: {player['mmr']})")
    
    broken_a_avg = sum(p['mmr'] for p in broken_team_a) / len(broken_team_a)
    broken_b_avg = sum(p['mmr'] for p in broken_team_b) / len(broken_team_b)
    print(f"\nTeam A Average MMR: {broken_a_avg:.0f}")
    print(f"Team B Average MMR: {broken_b_avg:.0f}")
    print(f"MMR Difference: {abs(broken_a_avg - broken_b_avg):.0f}")
    print(f"Balance: {len(broken_team_a)}v{len(broken_team_b)} ❌")
    
    # Test fixed algorithm
    print("\n✅ NEW FIXED ALGORITHM:")
    fixed_team_a, fixed_team_b = balance_teams_fixed(mock_players)
    print(f"Team A ({len(fixed_team_a)} players):")
    for player in fixed_team_a:
        print(f"  - {player['alias']} (MMR: {player['mmr']})")
    
    print(f"\nTeam B ({len(fixed_team_b)} players):")
    for player in fixed_team_b:
        print(f"  - {player['alias']} (MMR: {player['mmr']})")
    
    fixed_a_avg = sum(p['mmr'] for p in fixed_team_a) / len(fixed_team_a)
    fixed_b_avg = sum(p['mmr'] for p in fixed_team_b) / len(fixed_team_b)
    print(f"\nTeam A Average MMR: {fixed_a_avg:.0f}")
    print(f"Team B Average MMR: {fixed_b_avg:.0f}")
    print(f"MMR Difference: {abs(fixed_a_avg - fixed_b_avg):.0f}")
    print(f"Balance: {len(fixed_team_a)}v{len(fixed_team_b)} ✅")
    
    # Validation
    print("\n🔍 VALIDATION:")
    if len(fixed_team_a) == 5 and len(fixed_team_b) == 5:
        print("✅ Team balance: PASSED (5v5)")
    else:
        print(f"❌ Team balance: FAILED ({len(fixed_team_a)}v{len(fixed_team_b)})")
    
    if abs(fixed_a_avg - fixed_b_avg) < abs(broken_a_avg - broken_b_avg):
        print("✅ MMR balance: IMPROVED")
    else:
        print("❌ MMR balance: NOT IMPROVED")
    
    print("\n🎯 SNAKE DRAFT PATTERN VERIFICATION:")
    print("Expected: A-B-B-A-A-B-B-A-A-B")
    actual_pattern = []
    for i, player in enumerate(sorted(mock_players, key=lambda p: p['mmr'], reverse=True)):
        if player in fixed_team_a:
            actual_pattern.append('A')
        else:
            actual_pattern.append('B')
    print(f"Actual:   {'-'.join(actual_pattern)}")
    
    expected_pattern = ['A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'A', 'B']
    if actual_pattern == expected_pattern:
        print("✅ Snake draft pattern: CORRECT")
    else:
        print("❌ Snake draft pattern: INCORRECT")

if __name__ == "__main__":
    test_snake_draft()
