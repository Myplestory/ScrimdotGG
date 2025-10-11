#!/usr/bin/env python3
"""
Test Celery Tasks for Scrim.GG Phase 2
Tests the Celery background tasks for matchmaking
"""

import os
import sys
import django
import asyncio
import time

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from asgiref.sync import sync_to_async
from matchmaking.tasks import (
    periodic_matchmaking,
    cleanup_expired_matches,
    cleanup_expired_queues,
    health_check,
    manual_matchmaking
)
from matchmaking.queue_manager import QueueManager
from matchmaking.lobby_manager import LobbyManager
from scrimgg.models import Player, Lobby

async def create_test_data():
    """Create test data for Celery testing"""
    print("Creating test data for Celery tasks...")
    
    # Create test players and lobbies
    players = []
    lobbies = []
    
    for i in range(6):  # Create 6 players (3 lobbies)
        unique_id = f"test-celery-player-{int(time.time())}-{i}"
        
        player = await sync_to_async(Player.objects.create)(
            puuid=unique_id,
            alias=f"CeleryTestPlayer{i}",
            username=f"CeleryTestPlayer{i}",
            elo=1600 + (i * 25),  # ELO range: 1600-1725
            region="NA",
            team="Test Team"
        )
        players.append(player)
        
        # Create lobby for each player
        result = await LobbyManager.create_lobby(player.puuid)
        if result['status'] == 'success':
            lobby_id = result['lobby']['id']
            
            # Set map preferences
            map_prefs = ['bind', 'haven', 'split', 'ascent', 'icebox']
            server_prefs = ['NA']
            
            prefs_result = await LobbyManager.update_lobby_preferences(
                lobby_id, map_prefs, server_prefs, player.puuid
            )
            
            if prefs_result['status'] == 'success':
                # Join queue
                queue_result = await QueueManager.join_queue(lobby_id, player.puuid)
                if queue_result['status'] == 'success':
                    lobbies.append(lobby_id)
                    print(f"  [OK] Created and queued lobby for {player.alias}")
                else:
                    print(f"  [FAIL] Failed to queue lobby: {queue_result.get('message')}")
            else:
                print(f"  [FAIL] Failed to set preferences: {prefs_result.get('message')}")
        else:
            print(f"  [FAIL] Failed to create lobby: {result.get('message')}")
    
    return players, lobbies

async def test_health_check():
    """Test the health check task"""
    print("\n" + "="*60)
    print("TEST 1: Health Check Task")
    print("="*60)
    
    try:
        # Run health check task
        result = health_check.delay()
        
        # Wait for result (with timeout)
        health_data = result.get(timeout=10)
        
        if health_data.get('status') == 'healthy':
            print("  [OK] Health check passed")
            print(f"  [OK] Redis connected: {health_data.get('redis_connected', False)}")
            print(f"  [OK] Active confirmations: {health_data.get('active_confirmations', 0)}")
            print(f"  [OK] Queue stats: {health_data.get('queue_stats', {})}")
        else:
            print(f"  [FAIL] Health check failed: {health_data}")
            
    except Exception as e:
        print(f"  [FAIL] Health check error: {str(e)}")

async def test_manual_matchmaking():
    """Test manual matchmaking task"""
    print("\n" + "="*60)
    print("TEST 2: Manual Matchmaking Task")
    print("="*60)
    
    try:
        # Run manual matchmaking task
        result = manual_matchmaking.delay()
        
        # Wait for result
        matchmaking_data = result.get(timeout=30)
        
        if matchmaking_data.get('status') == 'success':
            print("  [OK] Manual matchmaking completed")
            print(f"  [OK] Matches found: {matchmaking_data.get('matches_found', 0)}")
            print(f"  [OK] Lobbies in queue: {matchmaking_data.get('lobbies_in_queue', 0)}")
            print(f"  [OK] Confirmations created: {matchmaking_data.get('confirmations_created', 0)}")
        else:
            print(f"  [FAIL] Manual matchmaking failed: {matchmaking_data}")
            
    except Exception as e:
        print(f"  [FAIL] Manual matchmaking error: {str(e)}")

