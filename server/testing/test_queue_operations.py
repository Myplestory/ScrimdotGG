#!/usr/bin/env python3
"""
Test Queue Operations for Scrim.GG Phase 2
Tests the complete queue system including QueueManager, Matchmaker, and MatchConfirmationManager
"""

import os
import sys
import django
import asyncio
import json
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from matchmaking.queue_manager import QueueManager
from matchmaking.matchmaker import Matchmaker
from matchmaking.match_confirmation import MatchConfirmationManager
from matchmaking.lobby_manager import LobbyManager
from scrimgg.models import Player, Lobby

async def create_test_players():
    """Create test players for queue testing"""
    print("Creating test players...")
    
    players = []
    for i in range(12):  # Create 12 players (enough for 2 full matches + 2 extra)
        try:
            player = await sync_to_async(Player.objects.create)(
                puuid=f"test-player-{i:02d}",
                alias=f"TestPlayer{i:02d}",
                elo=1500 + (i * 50),  # ELO range: 1500-2050
                region="NA",
                is_online=True
            )
            players.append(player)
            print(f"  ✓ Created {player.alias} (ELO: {player.elo})")
        except Exception as e:
            print(f"  ✗ Failed to create test player {i}: {e}")
    
    return players

async def create_test_lobbies(players):
    """Create test lobbies"""
    print("\nCreating test lobbies...")
    
    lobbies = []
    
    # Create 6 lobbies (mix of solo and party)
    lobby_configs = [
        {"players": [0], "name": "Solo Player 1"},
        {"players": [1, 2], "name": "Duo Party 1"},
        {"players": [3], "name": "Solo Player 2"},
        {"players": [4, 5, 6], "name": "Trio Party 1"},
        {"players": [7], "name": "Solo Player 3"},
        {"players": [8, 9, 10, 11], "name": "4-Stack Party 1"},
    ]
    
    for i, config in enumerate(lobby_configs):
        try:
            # Create lobby with first player as leader
            leader_puuid = players[config["players"][0]].puuid
            result = await LobbyManager.create_lobby(leader_puuid)
            
            if result['status'] == 'success':
                lobby_id = result['lobby']['id']
                lobby = result['lobby']
                
                # Add additional players if it's a party
                for player_idx in config["players"][1:]:
                    player_puuid = players[player_idx].puuid
                    add_result = await LobbyManager.add_player_to_lobby(
                        lobby_id, player_puuid, leader_puuid
                    )
                    if add_result['status'] != 'success':
                        print(f"  ✗ Failed to add player {player_idx} to lobby: {add_result.get('message')}")
                
                lobbies.append({
                    'id': lobby_id,
                    'name': config["name"],
                    'players': [players[idx] for idx in config["players"]],
                    'data': result['lobby']
                })
                print(f"  ✓ Created {config['name']} (Lobby: {lobby_id[:8]}...)")
            else:
                print(f"  ✗ Failed to create lobby {config['name']}: {result.get('message')}")
                
        except Exception as e:
            print(f"  ✗ Error creating lobby {config['name']}: {e}")
    
    return lobbies

async def test_queue_operations(lobbies):
    """Test queue join/leave operations"""
    print("\n" + "="*60)
    print("TEST 1: Queue Operations")
    print("="*60)
    
    # Test joining queue
    print("\n--- Joining Queue ---")
    for i, lobby in enumerate(lobbies[:4]):  # Join first 4 lobbies
        lobby_id = lobby['id']
        leader_puuid = lobby['players'][0].puuid
        
        try:
            result = await QueueManager.join_queue(lobby_id, leader_puuid)
            
            if result['status'] == 'success':
                print(f"  ✓ Lobby {lobby['name']} joined queue (Position: {result.get('queue_position', 'N/A')})")
            else:
                print(f"  ✗ Failed to join queue: {result.get('message')}")
                
        except Exception as e:
            print(f"  ✗ Error joining queue: {e}")
    
    # Check queue status
    print("\n--- Queue Status ---")
    try:
        queue_status = await QueueManager.get_queue_status(lobbies[0]['id'])
        print(f"  ✓ Queue size: {queue_status.get('queue_size', 0)}")
        print(f"  ✓ Estimated wait: {queue_status.get('estimated_wait', 'N/A')} seconds")
        
        # Show queue contents
        queue_contents = await QueueManager._get_queue_contents()
        print(f"  ✓ Lobbies in queue: {len(queue_contents)}")
        for lobby_data in queue_contents:
            print(f"    - {lobby_data['lobby_id'][:8]}... (ELO: {lobby_data['elo']})")
            
    except Exception as e:
        print(f"  ✗ Error getting queue status: {e}")
    
    # Test leaving queue
    print("\n--- Leaving Queue ---")
    try:
        # Leave first lobby from queue
        lobby_id = lobbies[0]['id']
        leader_puuid = lobbies[0]['players'][0].puuid
        
        result = await QueueManager.leave_queue(lobby_id, leader_puuid)
        
        if result['status'] == 'success':
            print(f"  ✓ Lobby {lobbies[0]['name']} left queue")
        else:
            print(f"  ✗ Failed to leave queue: {result.get('message')}")
            
    except Exception as e:
        print(f"  ✗ Error leaving queue: {e}")

