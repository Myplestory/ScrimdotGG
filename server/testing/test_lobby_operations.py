"""
Test script for Phase 1 Lobby Operations
Run this script to test LobbyManager functionality
"""

import os
import django
import asyncio

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
from matchmaking.lobby_manager import LobbyManager


async def test_create_lobby():
    """Test 1: Create a lobby"""
    print("\n" + "="*60)
    print("TEST 1: Create Lobby")
    print("="*60)
    
    # Get or create test player
    player, created = await asyncio.to_thread(
        Player.objects.get_or_create,
        puuid='test-player-1',
        defaults={
            'username': 'TestPlayer#001',
            'alias': 'TestPlayer1',
            'region': 'na',
            'elo': 1500
        }
    )
    print(f"✓ Test player: {player.alias} (ELO: {player.elo})")
    
    # Create lobby
    result = await LobbyManager.create_lobby('test-player-1')
    
    if result['status'] == 'success':
        print("✅ PASSED: Lobby created successfully")
        lobby_data = result['lobby']
        print(f"   - Lobby ID: {lobby_data['id']}")
        print(f"   - Leader: {lobby_data['lobby_leader']['alias']}")
        print(f"   - Size: {lobby_data['size']}/{lobby_data['max_size']}")
        print(f"   - Average ELO: {lobby_data['average_elo']}")
        return lobby_data['id']
    else:
        print(f"❌ FAILED: {result.get('message')}")
        return None


async def test_add_player_to_lobby(lobby_id):
    """Test 2: Add a player to lobby"""
    print("\n" + "="*60)
    print("TEST 2: Add Player to Lobby")
    print("="*60)
    
    # Create second player
    player2, created = await asyncio.to_thread(
        Player.objects.get_or_create,
        puuid='test-player-2',
        defaults={
            'username': 'TestPlayer#002',
            'alias': 'TestPlayer2',
            'region': 'na',
            'elo': 1550
        }
    )
    print(f"✓ Second player: {player2.alias} (ELO: {player2.elo})")
    
    # Add to lobby
    result = await LobbyManager.add_player_to_lobby(
        lobby_id,
        'test-player-2',
        'test-player-1'  # Inviter
    )
    
    if result['status'] == 'success':
        print("✅ PASSED: Player added successfully")
        lobby_data = result['lobby']
        print(f"   - Size: {lobby_data['size']}/{lobby_data['max_size']}")
        print(f"   - Average ELO: {lobby_data['average_elo']}")
        print(f"   - Players: {[p['alias'] for p in lobby_data['players']]}")
    else:
        print(f"❌ FAILED: {result.get('message')}")


async def test_update_preferences(lobby_id):
    """Test 3: Update lobby preferences"""
    print("\n" + "="*60)
    print("TEST 3: Update Lobby Preferences")
    print("="*60)
    
    maps = ['Ascent', 'Bind', 'Haven', 'Pearl', 'Split']
    servers = ['Virginia', 'Illinois']
    
    result = await LobbyManager.update_lobby_preferences(
        lobby_id,
        map_preferences=maps,
        server_preferences=servers,
        requester_puuid='test-player-1'
    )
    
    if result['status'] == 'success':
        print("✅ PASSED: Preferences updated")
        lobby_data = result['lobby']
        print(f"   - Maps: {lobby_data['map_preferences']}")
        print(f"   - Servers: {lobby_data['server_preferences']}")
    else:
        print(f"❌ FAILED: {result.get('message')}")


async def test_validate_queue_eligibility(lobby_id):
    """Test 4: Validate queue eligibility"""
    print("\n" + "="*60)
    print("TEST 4: Validate Queue Eligibility")
    print("="*60)
    
    result = await LobbyManager.validate_queue_eligibility(lobby_id)
    
    if result['eligible']:
        print("✅ PASSED: Lobby is eligible for queue")
    else:
        print(f"⚠️  Not eligible: {result['reason']}")


