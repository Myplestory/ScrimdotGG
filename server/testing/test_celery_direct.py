#!/usr/bin/env python3
"""
Direct Celery Tasks Test for Scrim.GG Phase 2
Tests Celery tasks directly without worker
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
from matchmaking.queue_manager import QueueManager
from matchmaking.matchmaker import Matchmaker
from matchmaking.match_confirmation import MatchConfirmationManager
from matchmaking.lobby_manager import LobbyManager
from scrimgg.models import Player, Lobby

async def create_test_data():
    """Create test data for direct testing"""
    print("Creating test data for direct Celery testing...")
    
    players = []
    lobbies = []
    
    for i in range(4):  # Create 4 players (2 lobbies)
        unique_id = f"test-celery-direct-{int(time.time())}-{i}"
        
        player = await sync_to_async(Player.objects.create)(
            puuid=unique_id,
            alias=f"CeleryDirectPlayer{i}",
            username=f"CeleryDirectPlayer{i}",
            elo=1600 + (i * 50),  # ELO range: 1600-1750
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

async def test_direct_matchmaking():
    """Test matchmaking directly"""
    print("\n" + "="*60)
    print("TEST 1: Direct Matchmaking")
    print("="*60)
    
    try:
        # Test queue stats
        queue_stats = await QueueManager.get_queue_stats()
        print(f"  [OK] Queue stats: {queue_stats}")
        
        # Test matchmaking
        result = await Matchmaker.find_matches()
        
        if result['status'] == 'success':
            matches_found = result.get('matches_found', 0)
            print(f"  [OK] Matchmaking completed: {matches_found} matches found")
            
            if matches_found > 0:
                matches = result.get('matches', [])
                for i, match in enumerate(matches):
                    lobby1_id = match['lobby1']['id'][:8]
                    lobby2_id = match['lobby2']['id'][:8]
                    elo_diff = abs(match['lobby1']['average_elo'] - match['lobby2']['average_elo'])
                    print(f"    Match {i+1}: {lobby1_id}... vs {lobby2_id}... (ELO diff: {elo_diff:.1f})")
                    
                    # Test match confirmation creation
                    confirmation_id = await MatchConfirmationManager.create_match_confirmation(
                        match['lobby1']['id'], match['lobby2']['id']
                    )
                    
                    if confirmation_id:
                        print(f"    [OK] Created match confirmation: {confirmation_id[:8]}...")
                        
                        # Test getting match data
                        match_data = await MatchConfirmationManager.get_match_data(confirmation_id)
                        if match_data:
                            print(f"    [OK] Retrieved match data")
                        else:
                            print(f"    [FAIL] Failed to retrieve match data")
                    else:
                        print(f"    [FAIL] Failed to create match confirmation")
            else:
                print("  [INFO] No matches found (may need more players or different ELO ranges)")
        else:
            print(f"  [FAIL] Matchmaking failed: {result.get('message')}")
            
    except Exception as e:
        print(f"  [FAIL] Direct matchmaking error: {str(e)}")

async def test_match_confirmation_operations():
    """Test match confirmation operations"""
    print("\n" + "="*60)
    print("TEST 2: Match Confirmation Operations")
    print("="*60)
    
    try:
        # Get all active confirmations
        active_confirmations = await MatchConfirmationManager.get_all_active_confirmations()
        print(f"  [OK] Active confirmations: {len(active_confirmations)}")
        
        for confirmation in active_confirmations:
            match_id = confirmation['id']
            
            # Test expiration check
            is_expired = await MatchConfirmationManager.is_match_expired(match_id)
            print(f"  [OK] Match {match_id[:8]}... expired: {is_expired}")
            
            # Test getting match lobbies
            lobbies = await MatchConfirmationManager.get_match_lobbies(match_id)
            print(f"  [OK] Match {match_id[:8]}... has {len(lobbies)} lobbies")
            
            # Test getting accepting players
            accepting = await MatchConfirmationManager.get_accepting_players(match_id)
            print(f"  [OK] Match {match_id[:8]}... has {len(accepting)} accepting players")
            
    except Exception as e:
        print(f"  [FAIL] Match confirmation operations error: {str(e)}")

async def test_cleanup_operations():
    """Test cleanup operations"""
    print("\n" + "="*60)
    print("TEST 3: Cleanup Operations")
    print("="*60)
    
    try:
        # Test queue cleanup
        cleaned_lobbies = await QueueManager.cleanup_expired_lobbies()
        print(f"  [OK] Queue cleanup: {cleaned_lobbies} lobbies cleaned")
        
        # Test expired matches handling
        active_confirmations = await MatchConfirmationManager.get_all_active_confirmations()
        
        for confirmation in active_confirmations:
            match_id = confirmation['id']
            is_expired = await MatchConfirmationManager.is_match_expired(match_id)
            
            if is_expired:
                print(f"  [INFO] Handling expired match: {match_id[:8]}...")
                result = await MatchConfirmationManager.handle_expired_match(match_id)
                
                if result['status'] == 'success':
                    print(f"    [OK] Expired match handled successfully")
                    print(f"    [OK] Affected lobbies: {len(result.get('affected_lobbies', []))}")
                    print(f"    [OK] Requeued lobbies: {len(result.get('requeued_lobbies', []))}")
                else:
                    print(f"    [FAIL] Failed to handle expired match: {result.get('message')}")
        
        print("  [OK] Cleanup operations completed")
        
    except Exception as e:
        print(f"  [FAIL] Cleanup operations error: {str(e)}")

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
    print("SCRIM.GG PHASE 2 - DIRECT CELERY TASKS TEST")
    print("Testing Celery task functionality directly")
    print("="*80)
    
    players = []
    
    try:
        # Create test data
        players, lobbies = await create_test_data()
        
        if not lobbies:
            print("[WARNING] No test lobbies created. Some tests may not work properly.")
        
        # Run tests
        await test_direct_matchmaking()
        await test_match_confirmation_operations()
        await test_cleanup_operations()
        
        print("\n" + "="*80)
        print("[SUCCESS] ALL DIRECT CELERY TESTS COMPLETED")
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
