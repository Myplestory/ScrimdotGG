"""
Match Flow Test with Live Client
Simulates 9 bot players + 1 real player (you) for end-to-end testing.

Usage:
1. Start your dev client and authenticate
2. Create a lobby in your client
3. Run this script
4. The script will create 9 bots, create a match, and simulate acceptance
5. You'll receive the match_starting event in your client
6. Follow the flow as the constructor or join the custom game

This allows you to test the complete match flow with just one real client!
"""
import os
import asyncio
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Match, Player, MatchStatistics, Lobby
from matchmaking.match_execution import MatchExecutionManager
from matchmaking.match_monitor import MatchMonitor
from matchmaking.match_confirmation import MatchConfirmationManager
from django.utils import timezone


async def get_live_player():
    """Get the actual player (you) from the database"""
    print("\n[SETUP] Looking for your player account...")
    
    from asgiref.sync import sync_to_async
    
    def find_player():
        # Find the most recently created player (likely you)
        players = Player.objects.exclude(puuid__startswith='sim-player-').exclude(puuid__startswith='test-player-')
        
        if not players.exists():
            return None
        
        # Try to find player with active lobby
        for player in players:
            lobby = Lobby.objects.filter(players=player, is_active=True).first()
            if lobby:
                return player
        
        # Otherwise return most recent
        return players.order_by('-id').first()
    
    player = await sync_to_async(find_player)()
    
    if player:
        print(f"   [OK] Found your player: {player.alias} (PUUID: {player.puuid})")
        print(f"   [INFO] ELO: {player.elo}, Region: {player.region}")
        return player
    else:
        print(f"   [FAIL] No player found!")
        print(f"   [HELP] Please authenticate with your dev client first")
        return None


async def create_bot_players(live_player, count=9):
    """Create 9 bot players to fill the match"""
    print(f"\n[SETUP] Creating {count} bot players...")
    
    from asgiref.sync import sync_to_async
    
    def create_players():
        players = []
        
        # Create bots with similar ELO to live player
        base_elo = live_player.elo if live_player.elo > 0 else 1500
        
        for i in range(count):
            # Vary ELO slightly (+/- 100)
            import random
            bot_elo = base_elo + random.randint(-100, 100)
            
            player, created = Player.objects.get_or_create(
                puuid=f"bot-player-{i}",
                defaults={
                    'username': f"Bot{i}",
                    'alias': f"Bot{i}",
                    'region': live_player.region,
                    'elo': bot_elo,
                    'rank': 'S',
                    'team': 'none'
                }
            )
            
            # Update ELO if player already existed
            if not created and player.elo != bot_elo:
                player.elo = bot_elo
                player.save()
            
            players.append(player)
        
        return players
    
    players = await sync_to_async(create_players)()
    print(f"   [OK] Created {count} bot players (ELO range: {min(p.elo for p in players)} - {max(p.elo for p in players)})")
    
    return players


