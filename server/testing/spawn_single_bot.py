"""
Spawn Single Bot - Manual Rematch Test
Creates a single bot that joins the queue and auto-accepts matches.
Use this to complete a 9-player queue after requeueing.
Run once, no inputs needed.
"""

import os
import sys
import asyncio
import django
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from testing.bot_websocket_client import BotWebSocketClient
from testing.bot_auto_acceptor_ws import BotAutoAcceptorWS
from matchmaking.match_confirmation import MatchConfirmationManager
from matchmaking.queue_manager import QueueManager
from matchmaking.lobby_manager import LobbyManager
from matchmaking.trueskill_manager import mmr_to_trueskill_mu
from scrimgg.models import Player, Lobby
from django.utils import timezone
from asgiref.sync import sync_to_async
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_bot_with_lobby(base_elo: int, base_mmr: int, region: str):
    """
    Create a bot player, create lobby, and join queue.
    Uses the EXACT same logic as test_queue_with_bots_v2.py
    """
    # Calculate bot's ELO and MMR
    bot_elo = base_elo + random.randint(-100, 100)
    bot_mmr = base_mmr + random.randint(-100, 100)
    bot_mu = mmr_to_trueskill_mu(bot_mmr)
    
    def create_bot():
        bot, created = Player.objects.get_or_create(
            puuid='podbot',
            defaults={
                'alias': 'PodBot',
                'elo': bot_elo,
                'mmr': bot_mmr,
                'region': region,
                'rank': 'Diamond 2',
                'trueskill_mu': bot_mu,
                'trueskill_sigma': 9.0
            }
        )
        
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


async def main():
    print("=" * 70)
    print("Spawn Single Bot - Auto Rematch Test")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Create 1 bot (podbot)")
    print("  2. Connect to WebSocket")
    print("  3. Add to queue")
    print("  4. Auto-accept matches with 20s delay")
    print()
    
    # Fixed config - no inputs
    bot_name = "podbot"
    base_elo = 6500
    base_mmr = 6200
    region = "na"
    
    acceptor = None
    
    try:
        # Create the bot
        print(f"[1/3] Creating {bot_name}...")
        bot_data = await create_bot_with_lobby(base_elo, base_mmr, region)
        
        if not bot_data:
            print(f"[ERROR] Failed to create bot!")
            return
        
        player = bot_data['player']
        lobby_id = bot_data['lobby_id']
        
        print(f"[SUCCESS] Created {player.alias}")
        print(f"  PUUID: {player.puuid}")
        print(f"  ELO: {player.elo}")
        print(f"  MMR: {player.mmr}")
        print(f"  Lobby ID: {lobby_id}")
        print(f"  Queue Position: {bot_data['queue_position']}")
        print(f"  ✅ Queued automatically")
        
        # Check queue stats
        queue_stats = await QueueManager.get_queue_stats('pug')
        print(f"\n[QUEUE STATUS]")
        print(f"  Total lobbies: {queue_stats.get('total_lobbies', 0)}")
        print(f"  Total players: {queue_stats.get('total_players', 0)}")
        
        # Connect to WebSocket using EXACT SAME METHOD as v2
        print(f"\n[2/3] Connecting to WebSocket (using BotAutoAcceptorWS)...")
        acceptor = BotAutoAcceptorWS()
        
        # Add bot with auto-accept enabled
        acceptor.add_bot(player.puuid, auto_accept=True)
        
        # Connect bot
        connected_count = await acceptor.connect_bots([player.puuid])
        
        if connected_count == 0:
            print(f"[ERROR] Failed to connect bot to WebSocket!")
            return
        
        print(f"[SUCCESS] Connected to WebSocket")
        
        print(f"\n[3/3] Bot is active and ready!")
        print(f"[INFO] Bot will auto-accept matches (random delay 1-15s)")
        print(f"\n" + "=" * 70)
        print("Bot is ready! Press Ctrl+C to stop")
        print("=" * 70)
        
        # Keep bot running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print(f"\n[INFO] Shutting down...")
        
    except KeyboardInterrupt:
        print(f"\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup using EXACT SAME METHOD as v2
        if acceptor:
            print(f"\n[CLEANUP] Closing bot WebSocket connections...")
            try:
                await acceptor.close()
                print(f"[CLEANUP] ✅ Connection closed")
            except Exception as e:
                print(f"[CLEANUP] Error: {e}")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PREREQUISITES:")
    print("  1. [OK] Daphne server running")
    print("  2. [OK] Celery worker running")
    print("  3. [OK] 9 lobbies in queue (from requeue test)")
    print("=" * 70)
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Script interrupted")
    finally:
        print("[INFO] Script exited")