async def test_cleanup_tasks():
    """Test cleanup tasks"""
    print("\n" + "="*60)
    print("TEST 3: Cleanup Tasks")
    print("="*60)
    
    try:
        # Test expired matches cleanup
        print("\n--- Testing Expired Matches Cleanup ---")
        cleanup_result = cleanup_expired_matches.delay()
        cleanup_data = cleanup_result.get(timeout=15)
        
        if cleanup_data.get('status') == 'success':
            print(f"  [OK] Expired matches cleanup: {cleanup_data.get('message')}")
            print(f"  [OK] Processed: {cleanup_data.get('processed_confirmations', 0)}")
            print(f"  [OK] Expired: {cleanup_data.get('expired_matches', 0)}")
        else:
            print(f"  [FAIL] Expired matches cleanup failed: {cleanup_data}")
        
        # Test expired queues cleanup
        print("\n--- Testing Expired Queues Cleanup ---")
        queue_cleanup_result = cleanup_expired_queues.delay()
        queue_cleanup_data = queue_cleanup_result.get(timeout=15)
        
        if queue_cleanup_data.get('status') == 'success':
            print(f"  [OK] Expired queues cleanup: {queue_cleanup_data.get('message')}")
            print(f"  [OK] Cleaned lobbies: {queue_cleanup_data.get('cleaned_lobbies', 0)}")
        else:
            print(f"  [FAIL] Expired queues cleanup failed: {queue_cleanup_data}")
            
    except Exception as e:
        print(f"  [FAIL] Cleanup tasks error: {str(e)}")

async def test_periodic_matchmaking():
    """Test periodic matchmaking task"""
    print("\n" + "="*60)
    print("TEST 4: Periodic Matchmaking Task")
    print("="*60)
    
    try:
        # Run periodic matchmaking task
        result = periodic_matchmaking.delay()
        
        # Wait for result
        periodic_data = result.get(timeout=30)
        
        if periodic_data.get('status') == 'success':
            print("  [OK] Periodic matchmaking completed")
            print(f"  [OK] Matches found: {periodic_data.get('matches_found', 0)}")
            print(f"  [OK] Lobbies in queue: {periodic_data.get('lobbies_in_queue', 0)}")
            print(f"  [OK] Message: {periodic_data.get('message')}")
        else:
            print(f"  [FAIL] Periodic matchmaking failed: {periodic_data}")
            
    except Exception as e:
        print(f"  [FAIL] Periodic matchmaking error: {str(e)}")

async def cleanup_test_data(players):
    """Clean up test data"""
    print("\n" + "="*60)
    print("CLEANUP: Removing Test Data")
    print("="*60)
    
    try:
        # Clear queue first
        await QueueManager._clear_queue()
        print("  [OK] Cleared matchmaking queue")
        
        # Remove test players and their lobbies
        for player in players:
            # Remove lobbies first
            test_lobbies = await sync_to_async(list)(
                Lobby.objects.filter(players=player)
            )
            
            for lobby in test_lobbies:
                await sync_to_async(lobby.delete)()
            
            # Remove player
            await sync_to_async(player.delete)()
            print(f"  [OK] Removed player {player.alias}")
        
        print(f"\n[SUCCESS] Cleanup completed: {len(players)} players removed")
        
    except Exception as e:
        print(f"  [FAIL] Error during cleanup: {e}")

async def main():
    """Main test function"""
    print("="*80)
    print("SCRIM.GG PHASE 2 - CELERY TASKS TEST SUITE")
    print("Testing Celery background tasks for matchmaking")
    print("="*80)
    
    players = []
    
    try:
        # Create test data
        players, lobbies = await create_test_data()
        
        if not lobbies:
            print("[WARNING] No test lobbies created. Some tests may not work properly.")
        
        # Run tests
        await test_health_check()
        await test_manual_matchmaking()
        await test_cleanup_tasks()
        await test_periodic_matchmaking()
        
        print("\n" + "="*80)
        print("[SUCCESS] ALL CELERY TASKS TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR] Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always cleanup
        if players:
            await cleanup_test_data(players)

if __name__ == "__main__":
    # Import sync_to_async here after Django setup
    from asgiref.sync import sync_to_async
    
    # Run the async test suite
    asyncio.run(main())