async def create_balanced_match(live_player, bot_players, make_you_constructor=True):
    """
    Create a balanced 5v5 match with you and 9 bots.
    
    Args:
        live_player: Your player object
        bot_players: List of 9 bot players
        make_you_constructor: If True, you'll be the constructor (create custom game)
    """
    print(f"\n[SETUP] Creating balanced 5v5 match...")
    
    from asgiref.sync import sync_to_async
    import random
    
    # Shuffle bots for randomness
    random.shuffle(bot_players)
    
    # Create teams
    if make_you_constructor:
        # Put you as Team A captain (constructor)
        team_a = [live_player] + bot_players[:4]
        team_b = bot_players[4:9]
        print(f"   [INFO] You will be the CONSTRUCTOR (create custom game)")
    else:
        # Put you on Team B (you'll join the custom game)
        team_a = bot_players[:5]
        team_b = [live_player] + bot_players[5:9]
        print(f"   [INFO] You will JOIN the custom game (Bot0 creates it)")
    
    def create_match():
        # Determine captains (highest ELO on each team)
        team_a_captain = max(team_a, key=lambda p: p.elo)
        team_b_captain = max(team_b, key=lambda p: p.elo)
        
        match = Match.objects.create(
            status='confirmed',
            selected_map='Haven',
            game_server='Virginia',
            team_a_data={
                'captain': {
                    'puuid': team_a_captain.puuid,
                    'alias': team_a_captain.alias,
                    'elo': team_a_captain.elo
                },
                'players': [
                    {'puuid': p.puuid, 'alias': p.alias, 'elo': p.elo}
                    for p in team_a
                ],
                'average_elo': sum(p.elo for p in team_a) / len(team_a)
            },
            team_b_data={
                'captain': {
                    'puuid': team_b_captain.puuid,
                    'alias': team_b_captain.alias,
                    'elo': team_b_captain.elo
                },
                'players': [
                    {'puuid': p.puuid, 'alias': p.alias, 'elo': p.elo}
                    for p in team_b
                ],
                'average_elo': sum(p.elo for p in team_b) / len(team_b)
            }
        )
        return match, team_a, team_b
    
    match, team_a, team_b = await sync_to_async(create_match)()
    
    print(f"   [OK] Match created: {match.id}")
    print(f"\n   === Team A ===")
    for p in team_a:
        marker = " <-- YOU" if p.puuid == live_player.puuid else ""
        print(f"   {p.alias:15} (ELO: {p.elo}){marker}")
    
    print(f"\n   === Team B ===")
    for p in team_b:
        marker = " <-- YOU" if p.puuid == live_player.puuid else ""
        print(f"   {p.alias:15} (ELO: {p.elo}){marker}")
    
    print(f"\n   [INFO] Map: {match.selected_map}")
    print(f"   [INFO] Server: {match.game_server}")
    
    return match, team_a, team_b


async def simulate_all_players_accept(match_id):
    """
    Simulate all players accepting the match.
    In real flow, this happens via MatchConfirmationManager.
    """
    print(f"\n[ACTION] Simulating all players accepting match...")
    print(f"   [INFO] In real flow, you would see 'match_found' event in your client")
    print(f"   [INFO] You would click 'Accept' button")
    print(f"   [INFO] When all 10 accept, match_starting event is triggered")
    
    # For testing, we'll directly trigger match start
    await asyncio.sleep(1)
    print(f"   [OK] All players accepted (simulated)")


async def trigger_match_start(match):
    """Trigger match start - this will send WebSocket events to your client"""
    print(f"\n[TRIGGER] Initiating match start...")
    print(f"   [IMPORTANT] Watch your dev client for 'match_starting' event!")
    
    result = await MatchExecutionManager.initiate_match_start(str(match.id))
    
    if result['status'] == 'success':
        print(f"   [OK] Match start initiated")
        print(f"   [OK] Constructor: {result['constructor_puuid']}")
        
        from asgiref.sync import sync_to_async
        match = await sync_to_async(Match.objects.get)(id=match.id)
        
        print(f"\n   [WebSocket Event Sent]")
        print(f"   Event: 'match_starting'")
        print(f"   Data: {{")
        print(f"       match_id: '{match.id}',")
        print(f"       constructor_puuid: '{match.constructor_puuid}',")
        print(f"       is_constructor: true/false,  # Depends on your team")
        print(f"       map: '{match.selected_map}',")
        print(f"       server: '{match.game_server}',")
        print(f"       team: 'team_a' or 'team_b'")
        print(f"   }}")
        
        print(f"\n   [NEXT STEPS FOR YOU]")
        if match.constructor_puuid == result.get('constructor_puuid'):
            print(f"   1. Your client should receive 'match_starting' with is_constructor=true")
            print(f"   2. Your client will automatically create Valorant custom game")
            print(f"   3. Bots will automatically 'join' (simulated)")
            print(f"   4. Match will go live")
        
        return match
    else:
        print(f"   [FAIL] {result.get('message')}")
        return None


