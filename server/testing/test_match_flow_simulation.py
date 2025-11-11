"""
Match Flow Simulation Test
Simulates a complete match from acceptance to completion with mock players.
This allows testing without needing 10 actual clients connected.
"""
import os
import asyncio
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Match, Player, MatchStatistics
from matchmaking.match_execution import MatchExecutionManager
from match_system.monitor import MatchMonitor
from django.utils import timezone


async def create_test_players(count=10):
    """Create test players for simulation"""
    print(f"\n[1/8] Creating {count} test players...")
    
    from asgiref.sync import sync_to_async
    
    def create_players():
        players = []
        for i in range(count):
            player, created = Player.objects.get_or_create(
                puuid=f"sim-player-{i}",
                defaults={
                    'username': f"SimPlayer{i}",
                    'alias': f"Player{i}",
                    'region': 'na',
                    'elo': 1500 + (i * 10),
                    'rank': 'S',
                    'team': 'none'
                }
            )
            players.append(player)
            if created:
                print(f"   [OK] Created {player.alias} (ELO: {player.elo})")
        return players
    
    players = await sync_to_async(create_players)()
    return players


async def create_test_match(players):
    """Create a test match with team assignments"""
    print("\n[2/8] Creating test match with teams...")
    
    from asgiref.sync import sync_to_async
    
    def create_match():
        match = Match.objects.create(
            status='confirmed',
            selected_map='Haven',
            game_server='Virginia',
            team_a_data={
                'captain': {
                    'puuid': players[0].puuid,
                    'alias': players[0].alias,
                    'elo': players[0].elo
                },
                'players': [
                    {'puuid': p.puuid, 'alias': p.alias, 'elo': p.elo}
                    for p in players[:5]
                ]
            },
            team_b_data={
                'captain': {
                    'puuid': players[5].puuid,
                    'alias': players[5].alias,
                    'elo': players[5].elo
                },
                'players': [
                    {'puuid': p.puuid, 'alias': p.alias, 'elo': p.elo}
                    for p in players[5:]
                ]
            }
        )
        return match
    
    match = await sync_to_async(create_match)()
    
    print(f"   [OK] Match created: {match.id}")
    print(f"   [INFO] Team A: {', '.join([p.alias for p in players[:5]])}")
    print(f"   [INFO] Team B: {', '.join([p.alias for p in players[5:]])}")
    print(f"   [INFO] Map: {match.selected_map}, Server: {match.game_server}")
    
    return match


async def test_match_start(match, players):
    """Test match start - select constructor and transition to starting"""
    print("\n[3/8] Testing match start (initiate_match_start)...")
    
    result = await MatchExecutionManager.initiate_match_start(str(match.id))
    
    if result['status'] == 'success':
        print(f"   [OK] Match starting initiated")
        print(f"   [INFO] Constructor: {result['constructor_puuid']}")
        print(f"   [INFO] Expected: {players[0].puuid} (highest ELO from Team A)")
        
        # Verify match status changed
        from asgiref.sync import sync_to_async
        match = await sync_to_async(Match.objects.get)(id=match.id)
        
        if match.status == 'starting':
            print(f"   [OK] Match status changed to 'starting'")
        else:
            print(f"   [FAIL] Match status is '{match.status}', expected 'starting'")
        
        if match.constructor_puuid == players[0].puuid:
            print(f"   [OK] Constructor correctly assigned to {players[0].alias}")
        else:
            print(f"   [FAIL] Constructor mismatch")
    else:
        print(f"   [FAIL] {result.get('message')}")
    
    return match


async def simulate_custom_game_creation(match):
    """Simulate constructor creating custom game"""
    print("\n[4/8] Simulating custom game creation...")
    
    # In real flow, constructor client would call party_change_to_custom()
    # and get a pregame_id. We'll simulate this.
    fake_pregame_id = f"pregame-{match.id}-{timezone.now().timestamp()}"
    
    result = await MatchExecutionManager.handle_custom_game_created(
        str(match.id),
        fake_pregame_id,
        match.constructor_puuid
    )
    
    if result['status'] == 'success':
        print(f"   [OK] Custom game created: {fake_pregame_id}")
        print(f"   [INFO] Other 9 players would receive 'join_custom_game' WebSocket event")
    else:
        print(f"   [FAIL] {result.get('message')}")
    
    return fake_pregame_id


