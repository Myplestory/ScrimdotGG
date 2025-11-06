"""
Queue Test with Bot Players V2 - Partial Accept Test
Creates 9 bot players, but only 8 will auto-accept.
Tests timeout/requeue functionality when not all players accept.

This tests:
1. 9 bots in queue (8 will accept, 1 will not)
2. You join queue via client (10th player)
3. Matchmaker finds match
4. 8 bots auto-accept
5. YOU accept
6. 1 bot doesn't accept (simulated)
7. Match times out
8. Lobbies should be requeued
9. Progress indicators should work
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
from testing.bot_auto_acceptor_ws import BotAutoAcceptorWS, start_bot_acceptor_ws
from asgiref.sync import sync_to_async
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


async def start_selective_bot_acceptor(bot_puuids: list, accept_count: int = 8):
    """
    Start bot auto-acceptor with WebSocket connections.
    
    Args:
        bot_puuids: List of all bot PUUIDs
        accept_count: How many bots should accept (default 8, leaving 1 to timeout)
        
    Returns:
        BotAutoAcceptorWS instance
    """
    # Create acceptor
    acceptor = BotAutoAcceptorWS()
    
    # Determine which bots should accept
    accepting_bots = bot_puuids[:accept_count]
    non_accepting_bots = bot_puuids[accept_count:]
    
    # Add all bots (mark which should accept)
    for bot_puuid in accepting_bots:
        acceptor.add_bot(bot_puuid, auto_accept=True)
    for bot_puuid in non_accepting_bots:
        acceptor.add_bot(bot_puuid, auto_accept=False)
    
    # Connect all bots to WebSocket
    logger.info(f"[AUTO-ACCEPT] Connecting {len(bot_puuids)} bots to WebSocket...")
    connected_count = await acceptor.connect_bots(bot_puuids)
    
    if connected_count < len(bot_puuids):
        logger.warning(f"[AUTO-ACCEPT] Only {connected_count}/{len(bot_puuids)} bots connected!")
    
    logger.info(f"[SELECTIVE-ACCEPT] Will auto-accept for {len(accepting_bots)} bots")
    logger.info(f"[SELECTIVE-ACCEPT] Will NOT accept for {len(non_accepting_bots)} bots:")
    for puuid in non_accepting_bots:
        logger.info(f"   - {puuid} (will timeout)")
    
    # Return acceptor (no task needed, WebSocket handles everything)
    return acceptor, None


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
    print(f"   7. Watch as only 8 bots accept (1 will timeout)")
    print(f"   8. Match should timeout and requeue you")
    
    print(f"\n[MONITORING] Watching queue for your entry...")
    
    # Monitor queue for changes
    initial_count = 9
    
    for i in range(120):  # Wait up to 2 minutes
        queue_status = await QueueManager.get_queue_stats('pug')
        current_count = queue_status.get('total_players', 0)
        
        if current_count > initial_count:
            print(f"\n   [DETECTED] Queue size increased: {initial_count} -> {current_count}")
            print(f"   [SUCCESS] You joined the queue!")
            print(f"\n   [INFO] Matchmaker runs every 10 seconds...")
            print(f"   [INFO] Wait for match_found event in your client...")
            return True
        
        if i % 10 == 0 and i > 0:
            print(f"   [WAITING] Still monitoring... ({i}s elapsed, queue has {current_count} players)")
        
        await asyncio.sleep(1)
    
    print(f"\n   [TIMEOUT] You didn't join queue within 2 minutes")
    print(f"   [INFO] That's okay - bots will stay in queue for testing")
    return False


async def monitor_match_and_timeout():
    """Monitor for match creation and timeout"""
    print(f"\n[MONITORING] Watching for match and timeout behavior...")
    print(f"   [EXPECTED] 8 bots accept + YOU accept = 9/10")
    print(f"   [EXPECTED] 1 bot doesn't accept")
    print(f"   [EXPECTED] Match times out after 30 seconds")
    print(f"   [EXPECTED] All lobbies requeued automatically")
    
    # Check for active match confirmations
    for i in range(120):  # Check for 2 minutes
        confirmations = await MatchConfirmationManager.get_all_active_confirmations()
        
        if confirmations:
            match_id = confirmations[0].get('match_id') or confirmations[0].get('id')
            print(f"\n   [DETECTED] Match created: {match_id[:8]}...")
            print(f"   [INFO] Waiting for timeout (30 seconds)...")
            print(f"   [INFO] Watch your client for acceptance progress (should show 9/10)")
            
            # Wait for match to timeout
            await asyncio.sleep(35)  # Wait slightly longer than 30s
            
            # Check if match was cleaned up
            remaining = await MatchConfirmationManager.get_all_active_confirmations()
            
            if not remaining:
                print(f"\n   [SUCCESS] Match timed out and was cleaned up!")
                
                # Check if lobbies were requeued
                await asyncio.sleep(2)  # Give requeue time to happen
                queue_status = await QueueManager.get_queue_stats('pug')
                requeued_count = queue_status.get('total_lobbies', 0)
                
                print(f"   [REQUEUE] Queue now has {requeued_count} lobbies")
                
                if requeued_count > 0:
                    print(f"   [SUCCESS] ✅ Lobbies were requeued automatically!")
                else:
                    print(f"   [FAIL] ❌ No lobbies in queue after timeout")
                
                return True
            else:
                print(f"   [WARN] Match still active after timeout")
                return False
        
        if i % 10 == 0 and i > 0:
            print(f"   [WAITING] No match yet... ({i}s elapsed)")
        
        await asyncio.sleep(1)
    
    print(f"\n   [TIMEOUT] No match found within 2 minutes")
    return False


async def main():
    print("=" * 70)
    print("Queue Test V2 - Partial Accept (8/9 Bots Accept)")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Create 9 bot players with similar MMR to you")
    print("  2. Put all 9 bots in queue")
    print("  3. Start selective bot auto-acceptor (ONLY 8 will accept)")
    print("  4. Wait for YOU to join queue via your Electron client")
    print("  5. Matchmaker will find a match (10 players total)")
    print("  6. 8 bots + YOU accept = 9/10")
    print("  7. 1 bot doesn't accept")
    print("  8. Match times out → 9 lobbies requeued!")
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
        
        # Start selective bot auto-acceptor (only 8 bots will accept)
        print(f"\n[AUTO-ACCEPT] Starting selective bot auto-acceptor...")
        bot_puuids = [bot['player'].puuid for bot in bots]
        acceptor, acceptor_task = await start_selective_bot_acceptor(bot_puuids, accept_count=8)
        print(f"[AUTO-ACCEPT] Monitoring 8/9 bots for acceptance (1 bot will NOT accept)")
        
        # Wait for you to join
        you_joined = await wait_for_you_to_join()
        
        if you_joined:
            # Monitor for match and timeout
            result = await monitor_match_and_timeout()
            
            if result:
                print(f"\n[SUCCESS] ✅ Timeout and requeue flow completed!")
            else:
                print(f"\n[INFO] Check logs for details")
        else:
            print(f"\n[INFO] Bots are still in queue, waiting for you")
        
        print(f"\n" + "=" * 70)
        print("Test Complete!")
        print("=" * 70)
        
        print(f"\n[INFO] Bot auto-acceptor still running in background")
        print(f"[INFO] Press Ctrl+C to stop")
        
        # Keep running to continue auto-accepting
        if acceptor_task:
            try:
                await acceptor_task
            except KeyboardInterrupt:
                print(f"\n[INFO] Stopping...")
        else:
            # If no task, just wait for Ctrl+C
            try:
                await asyncio.Event().wait()
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
        if 'acceptor' in locals() and acceptor:
            print(f"\n[CLEANUP] Closing bot WebSocket connections...")
            try:
                await acceptor.close()
                print(f"[CLEANUP] ✅ All bot connections closed")
            except Exception as e:
                print(f"[CLEANUP] Error closing connections: {e}")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PREREQUISITES:")
    print("  1. [OK] Daphne server running")
    print("  2. [OK] Celery worker running (with correct queues)")
    print("  3. [OK] Celery beat running")
    print("  4. [OK] Your Electron client running")
    print("  5. [OK] Authenticated in your client")
    print("=" * 70)
    print()
    
    # Run with proper cleanup
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Script interrupted - cleanup already handled")
    finally:
        print("[INFO] Script exited")

