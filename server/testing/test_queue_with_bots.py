"""
Queue Test with Bot Players
Creates 9 bot players with similar ELO to you and puts them in queue.
Then YOU can join queue through your Electron client and get matched!

This tests the complete matchmaking flow:
1. 9 bots in queue (waiting)
2. You join queue via client
3. Matchmaker finds match (you + 9 bots)
4. All 10 receive match confirmation
5. Accept match → Match starts
"""
import os
import sys
import asyncio
import django

# Add server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
from matchmaking.lobby_manager import LobbyManager
from matchmaking.queue_manager import QueueManager
from matchmaking.match_confirmation import MatchConfirmationManager
from matchmaking.trueskill_manager import mmr_to_trueskill_mu
from testing.bot_auto_acceptor import start_bot_acceptor
from asgiref.sync import sync_to_async
import random


async def create_bot_with_lobby(bot_num: int, base_elo: int, base_mmr: int, region: str):
    """
    Create a bot player, create lobby, and join queue.
    This simulates a solo player in queue.
    """
    # Create bot player
    def create_bot():
        # Calculate bot's specific ELO and MMR
        bot_elo = base_elo + random.randint(-50, 50)
        bot_mmr = base_mmr + random.randint(-50, 50)
        bot_mu = mmr_to_trueskill_mu(bot_mmr)
        
        bot, created = Player.objects.get_or_create(
            puuid=f"queuebot-{bot_num}",
            defaults={
                'username': f"QueueBot{bot_num}",
                'alias': f"QueueBot{bot_num}",
                'region': region,
                'elo': bot_elo,
                'mmr': bot_mmr,
                'trueskill_mu': bot_mu,
                'trueskill_sigma': 9.0,  # New player uncertainty
                'rank': 'S',
                'team': 'none'
            }
        )
        
        # Update if existed
        if not created:
            bot.elo = bot_elo
            bot.mmr = bot_mmr
            bot.trueskill_mu = bot_mu
            bot.trueskill_sigma = 9.0
            bot.save()
        
        return bot
    
    bot = await sync_to_async(create_bot)()
    
    # Create lobby for bot (solo lobby)
    lobby_result = await LobbyManager.create_lobby(bot.puuid)
    
    if lobby_result['status'] != 'success':
        print(f"   [FAIL] Failed to create lobby for {bot.alias}")
        return None
    
    lobby_id = lobby_result['lobby']['id']
    
    # Set map preferences (required for queue)
    all_maps = ['Ascent', 'Bind', 'Breeze', 'Haven', 'Icebox', 'Lotus', 'Pearl', 'Split', 'Fracture']
    
    prefs_result = await LobbyManager.update_lobby_preferences(
        lobby_id, all_maps, [region.upper()], bot.puuid
    )
    
    if prefs_result['status'] != 'success':
        print(f"   [FAIL] Failed to set preferences for {bot.alias}")
        return None
    
    # Join queue
    queue_result = await QueueManager.join_queue(lobby_id, bot.puuid, 'pug')
    
    if queue_result['status'] == 'success':
        return {
            'player': bot,
            'lobby_id': lobby_id,
            'queue_position': queue_result.get('queue_position', 0)
        }
    else:
        print(f"   [FAIL] Failed to join queue for {bot.alias}: {queue_result.get('message')}")
        return None


async def get_your_player_info():
    """Get your player info from database"""
    print("\n[1/3] Finding your player account...")
    
    def find_player():
        # Look for your specific player first (evisc#erate)
        you = Player.objects.filter(username__icontains='evisc').first()
        
        if you:
            return you
            
        # If not found, find any non-bot, non-sim, non-test players
        players = Player.objects.exclude(puuid__startswith='sim-player-') \
                                .exclude(puuid__startswith='bot-') \
                                .exclude(puuid__startswith='queuebot-') \
                                .exclude(puuid__startswith='test-player-') \
                                .exclude(puuid__startswith='test-celery-')
        
        # Try to find most recent
        return players.order_by('-id').first() if players.exists() else None
    
    you = await sync_to_async(find_player)()
    
    if not you:
        print("   [FAIL] No player found!")
        print("   [HELP] Please authenticate with your dev client first")
        print("   [HELP] Make sure you're logged in as 'evisc#erate' or similar")
        return None
    
    print(f"   [OK] Found you: {you.alias}")
    print(f"   [INFO] PUUID: {you.puuid}")
    print(f"   [INFO] Display ELO: {you.elo}")
    print(f"   [INFO] Hidden MMR: {you.mmr:.0f}")
    print(f"   [INFO] Gap: {abs(you.mmr - you.elo):.0f} ELO")
    print(f"   [INFO] Region: {you.region}")
    
    return you