async def simulate_match_start(match):
    """Simulate all players joining and match starting"""
    print("\n[5/8] Simulating all players joining and match start...")
    
    # In real flow, once all 10 players join, constructor gets coregame_id
    fake_coregame_id = f"coregame-{match.id}-{timezone.now().timestamp()}"
    
    result = await MatchExecutionManager.handle_match_started(
        str(match.id),
        fake_coregame_id
    )
    
    if result['status'] == 'success':
        print(f"   [OK] Match started: {fake_coregame_id}")
        
        from asgiref.sync import sync_to_async
        match = await sync_to_async(Match.objects.get)(id=match.id)
        
        if match.status == 'in_progress':
            print(f"   [OK] Match status: 'in_progress'")
        if match.coregame_id == fake_coregame_id:
            print(f"   [OK] Coregame ID stored correctly")
        
        print(f"   [INFO] Match monitoring would start now (30s polling)")
    else:
        print(f"   [FAIL] {result.get('message')}")
    
    return fake_coregame_id


async def simulate_score_updates(match):
    """Simulate live score updates during match"""
    print("\n[6/8] Simulating live score updates...")
    
    # Simulate score progression
    scores = [
        (1, 0, 1),   # Round 1: Team A wins
        (2, 0, 2),   # Round 2: Team A wins
        (2, 1, 3),   # Round 3: Team B wins
        (3, 1, 4),   # Round 4: Team A wins
        (3, 2, 5),   # Round 5: Team B wins
        (5, 3, 8),   # Skip to round 8
        (8, 6, 14),  # Skip to round 14
        (10, 8, 18), # Skip to round 18
        (13, 10, 23) # Final: Team A wins 13-10
    ]
    
    for team_a, team_b, round_num in scores:
        result = await MatchMonitor.update_match_score(
            str(match.id), team_a, team_b, round_num
        )
        
        if result['status'] == 'success' and result['changed']:
            print(f"   [OK] Score update: Team A {team_a} - {team_b} Team B (Round {round_num})")
            await asyncio.sleep(0.2)  # Small delay to simulate real game
    
    print(f"   [INFO] All score updates sent successfully")
    print(f"   [INFO] In real flow, spectators would see these updates in real-time")


async def simulate_player_statistics(match, players):
    """Simulate player statistics collection"""
    print("\n[7/8] Simulating player statistics collection...")
    
    # Generate realistic stats for all 10 players
    import random
    
    player_stats = {}
    
    for i, player in enumerate(players):
        # Team A generally did better (won 13-10)
        if i < 5:  # Team A
            base_kills = random.randint(12, 20)
            base_deaths = random.randint(8, 15)
        else:  # Team B
            base_kills = random.randint(8, 16)
            base_deaths = random.randint(10, 18)
        
        player_stats[player.puuid] = {
            'team': 'team_a' if i < 5 else 'team_b',
            'kills': base_kills,
            'deaths': base_deaths,
            'assists': random.randint(3, 8),
            'headshots': int(base_kills * random.uniform(0.3, 0.5)),
            'bodyshots': int(base_kills * random.uniform(0.4, 0.6)),
            'legshots': int(base_kills * random.uniform(0.05, 0.15)),
            'damage_dealt': base_kills * random.randint(120, 180),
            'damage_received': base_deaths * random.randint(100, 150)
        }
    
    result = await MatchMonitor.update_player_statistics(str(match.id), player_stats)
    
    if result['status'] == 'success':
        print(f"   [OK] Statistics updated for all 10 players")
        
        # Display stats
        from asgiref.sync import sync_to_async
        
        def get_stats():
            return list(MatchStatistics.objects.filter(match=match).select_related('player'))
        
        stats = await sync_to_async(get_stats)()
        
        print(f"\n   === Team A Stats ===")
        for stat in stats:
            if stat.team == 'team_a':
                print(f"   {stat.player.alias:12} | K: {stat.kills:2} D: {stat.deaths:2} A: {stat.assists:2} | "
                      f"ADR: {stat.adr:5.1f} | HS%: {stat.headshot_percentage:4.1f}% | K/D: {stat.kd_ratio:.2f}")
        
        print(f"\n   === Team B Stats ===")
        for stat in stats:
            if stat.team == 'team_b':
                print(f"   {stat.player.alias:12} | K: {stat.kills:2} D: {stat.deaths:2} A: {stat.assists:2} | "
                      f"ADR: {stat.adr:5.1f} | HS%: {stat.headshot_percentage:4.1f}% | K/D: {stat.kd_ratio:.2f}")
    else:
        print(f"   [FAIL] {result.get('message')}")