async def test_matchmaking(lobbies):
    """Test matchmaking algorithm"""
    print("\n" + "="*60)
    print("TEST 2: Matchmaking Algorithm")
    print("="*60)
    
    # Ensure we have lobbies in queue
    print("\n--- Preparing Queue ---")
    for lobby in lobbies[:4]:
        lobby_id = lobby['id']
        leader_puuid = lobby['players'][0].puuid
        await QueueManager.join_queue(lobby_id, leader_puuid)
    
    print("  ✓ Added 4 lobbies to queue")
    
    # Test matchmaking
    print("\n--- Running Matchmaker ---")
    try:
        result = await Matchmaker.find_matches()
        
        if result['status'] == 'success':
            matches_found = result.get('matches_found', 0)
            print(f"  ✓ Matchmaker completed successfully")
            print(f"  ✓ Matches found: {matches_found}")
            
            if matches_found > 0:
                matches = result.get('matches', [])
                for i, match in enumerate(matches):
                    lobby1_id = match['lobby1']['id'][:8]
                    lobby2_id = match['lobby2']['id'][:8]
                    elo_diff = abs(match['lobby1']['average_elo'] - match['lobby2']['average_elo'])
                    print(f"    Match {i+1}: {lobby1_id}... vs {lobby2_id}... (ELO diff: {elo_diff:.1f})")
            else:
                print("  ℹ No matches found (insufficient players or ELO mismatch)")
        else:
            print(f"  ✗ Matchmaker failed: {result.get('message')}")
            
    except Exception as e:
        print(f"  ✗ Error in matchmaking: {e}")

async def test_match_confirmation():
    """Test match confirmation system"""
    print("\n" + "="*60)
    print("TEST 3: Match Confirmation System")
    print("="*60)
    
    # Create a test match confirmation
    print("\n--- Creating Test Match ---")
    try:
        # Create two test lobbies
        test_lobbies = []
        for i in range(2):
            leader_puuid = f"test-confirmation-{i}"
            
            # Create player first
            player = await sync_to_async(Player.objects.create)(
                puuid=leader_puuid,
                alias=f"ConfirmationPlayer{i}",
                elo=1600,
                region="NA",
                is_online=True
            )
            
            # Create lobby
            result = await LobbyManager.create_lobby(leader_puuid)
            if result['status'] == 'success':
                test_lobbies.append(result['lobby'])
        
        if len(test_lobbies) >= 2:
            # Create match confirmation
            match_confirmation_id = await MatchConfirmationManager.create_match_confirmation(
                test_lobbies[0]['id'], test_lobbies[1]['id']
            )
            
            print(f"  ✓ Created match confirmation: {match_confirmation_id}")
            
            # Test player acceptance
            print("\n--- Testing Player Acceptance ---")
            for i, lobby in enumerate(test_lobbies):
                leader_puuid = lobby['leader']['puuid']
                
                result = await MatchConfirmationManager.accept_match(match_confirmation_id, leader_puuid)
                
                if result['status'] == 'success':
                    accepted_count = result.get('accepted_count', 0)
                    total_players = result.get('total_players', 0)
                    match_confirmed = result.get('match_confirmed', False)
                    
                    print(f"  ✓ Player {leader_puuid} accepted ({accepted_count}/{total_players})")
                    
                    if match_confirmed:
                        print(f"  ✓ Match confirmed! Match ID: {result.get('match_id')}")
                        break
                else:
                    print(f"  ✗ Failed to accept match: {result.get('message')}")
            
            # Test declining match
            print("\n--- Testing Match Decline ---")
            decline_result = await MatchConfirmationManager.decline_match(
                match_confirmation_id, test_lobbies[0]['leader']['puuid']
            )
            
            if decline_result['status'] == 'success':
                print(f"  ✓ Match declined successfully")
                print(f"  ✓ Affected lobbies: {len(decline_result.get('affected_lobbies', []))}")
            else:
                print(f"  ✗ Failed to decline match: {decline_result.get('message')}")
                
        else:
            print("  ✗ Failed to create test lobbies for confirmation")
            
    except Exception as e:
        print(f"  ✗ Error in match confirmation test: {e}")

async def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "="*60)
    print("CLEANUP: Removing Test Data")
    print("="*60)
    
    try:
        # Remove test players and lobbies
        test_players = await sync_to_async(list)(Player.objects.filter(puuid__startswith="test-"))
        test_lobbies = await sync_to_async(list)(Lobby.objects.filter(players__puuid__startswith="test-").distinct())
        
        # Remove lobbies first (to avoid foreign key constraints)
        for lobby in test_lobbies:
            await sync_to_async(lobby.delete)()
            print(f"  ✓ Removed lobby {lobby.id}")
        
        # Remove players
        for player in test_players:
            await sync_to_async(player.delete)()
            print(f"  ✓ Removed player {player.alias}")
        
        # Clear queue
        await QueueManager._clear_queue()
        print("  ✓ Cleared matchmaking queue")
        
        print(f"\n✅ Cleanup completed: {len(test_lobbies)} lobbies, {len(test_players)} players removed")
        
    except Exception as e:
        print(f"  ✗ Error during cleanup: {e}")

async def main():
    """Main test function"""
    print("="*80)
    print("SCRIM.GG PHASE 2 - QUEUE OPERATIONS TEST SUITE")
    print("Testing QueueManager, Matchmaker, and MatchConfirmationManager")
    print("="*80)
    
    try:
        # Create test data
        players = await create_test_players()
        lobbies = await create_test_lobbies(players)
        
        if not lobbies:
            print("❌ No test lobbies created. Aborting tests.")
            return
        
        # Run tests
        await test_queue_operations(lobbies)
        await test_matchmaking(lobbies)
        await test_match_confirmation()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always cleanup
        await cleanup_test_data()

if __name__ == "__main__":
    # Import sync_to_async here after Django setup
    from asgiref.sync import sync_to_async
    
    # Run the async test suite
    asyncio.run(main())