async def test_kick_player(lobby_id):
    """Test 5: Kick player from lobby"""
    print("\n" + "="*60)
    print("TEST 5: Kick Player from Lobby")
    print("="*60)
    
    result = await LobbyManager.remove_player_from_lobby(
        lobby_id,
        'test-player-2',
        kicked_by='test-player-1'
    )
    
    if result['status'] == 'success':
        print("✅ PASSED: Player kicked successfully")
        lobby_data = result['lobby']
        print(f"   - Remaining players: {[p['alias'] for p in lobby_data['players']]}")
        print(f"   - Size: {lobby_data['size']}/{lobby_data['max_size']}")
    else:
        print(f"❌ FAILED: {result.get('message')}")


async def test_leave_lobby(lobby_id):
    """Test 6: Player leaves lobby"""
    print("\n" + "="*60)
    print("TEST 6: Player Leaves Lobby")
    print("="*60)
    
    result = await LobbyManager.remove_player_from_lobby(
        lobby_id,
        'test-player-1'
    )
    
    if result['status'] == 'success':
        if result.get('lobby_disbanded'):
            print("✅ PASSED: Player left and lobby disbanded (no players remaining)")
        else:
            print("✅ PASSED: Player left successfully")
            lobby_data = result['lobby']
            print(f"   - New leader: {lobby_data['lobby_leader']['alias']}")
            print(f"   - Remaining players: {[p['alias'] for p in lobby_data['players']]}")
    else:
        print(f"❌ FAILED: {result.get('message')}")


async def test_get_lobby_by_player():
    """Test 7: Get lobby by player"""
    print("\n" + "="*60)
    print("TEST 7: Get Lobby by Player")
    print("="*60)
    
    # Create new lobby for testing
    result = await LobbyManager.create_lobby('test-player-1')
    if result['status'] != 'success':
        print(f"❌ FAILED: Could not create lobby")
        return
    
    lobby_id = result['lobby']['id']
    
    # Get lobby by player
    lobby_data = await LobbyManager.get_lobby_by_player('test-player-1')
    
    if lobby_data:
        print("✅ PASSED: Lobby retrieved successfully")
        print(f"   - Lobby ID: {lobby_data['id']}")
        print(f"   - Leader: {lobby_data['lobby_leader']['alias']}")
    else:
        print("❌ FAILED: Could not retrieve lobby")
    
    return lobby_id


async def cleanup():
    """Cleanup test data"""
    print("\n" + "="*60)
    print("CLEANUP: Removing test data")
    print("="*60)
    
    # Delete test lobbies
    deleted_lobbies = await asyncio.to_thread(
        Lobby.objects.filter(
            lobby_leader__puuid__in=['test-player-1', 'test-player-2']
        ).delete
    )
    print(f"✓ Deleted {deleted_lobbies[0]} test lobbies")
    
    # Delete test players
    deleted_players = await asyncio.to_thread(
        Player.objects.filter(
            puuid__in=['test-player-1', 'test-player-2']
        ).delete
    )
    print(f"✓ Deleted {deleted_players[0]} test players")


async def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*60)
    print("PHASE 1 LOBBY OPERATIONS TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Create lobby
        lobby_id = await test_create_lobby()
        if not lobby_id:
            print("\n❌ Test suite stopped: Could not create lobby")
            return
        
        # Test 2: Add player
        await test_add_player_to_lobby(lobby_id)
        
        # Test 3: Update preferences
        await test_update_preferences(lobby_id)
        
        # Test 4: Validate queue eligibility
        await test_validate_queue_eligibility(lobby_id)
        
        # Test 5: Kick player
        await test_kick_player(lobby_id)
        
        # Test 6: Leave lobby
        await test_leave_lobby(lobby_id)
        
        # Test 7: Get lobby by player
        await test_get_lobby_by_player()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST SUITE ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await cleanup()


if __name__ == '__main__':
    asyncio.run(run_all_tests())

