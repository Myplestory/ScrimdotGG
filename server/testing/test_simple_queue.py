#!/usr/bin/env python3
"""
Simple Queue Test for Scrim.GG Phase 2
Quick test to verify queue operations work
"""

import os
import sys
import django
import asyncio

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from asgiref.sync import sync_to_async
from matchmaking.queue_manager import QueueManager
from matchmaking.matchmaker import Matchmaker
from matchmaking.match_confirmation import MatchConfirmationManager
from matchmaking.lobby_manager import LobbyManager
from scrimgg.models import Player, Lobby

async def simple_queue_test():
    """Simple test of queue operations"""
    print("="*60)
    print("SIMPLE QUEUE TEST")
    print("="*60)
    
    try:
        # Test 1: Redis Connection
        print("\n1. Testing Redis Connection...")
        redis = QueueManager.get_redis()
        redis.ping()
        print("   [OK] Redis connection working")
        
        # Test 2: Create test player and lobby
        print("\n2. Creating test player and lobby...")
        
        # Create player with unique ID
        import time
        unique_id = f"test-queue-player-{int(time.time())}"
        
        player = await sync_to_async(Player.objects.create)(
            puuid=unique_id,
            alias=f"QueueTestPlayer_{int(time.time())}",
            username=f"QueueTestPlayer_{int(time.time())}",
            elo=1600,
            region="NA",
            team="Test Team"
        )
        print(f"   [OK] Created player: {player.alias}")
        
        # Create lobby
        result = await LobbyManager.create_lobby(player.puuid)
        if result['status'] == 'success':
            lobby_id = result['lobby']['id']
            print(f"   [OK] Created lobby: {lobby_id[:8]}...")
            
            # Set map preferences (required for queue eligibility)
            map_prefs = ['bind', 'haven', 'split', 'ascent', 'icebox']  # 5 maps minimum
            server_prefs = ['NA']
            
            prefs_result = await LobbyManager.update_lobby_preferences(
                lobby_id, map_prefs, server_prefs, player.puuid
            )
            
            if prefs_result['status'] == 'success':
                print(f"   [OK] Set map preferences: {len(map_prefs)} maps")
            else:
                print(f"   [FAIL] Failed to set preferences: {prefs_result.get('message')}")
                return
        else:
            print(f"   [FAIL] Failed to create lobby: {result.get('message')}")
            return
        
        # Test 3: Join queue
        print("\n3. Testing queue join...")
        queue_result = await QueueManager.join_queue(lobby_id, player.puuid)
        
        if queue_result['status'] == 'success':
            print(f"   [OK] Joined queue successfully")
            print(f"   [OK] Queue position: {queue_result.get('queue_position', 'N/A')}")
        else:
            print(f"   [FAIL] Failed to join queue: {queue_result.get('message')}")
        
        # Test 4: Check queue status
        print("\n4. Testing queue status...")
        status_result = await QueueManager.get_queue_status(lobby_id)
        
        if status_result['status'] == 'success':
            print(f"   [OK] Queue size: {status_result.get('queue_size', 0)}")
            print(f"   [OK] In queue: {status_result.get('in_queue', False)}")
        else:
            print(f"   [FAIL] Failed to get queue status: {status_result.get('message')}")
        
        # Test 5: Leave queue
        print("\n5. Testing queue leave...")
        leave_result = await QueueManager.leave_queue(lobby_id, player.puuid)
        
        if leave_result['status'] == 'success':
            print(f"   [OK] Left queue successfully")
        else:
            print(f"   [FAIL] Failed to leave queue: {leave_result.get('message')}")
        
        # Test 6: Verify queue is empty
        print("\n6. Verifying queue is empty...")
        final_status = await QueueManager.get_queue_status(lobby_id)
        
        if final_status['status'] == 'success':
            in_queue = final_status.get('in_queue', False)
            queue_size = final_status.get('queue_size', 0)
            
            if not in_queue and queue_size == 0:
                print("   [OK] Queue is empty as expected")
            else:
                print(f"   [FAIL] Queue not empty: in_queue={in_queue}, size={queue_size}")
        
        # Cleanup
        print("\n7. Cleaning up...")
        await sync_to_async(player.delete)()
        print("   [OK] Test player deleted")
        
        print("\n" + "="*60)
        print("[SUCCESS] SIMPLE QUEUE TEST PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_queue_test())