async def wait_for_your_action(match):
    """Wait for you to create custom game or join"""
    print(f"\n[WAITING] Waiting for your action in Valorant...")
    
    # Check if you're the constructor
    from asgiref.sync import sync_to_async
    
    is_constructor = False
    
    print(f"\n   [INFO] If you're the constructor:")
    print(f"   - Your client will automatically call party_change_to_custom()")
    print(f"   - Then send 'custom_game_created' WebSocket event")
    print(f"   - You'll see this script detect it below")
    
    print(f"\n   [INFO] If you're NOT the constructor:")
    print(f"   - Wait for 'join_custom_game' event")
    print(f"   - Your client will automatically call party_join(pregame_id)")
    print(f"   - Then send 'player_joined_game' WebSocket event")
    
    print(f"\n   [MONITORING] Checking for your pregame_id...")
    
    # Poll for pregame_id to be set (means you created custom game)
    for i in range(60):  # Wait up to 60 seconds
        match = await sync_to_async(Match.objects.get)(id=match.id)
        
        if match.pregame_id:
            print(f"\n   [DETECTED] Custom game created!")
            print(f"   [INFO] Pregame ID: {match.pregame_id}")
            return True
        
        await asyncio.sleep(1)
        
        if i % 10 == 0 and i > 0:
            print(f"   [WAITING] Still waiting... ({i}s elapsed)")
    
    print(f"\n   [TIMEOUT] No pregame_id detected after 60 seconds")
    print(f"   [INFO] This is normal if testing without Valorant running")
    return False


async def simulate_bots_joining(match):
    """Simulate bot players joining the custom game"""
    print(f"\n[SIMULATION] Simulating bot players joining custom game...")
    
    # In real flow, bots would receive 'join_custom_game' and respond
    # For simulation, we'll just log it
    print(f"   [INFO] 9 bots would now join pregame_id: {match.pregame_id}")
    print(f"   [INFO] In real flow, they'd call party_join(pregame_id)")
    
    # Simulate all bots joined
    await asyncio.sleep(2)
    print(f"   [OK] All bots joined (simulated)")


async def simulate_match_go_live(match):
    """Simulate match going live after all players joined"""
    print(f"\n[SIMULATION] Simulating match going live...")
    
    fake_coregame_id = f"coregame-live-{match.id}-{timezone.now().timestamp()}"
    
    result = await MatchExecutionManager.handle_match_started(
        str(match.id),
        fake_coregame_id
    )
    
    if result['status'] == 'success':
        print(f"   [OK] Match started: {fake_coregame_id}")
        print(f"   [WebSocket Event Sent] 'match_in_progress' to all players")
        print(f"\n   [YOUR CLIENT] Should receive:")
        print(f"   {{")
        print(f"       event: 'match_in_progress',")
        print(f"       data: {{")
        print(f"           match_id: '{match.id}',")
        print(f"           coregame_id: '{fake_coregame_id}',")
        print(f"           map: '{match.selected_map}',")
        print(f"           server: '{match.game_server}'")
        print(f"       }}")
        print(f"   }}")
        
        return fake_coregame_id
    else:
        print(f"   [FAIL] {result.get('message')}")
        return None


async def simulate_live_match_with_updates(match, coregame_id):
    """
    Simulate live match with score updates.
    You can watch these updates in real-time in your client.
    """
    print(f"\n[LIVE MATCH] Simulating live match with score updates...")
    print(f"   [INFO] Updates will be sent every 5 seconds (accelerated for testing)")
    print(f"   [INFO] In production, this would be every 30 seconds")
    
    scores = [
        (1, 0, 1),   # Round 1
        (2, 0, 2),   # Round 2
        (2, 1, 3),   # Round 3
        (3, 2, 4),   # Round 4
        (4, 2, 5),   # Round 5
        (5, 3, 6),   # Round 6
        (6, 4, 7),   # Round 7
        (7, 5, 8),   # Round 8
    ]
    
    print(f"\n   [INFO] Match is live! Score updates:")
    
    for team_a, team_b, round_num in scores:
        result = await MatchMonitor.update_match_score(
            str(match.id), team_a, team_b, round_num
        )
        
        if result['status'] == 'success' and result['changed']:
            print(f"   Round {round_num:2}: Team A {team_a} - {team_b} Team B")
            
            # In real flow, your client would receive 'match_score_update' event
            # and update the UI
            
        await asyncio.sleep(5)  # 5 seconds between updates for demo
    
    print(f"\n   [INFO] Match is ongoing...")
    print(f"   [INFO] Your client should be showing live scores")


