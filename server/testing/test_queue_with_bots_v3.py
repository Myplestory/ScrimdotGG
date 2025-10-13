"""
Queue Test with Bot Players V3 - Full Accept Test
Creates 9 bot players, ALL will auto-accept.
Tests match page redirect and veto functionality.

This tests:
1. 9 bots in queue (ALL 9 will accept)
2. You join queue via client (10th player)
3. Matchmaker finds match
4. ALL 9 bots auto-accept
5. YOU accept
6. Match confirmed → redirect to match page
7. Veto phase starts
8. Test veto functionality
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


async def start_full_bot_acceptor(bot_puuids: list):
    """
    Start bot auto-acceptor with WebSocket connections.
    ALL bots will accept (unlike v2 where 1 doesn't accept).
    
    Args:
        bot_puuids: List of all bot PUUIDs
        
    Returns:
        BotAutoAcceptorWS instance
    """
    # Create acceptor
    acceptor = BotAutoAcceptorWS()
    
    # Add ALL bots with auto-accept enabled
    for bot_puuid in bot_puuids:
        acceptor.add_bot(bot_puuid, auto_accept=True)
    
    # Connect all bots to WebSocket
    logger.info(f"[AUTO-ACCEPT] Connecting {len(bot_puuids)} bots to WebSocket...")
    connected_count = await acceptor.connect_bots(bot_puuids)
    
    if connected_count < len(bot_puuids):
        logger.warning(f"[AUTO-ACCEPT] Only {connected_count}/{len(bot_puuids)} bots connected!")
    
    logger.info(f"[FULL-ACCEPT] Will auto-accept for ALL {len(bot_puuids)} bots")
    
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
    print(f"   7. Watch as ALL 9 bots accept")
    print(f"   8. You'll be redirected to match page for veto!")
    
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


async def monitor_match_confirmation():
    """Monitor for match creation and confirmation"""
    print(f"\n[MONITORING] Watching for match confirmation...")
    print(f"   [EXPECTED] ALL 9 bots accept + YOU accept = 10/10")
    print(f"   [EXPECTED] Match confirms and redirects to match page")
    print(f"   [EXPECTED] Veto phase starts automatically")
    
    # Check for active match confirmations
    for i in range(120):  # Check for 2 minutes
        confirmations = await MatchConfirmationManager.get_all_active_confirmations()
        
        if confirmations:
            match_id = confirmations[0].get('match_id') or confirmations[0].get('id')
            print(f"\n   [DETECTED] Match created: {match_id[:8]}...")
            print(f"   [INFO] Waiting for all players to accept...")
            print(f"   [INFO] Watch your client - should show 10/10 accepted soon")
            
            # Wait for confirmation (or timeout)
            await asyncio.sleep(40)  # Wait for acceptance period
            
            # Check if match was confirmed (should transition to Match instance)
            remaining = await MatchConfirmationManager.get_all_active_confirmations()
            
            if not remaining:
                print(f"\n   [SUCCESS] ✅ Match confirmation complete!")
                print(f"   [INFO] Match should have transitioned to Match instance")
                print(f"   [INFO] Check your client - you should be on match page!")
                print(f"   [INFO] Veto phase should have started")
                
                # Check if Match instance was created
                from matchmaking.models_match import Match
                await asyncio.sleep(1)
                
                try:
                    # Try to find the Match instance (may not have exact match_id)
                    recent_matches = await sync_to_async(
                        lambda: list(Match.objects.filter(
                            state__in=['CONFIRMED', 'VETO']
                        ).order_by('-created_at')[:1])
                    )()
                    
                    if recent_matches:
                        match = recent_matches[0]
                        print(f"\n   [MATCH FOUND] Match instance created: {match.id}")
                        print(f"   [STATE] {match.state}")
                        print(f"   [VETO] Turn: {match.veto_turn}, Maps: {len(match.get_remaining_maps())}")
                        return True
                    else:
                        print(f"\n   [WARN] No Match instance found in database")
                        return False
                        
                except Exception as e:
                    print(f"\n   [ERROR] Error checking Match instance: {e}")
                    return False
            else:
                print(f"\n   [WARN] Match still in confirmation phase")
                return False
        
        if i % 10 == 0 and i > 0:
            print(f"   [WAITING] No match yet... ({i}s elapsed)")
        
        await asyncio.sleep(1)
    
    print(f"\n   [TIMEOUT] No match found within 2 minutes")
    return False


async def main():
    print("=" * 70)
    print("Queue Test V3 - Full Accept (ALL 9 Bots Accept)")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Create 9 bot players with similar MMR to you")
    print("  2. Put all 9 bots in queue")
    print("  3. Start bot auto-acceptor (ALL 9 will accept)")
    print("  4. Wait for YOU to join queue via your Electron client")
    print("  5. Matchmaker will find a match (10 players total)")
    print("  6. ALL 9 bots + YOU accept = 10/10")
    print("  7. Match confirms → redirect to match page")
    print("  8. Veto phase starts automatically")
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
        
        # Start FULL bot auto-acceptor (ALL 9 bots will accept)
        print(f"\n[AUTO-ACCEPT] Starting FULL bot auto-acceptor...")
        bot_puuids = [bot['player'].puuid for bot in bots]
        acceptor, acceptor_task = await start_full_bot_acceptor(bot_puuids)
        print(f"[AUTO-ACCEPT] Monitoring ALL 9 bots for acceptance")
        
        # Wait for you to join
        you_joined = await wait_for_you_to_join()
        
        if you_joined:
            # Monitor for match confirmation
            result = await monitor_match_confirmation()
            
            if result:
                print(f"\n[SUCCESS] ✅ Match confirmed and veto phase started!")
                print(f"\n[INFO] Check your client:")
                print(f"   - You should be on the match page (/match/...)")
                print(f"   - Veto UI should be visible")
                print(f"   - Countdown timer should be running")
                print(f"   - Your team should be highlighted")
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