async def create_bots_in_queue(your_elo: int, your_mmr: float, your_region: str):
    """Create 9 bot players and put them all in queue"""
    print(f"\n[2/3] Creating 9 bots and queueing them...")
    print(f"   [INFO] Your Display ELO: {your_elo}")
    print(f"   [INFO] Your Hidden MMR: {your_mmr:.0f}")
    print(f"   [INFO] Bot ELO range: {your_elo - 100} to {your_elo + 100}")
    print(f"   [INFO] Bot MMR range: {your_mmr - 100:.0f} to {your_mmr + 100:.0f}")
    
    bots_in_queue = []
    
    for i in range(9):
        bot_data = await create_bot_with_lobby(i, your_elo, int(your_mmr), your_region)
        
        if bot_data:
            bots_in_queue.append(bot_data)
            print(f"   [OK] {bot_data['player'].alias:12} in queue (ELO: {bot_data['player'].elo}, MMR: {bot_data['player'].mmr:.0f}, Pos: {bot_data['queue_position']})")
        else:
            print(f"   [FAIL] Failed to queue bot {i}")
    
    if len(bots_in_queue) == 9:
        print(f"\n   [SUCCESS] All 9 bots are now in queue!")
    else:
        print(f"\n   [WARN] Only {len(bots_in_queue)}/9 bots in queue")
    
    return bots_in_queue


async def check_queue_status():
    """Check current queue status"""
    print(f"\n[3/3] Checking queue status...")
    
    queue_status = await QueueManager.get_queue_stats('pug')
    
    players_count = queue_status.get('total_players', 0)
    total_lobbies = queue_status.get('total_lobbies', 0)
    print(f"   [OK] Queue has {players_count} players in {total_lobbies} lobbies")
    print(f"   [INFO] Estimated wait: {queue_status.get('estimated_wait', 0)} seconds")
    
    return queue_status


async def wait_for_you_to_join():
    """Wait and monitor for you to join the queue"""
    print(f"\n" + "=" * 60)
    print("READY FOR YOU TO JOIN!")
    print("=" * 60)
    
    print(f"\n[INSTRUCTIONS] In your Electron client:")
    print(f"   1. Select at least 5 maps")
    print(f"   2. Click 'FIND MATCH' button")
    print(f"   3. You'll be queued with the 9 bots")
    print(f"   4. Matchmaker will find a match within 30 seconds")
    print(f"   5. You'll receive 'match_found' event")
    print(f"   6. Accept the match")
    print(f"   7. Then you'll receive 'match_starting' event")
    
    print(f"\n[MONITORING] Watching queue for your entry...")
    
    # Monitor queue for changes
    initial_count = 9
    
    for i in range(120):  # Wait up to 2 minutes
        queue_status = await QueueManager.get_queue_stats('pug')
        current_count = queue_status.get('total_players', 0)
        
        if current_count > initial_count:
            print(f"\n   [DETECTED] Queue size increased: {initial_count} -> {current_count}")
            print(f"   [SUCCESS] You joined the queue!")
            print(f"\n   [INFO] Matchmaker runs every 30 seconds...")
            print(f"   [INFO] Wait for match_found event in your client...")
            return True
        
        if i % 10 == 0 and i > 0:
            print(f"   [WAITING] Still monitoring... ({i}s elapsed, queue has {current_count} players)")
        
        await asyncio.sleep(1)
    
    print(f"\n   [TIMEOUT] You didn't join queue within 2 minutes")
    print(f"   [INFO] That's okay - bots will stay in queue for testing")
    return False


async def monitor_match_confirmation():
    """Monitor for match confirmation creation"""
    print(f"\n[MONITORING] Watching for match creation...")
    print(f"   [INFO] When matchmaker finds a match, all 10 players get 'match_found' event")
    print(f"   [INFO] You have 30 seconds to accept in your client")
    
    # Check for active match confirmations
    for i in range(60):  # Check for 1 minute
        confirmations = await MatchConfirmationManager.get_all_active_confirmations()
        
        if confirmations:
            print(f"\n   [DETECTED] Match found! {len(confirmations)} active confirmation(s)")
            
            for conf_id, conf_data in confirmations:
                print(f"   [INFO] Match ID: {conf_id}")
                print(f"   [INFO] Check your client for match acceptance popup!")
                
                # Monitor acceptance
                await monitor_match_acceptance(conf_id)
            
            return True
        
        if i % 10 == 0 and i > 0:
            print(f"   [WAITING] No match yet... ({i}s elapsed)")
        
        await asyncio.sleep(1)
    
    print(f"\n   [INFO] No match found within 1 minute")
    print(f"   [INFO] Matchmaker runs every 30 seconds, so it might take time")
    return False