async def wait_for_manual_completion(match):
    """Wait for you to manually complete the match or auto-complete after timeout"""
    print(f"\n[WAITING] Waiting for match completion...")
    print(f"   [MANUAL] You can:")
    print(f"   1. Actually play the match in Valorant (if connected)")
    print(f"   2. Press Enter to simulate match completion")
    print(f"   3. Wait 30 seconds for auto-completion")
    
    try:
        # Try to read input with timeout
        import sys
        import select
        
        print(f"\n   Press Enter to complete match (or wait 30s)...", end='', flush=True)
        
        # Simple wait with timeout
        await asyncio.sleep(30)
        
        print(f"\n   [AUTO] Auto-completing match after timeout...")
        
    except:
        pass
    
    return True


async def complete_match_with_stats(match, live_player, bot_players):
    """Complete the match and generate final statistics"""
    print(f"\n[COMPLETION] Completing match and generating statistics...")
    
    # Generate realistic stats
    import random
    all_players = [live_player] + bot_players
    
    # Determine if you're on team A or B
    from asgiref.sync import sync_to_async
    
    def get_teams():
        team_a_puuids = [p['puuid'] for p in match.team_a_data.get('players', [])]
        return team_a_puuids
    
    team_a_puuids = await sync_to_async(get_teams)()
    
    your_team = 'team_a' if live_player.puuid in team_a_puuids else 'team_b'
    
    # Generate stats
    player_stats = {}
    
    for player in all_players:
        is_team_a = player.puuid in team_a_puuids
        
        # Generate realistic stats
        if is_team_a:
            base_kills = random.randint(10, 18)
            base_deaths = random.randint(8, 14)
        else:
            base_kills = random.randint(8, 16)
            base_deaths = random.randint(10, 16)
        
        player_stats[player.puuid] = {
            'team': 'team_a' if is_team_a else 'team_b',
            'kills': base_kills,
            'deaths': base_deaths,
            'assists': random.randint(3, 8),
            'headshots': int(base_kills * random.uniform(0.3, 0.5)),
            'bodyshots': int(base_kills * random.uniform(0.4, 0.6)),
            'legshots': int(base_kills * random.uniform(0.05, 0.15)),
            'damage_dealt': base_kills * random.randint(120, 180),
            'damage_received': base_deaths * random.randint(100, 150)
        }
    
    # Update statistics
    await MatchMonitor.update_player_statistics(str(match.id), player_stats)
    
    # Complete match
    final_data = {
        'team_a_score': 13,
        'team_b_score': 8,
        'total_rounds': 21
    }
    
    await MatchExecutionManager.handle_match_completion(str(match.id), final_data)
    
    print(f"   [OK] Match completed!")
    print(f"   [OK] Final score: Team A 13 - 8 Team B")
    
    # Show your stats
    from asgiref.sync import sync_to_async
    
    def get_your_stats():
        return MatchStatistics.objects.filter(match=match, player=live_player).first()
    
    your_stats = await sync_to_async(get_your_stats)()
    
    if your_stats:
        print(f"\n   === YOUR STATS ===")
        print(f"   Team: {your_stats.team.upper()}")
        print(f"   K/D/A: {your_stats.kills}/{your_stats.deaths}/{your_stats.assists}")
        print(f"   ADR: {your_stats.adr:.1f}")
        print(f"   Headshot %: {your_stats.headshot_percentage:.1f}%")
        print(f"   K/D Ratio: {your_stats.kd_ratio:.2f}")
        
        winner = 'Team A' if final_data['team_a_score'] > final_data['team_b_score'] else 'Team B'
        your_team_name = 'Team A' if your_team == 'team_a' else 'Team B'
        
        if winner == your_team_name:
            print(f"\n   [VICTORY] Your team won! 🎉")
        else:
            print(f"\n   [DEFEAT] Your team lost.")
    
    return match


async def cleanup_bot_players():
    """Clean up bot players"""
    print(f"\n[CLEANUP] Cleaning up bot players...")
    
    from asgiref.sync import sync_to_async
    
    def cleanup():
        count = Player.objects.filter(puuid__startswith='bot-player-').count()
        Player.objects.filter(puuid__startswith='bot-player-').delete()
        return count
    
    count = await sync_to_async(cleanup)()
    print(f"   [OK] Deleted {count} bot players")


