"""
Quick Match Test - Create a match with you + 9 bots

This is the simplest way to test the match flow with your dev client.
Just run this script and your client will receive match events!
"""
import os
import asyncio
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Match, Player, Lobby
from matchmaking.match_execution import MatchExecutionManager
from asgiref.sync import sync_to_async
import random


async def main():
    print("\n" + "=" * 60)
    print("Quick Match Test - YOU + 9 Bots")
    print("=" * 60)
    
    # Find your player
    print("\n[1/4] Finding your player...")
    
    def find_player():
        players = Player.objects.exclude(puuid__startswith='sim-player-').exclude(puuid__startswith='bot-player-').exclude(puuid__startswith='test-player-')
        
        # Try to find player with active lobby
        for player in players:
            lobby = Lobby.objects.filter(players=player, is_active=True).first()
            if lobby:
                return player
        
        # Return most recent
        return players.order_by('-id').first() if players.exists() else None
    
    you = await sync_to_async(find_player)()
    
    if not you:
        print("   [FAIL] No player found. Please authenticate first.")
        return
    
    print(f"   [OK] Found you: {you.alias} (ELO: {you.elo})")
    
    # Create 9 bots
    print("\n[2/4] Creating 9 bot players...")
    
    def create_bots():
        bots = []
        base_elo = you.elo if you.elo > 0 else 1500
        
        for i in range(9):
            bot_elo = base_elo + random.randint(-100, 100)
            bot, _ = Player.objects.get_or_create(
                puuid=f"bot-{i}",
                defaults={
                    'username': f"Bot{i}",
                    'alias': f"Bot{i}",
                    'region': you.region,
                    'elo': bot_elo,
                    'rank': 'S',
                    'team': 'none'
                }
            )
            bots.append(bot)
        return bots
    
    bots = await sync_to_async(create_bots)()
    print(f"   [OK] 9 bots ready")
    
    # Create match - you as constructor
    print("\n[3/4] Creating match (you as constructor)...")
    
    def create_match():
        team_a = [you] + bots[:4]
        team_b = bots[4:9]
        
        match = Match.objects.create(
            status='confirmed',
            selected_map='Haven',
            game_server='Virginia',
            team_a_data={
                'captain': {'puuid': you.puuid, 'alias': you.alias, 'elo': you.elo},
                'players': [{'puuid': p.puuid, 'alias': p.alias, 'elo': p.elo} for p in team_a]
            },
            team_b_data={
                'captain': {'puuid': bots[4].puuid, 'alias': bots[4].alias, 'elo': bots[4].elo},
                'players': [{'puuid': p.puuid, 'alias': p.alias, 'elo': p.elo} for p in team_b]
            }
        )
        return match
    
    match = await sync_to_async(create_match)()
    
    print(f"   [OK] Match {match.id} created")
    print(f"   [INFO] Team A: {you.alias} + 4 bots")
    print(f"   [INFO] Team B: 5 bots")
    
    # Trigger match start
    print("\n[4/4] Starting match...")
    print(f"   [IMPORTANT] Check your dev client NOW!")
    
    result = await MatchExecutionManager.initiate_match_start(str(match.id))
    
    if result['status'] == 'success':
        print(f"\n   [SUCCESS] Match started!")
        print(f"   [WebSocket] Sent 'match_starting' event to your client")
        print(f"\n   Your client should:")
        print(f"   1. Receive 'match_starting' event")
        print(f"   2. See is_constructor = True")
        print(f"   3. Automatically call party_change_to_custom()")
        print(f"   4. Send back 'custom_game_created' event")
        
        print(f"\n   [INFO] Match ID: {match.id}")
        print(f"   [INFO] Constructor: {you.alias} (you!)")
        print(f"   [INFO] Map: Haven, Server: Virginia")
        
        print(f"\n" + "=" * 60)
        print("Test complete! Check your dev client for events.")
        print("=" * 60)
        
        print(f"\nTo clean up later:")
        print(f"  pipenv run python manage.py shell")
        print(f"  >>> Match.objects.filter(id={match.id}).delete()")
        print(f"  >>> Player.objects.filter(puuid__startswith='bot-').delete()")
    else:
        print(f"   [FAIL] {result.get('message')}")


if __name__ == '__main__':
    asyncio.run(main())