async def monitor_match_acceptance(match_id: str):
    """Monitor how many players accepted the match"""
    print(f"\n   [MONITORING] Watching match acceptance for {match_id[:8]}...")
    
    for i in range(30):  # 30 seconds to accept
        status = await MatchConfirmationManager.get_confirmation_status(match_id)
        
        if status['status'] == 'success':
            accepted = status.get('accepted_count', 0)
            required = status.get('required_count', 10)
            
            print(f"   [STATUS] {accepted}/{required} players accepted", end='\r')
            
            if accepted == required:
                print(f"\n   [SUCCESS] All players accepted! Match starting...")
                return True
        
        await asyncio.sleep(1)
    
    print(f"\n   [TIMEOUT] Not all players accepted within 30 seconds")
    return False


async def cleanup_bots():
    """Clean up bot players and lobbies"""
    print(f"\n[CLEANUP] Cleaning up bot players...")
    
    from asgiref.sync import sync_to_async
    
    def cleanup():
        # Delete bot lobbies
        Lobby.objects.filter(lobby_leader__puuid__startswith='queuebot-').delete()
        
        # Delete bot players
        count = Player.objects.filter(puuid__startswith='queuebot-').count()
        Player.objects.filter(puuid__startswith='queuebot-').delete()
        
        return count
    
    count = await sync_to_async(cleanup)()
    print(f"   [OK] Cleaned up {count} bot players")


async def main():
    print("=" * 70)
    print("Queue Test - 9 Bots + YOU (Live Client)")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Create 9 bot players with similar MMR to you")
    print("  2. Put all 9 bots in queue")
    print("  3. Start bot auto-acceptor (bots will auto-accept matches)")
    print("  4. Wait for YOU to join queue via your Electron client")
    print("  5. Matchmaker will find a match (10 players total)")
    print("  6. Bots auto-accept, YOU accept in client -> Match ready!")
    print()
    
    acceptor_task = None
    
    try:
        # Get your player
        you = await get_your_player_info()
        
        if not you:
            return
        
        # Create bots and queue them
        bots = await create_bots_in_queue(you.elo, you.mmr, you.region)
        
        if len(bots) < 9:
            print(f"\n[ERROR] Failed to create all bots")
            return
        
        # Start bot auto-acceptor
        print(f"\n[AUTO-ACCEPT] Starting bot auto-acceptor...")
        bot_puuids = [bot['player'].puuid for bot in bots]
        acceptor, acceptor_task = await start_bot_acceptor(bot_puuids)
        print(f"[AUTO-ACCEPT] Monitoring {len(bot_puuids)} bots for match acceptance")
        
        # Check queue
        await check_queue_status()
        
        # Wait for you to join
        you_joined = await wait_for_you_to_join()
        
        if you_joined:
            # Monitor for match
            match_found = await monitor_match_confirmation()
            
            if match_found:
                print(f"\n[SUCCESS] Match flow completed!")
            else:
                print(f"\n[INFO] Match may still be found - check your client!")
        else:
            print(f"\n[INFO] Bots are still in queue, waiting for you")
            print(f"\n[MANUAL TEST] You can now:")
            print(f"   1. Join queue in your client")
            print(f"   2. Wait for match (runs every 30 seconds)")
            print(f"   3. Bots will auto-accept, you accept in client")
        
        print(f"\n" + "=" * 70)
        print("Test Complete!")
        print("=" * 70)
        
        print(f"\n[INFO] Bot auto-acceptor still running in background")
        print(f"[INFO] Bots will auto-accept any new matches")
        print(f"[INFO] Press Ctrl+C to stop and clean up")
        
        # Keep running to continue auto-accepting
        try:
            await acceptor_task
        except KeyboardInterrupt:
            print(f"\n[INFO] Stopping...")
        
    except KeyboardInterrupt:
        print(f"\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop acceptor if running
        if acceptor_task and not acceptor_task.done():
            print(f"\n[CLEANUP] Stopping bot auto-acceptor...")
            from testing.bot_auto_acceptor import get_acceptor
            get_acceptor().stop()
            try:
                await asyncio.wait_for(acceptor_task, timeout=2.0)
            except:
                pass


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PREREQUISITES:")
    print("  1. [OK] Daphne server running (you have this)")
    print("  2. [OK] Celery worker running")
    print("  3. [OK] Celery beat running")
    print("  4. [OK] Your Electron client running")
    print("  5. [OK] Authenticated in your client")
    print("=" * 70)
    print()
    
    asyncio.run(main())