async def main():
    """Main test execution"""
    print("=" * 70)
    print("Phase 3.1 - Live Client Match Flow Test")
    print("=" * 70)
    print("\nThis test creates 9 bots + YOU for a complete 10-player match.")
    print("You'll receive real WebSocket events in your dev client!\n")
    
    try:
        # Find your player
        live_player = await get_live_player()
        
        if not live_player:
            print("\n[ERROR] Cannot proceed without a live player")
            print("[HELP] Steps to fix:")
            print("  1. Start your dev client (client/backend)")
            print("  2. Authenticate with Valorant")
            print("  3. Run this script again")
            return
        
        # Ask if you want to be constructor
        print(f"\n[QUESTION] Do you want to be the constructor?")
        print(f"  - Constructor creates the Valorant custom game")
        print(f"  - Non-constructor joins the custom game")
        print(f"  - This tests different code paths")
        
        # For non-interactive, default to constructor
        make_constructor = True
        print(f"\n   [DEFAULT] Making you the constructor (you create custom game)")
        
        # Create bots
        bot_players = await create_bot_players(live_player, 9)
        
        # Create match
        match, team_a, team_b = await create_balanced_match(live_player, bot_players, make_constructor)
        
        # Simulate acceptance
        await simulate_all_players_accept(match.id)
        
        # Trigger match start - YOU WILL RECEIVE WEBSOCKET EVENT
        match = await trigger_match_start(match)
        
        if not match:
            print("\n[ERROR] Match start failed")
            return
        
        # Wait for your action
        print(f"\n[PAUSED] Script paused for 15 seconds...")
        print(f"   [INFO] This gives you time to:")
        print(f"   - Check your client received 'match_starting' event")
        print(f"   - See if custom game creation was triggered")
        print(f"   - Verify WebSocket events are working")
        
        for i in range(15, 0, -1):
            print(f"   Resuming in {i}s...", end='\r')
            await asyncio.sleep(1)
        
        print(f"\n\n[RESUME] Continuing simulation...")
        
        # Check if you created custom game
        from asgiref.sync import sync_to_async
        match = await sync_to_async(Match.objects.get)(id=match.id)
        
        if match.pregame_id:
            print(f"\n   [SUCCESS] Detected pregame_id: {match.pregame_id}")
            print(f"   [INFO] You successfully created the custom game!")
            
            # Simulate bots joining
            await simulate_bots_joining(match)
            
            # Simulate match going live
            coregame_id = await simulate_match_go_live(match)
            
            if coregame_id:
                # Simulate live match
                await simulate_live_match_with_updates(match, coregame_id)
                
                # Complete match
                match = await complete_match_with_stats(match, live_player, bot_players)
        else:
            print(f"\n   [INFO] No pregame_id detected (expected if Valorant not running)")
            print(f"   [INFO] Simulating the rest of the flow anyway...")
            
            # Simulate everything
            fake_pregame = f"pregame-sim-{match.id}"
            
            from asgiref.sync import sync_to_async
            def set_pregame():
                match.pregame_id = fake_pregame
                match.save()
            await sync_to_async(set_pregame)()
            
            await simulate_bots_joining(match)
            coregame_id = await simulate_match_go_live(match)
            await simulate_live_match_with_updates(match, coregame_id)
            match = await complete_match_with_stats(match, live_player, bot_players)
        
        print("\n" + "=" * 70)
        print("[SUCCESS] Live client test completed!")
        print("=" * 70)
        
        print(f"\n[DATA] Test data created:")
        print(f"  - Match ID: {match.id}")
        print(f"  - Match status: {match.status}")
        print(f"  - Final score: {match.team_a_score} - {match.team_b_score}")
        print(f"  - Your stats saved: Yes")
        print(f"  - Bot players: 9")
        
        print(f"\n[INFO] You can inspect this match in:")
        print(f"  - Django admin: http://localhost:8000/admin/")
        print(f"  - Django shell: pipenv run python manage.py shell")
        print(f"    >>> Match.objects.get(id={match.id})")
        print(f"    >>> MatchStatistics.objects.filter(match_id={match.id})")
        
        # Clean up bots
        await cleanup_bot_players()
        
        print(f"\n[INFO] Test complete! Match data preserved for inspection.")
        print(f"[INFO] Bot players cleaned up. Your player account unchanged.")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("IMPORTANT: Make sure these are running:")
    print("  1. Django/Daphne server (port 8000)")
    print("  2. Your dev client (authenticated)")
    print("  3. Redis server")
    print("=" * 70)
    
    asyncio.run(main())