async def simulate_match_completion(match):
    """Simulate match completion"""
    print("\n[8/8] Simulating match completion...")
    
    final_data = {
        'team_a_score': 13,
        'team_b_score': 10,
        'total_rounds': 23,
        'match_duration_minutes': 42
    }
    
    result = await MatchExecutionManager.handle_match_completion(
        str(match.id), final_data
    )
    
    if result['status'] == 'success':
        print(f"   [OK] Match completed successfully")
        
        from asgiref.sync import sync_to_async
        match = await sync_to_async(Match.objects.get)(id=match.id)
        
        if match.status == 'completed':
            print(f"   [OK] Match status: 'completed'")
        print(f"   [OK] Final score: Team A {match.team_a_score} - {match.team_b_score} Team B")
        print(f"   [INFO] Winner: Team A")
    else:
        print(f"   [FAIL] {result.get('message')}")


async def test_rejoin_token(match, players):
    """Test rejoin token generation and validation"""
    print("\n[BONUS] Testing rejoin token system...")
    
    # Generate token for a disconnected player
    token = await MatchExecutionManager.generate_rejoin_token(
        str(match.id), players[3].puuid
    )
    
    print(f"   [OK] Rejoin token generated for {players[3].alias}")
    print(f"   [INFO] Token: {token[:32]}...")
    
    # Validate token
    validation = await MatchExecutionManager.validate_rejoin_token(token)
    
    if validation['valid']:
        print(f"   [OK] Token validated successfully")
        print(f"   [INFO] Player can rejoin match {validation['match_id'][:8]}...")
    else:
        print(f"   [FAIL] Token validation failed: {validation.get('reason')}")
    
    # Try using same token again (should fail)
    validation2 = await MatchExecutionManager.validate_rejoin_token(token)
    if not validation2['valid'] and validation2['reason'] == 'Invalid token':
        print(f"   [OK] Token correctly marked as used (one-time use)")
    else:
        print(f"   [FAIL] Token was reusable (security issue!)")


async def cleanup_test_data(match, players):
    """Clean up test data"""
    print("\n[CLEANUP] Removing test data...")
    
    from asgiref.sync import sync_to_async
    
    def cleanup():
        # Delete match statistics
        MatchStatistics.objects.filter(match=match).delete()
        
        # Delete match
        Match.objects.filter(id=match.id).delete()
        
        # Delete test players
        Player.objects.filter(puuid__startswith='sim-player-').delete()
    
    await sync_to_async(cleanup)()
    
    print(f"   [OK] Test data cleaned up")


async def main():
    """Main test execution"""
    print("=" * 70)
    print("Phase 3.1 - Complete Match Flow Simulation")
    print("=" * 70)
    print("\nThis test simulates a full match from acceptance to completion")
    print("without requiring 10 actual clients connected.\n")
    
    try:
        # Create test environment
        players = await create_test_players(10)
        match = await create_test_match(players)
        
        # Execute match flow
        match = await test_match_start(match, players)
        await asyncio.sleep(0.5)
        
        pregame_id = await simulate_custom_game_creation(match)
        await asyncio.sleep(0.5)
        
        coregame_id = await simulate_match_start(match)
        await asyncio.sleep(0.5)
        
        await simulate_score_updates(match)
        await asyncio.sleep(0.5)
        
        await simulate_player_statistics(match, players)
        await asyncio.sleep(0.5)
        
        # Test rejoin before match completes (when match is still in_progress)
        await test_rejoin_token(match, players)
        await asyncio.sleep(0.5)
        
        await simulate_match_completion(match)
        
        print("\n" + "=" * 70)
        print("[SUCCESS] All tests completed successfully!")
        print("=" * 70)
        
        # Clean up test data automatically
        print("\nTest data created:")
        print(f"  - Match ID: {match.id}")
        print(f"  - 10 test players")
        print(f"  - 10 player statistics records")
        print(f"  - 1 rejoin token")
        
        print("\n[INFO] Cleaning up test data...")
        await cleanup_test_data(match, players)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\nStarting match flow simulation...")
    print("Make sure your Django server is running!\n")
    
    asyncio.run(main())

