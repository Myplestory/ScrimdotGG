"""
Debug the queue joining process for your lobby
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
from matchmaking.queue_manager import QueueManager
from matchmaking.lobby_manager import LobbyManager
from asgiref.sync import sync_to_async
import asyncio

async def debug_queue_join():
    print("Debugging queue join process...")
    
    # Find your player and lobby
    def get_player_and_lobby():
        you = Player.objects.filter(username__icontains='evisc').first()
        if you:
            lobby = Lobby.objects.select_related('lobby_leader').filter(players=you, is_active=True).first()
            return you, lobby
        return None, None
    
    you, lobby = await sync_to_async(get_player_and_lobby)()
    
    if not you or not lobby:
        print("Player or lobby not found!")
        return
    
    print(f"Player: {you.alias}")
    print(f"Lobby ID: {lobby.id}")
    print(f"Lobby Leader: {lobby.lobby_leader.alias}")
    print(f"Is Active: {lobby.is_active}")
    print(f"In Queue: {lobby.in_queue}")
    print(f"Map Preferences: {lobby.map_preferences}")
    
    # Test validation
    print("\n1. Testing validation...")
    validation = await LobbyManager.validate_queue_eligibility(str(lobby.id))
    print(f"Validation result: {validation}")
    
    if not validation.get('eligible', False):
        print(f"❌ Cannot join queue: {validation.get('reason')}")
        return
    
    # Test lobby serialization
    print("\n2. Testing lobby serialization...")
    try:
        lobby_data = await LobbyManager._serialize_lobby(lobby)
        print(f"Serialized lobby data: {lobby_data}")
    except Exception as e:
        print(f"❌ Serialization failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test queue join
    print("\n3. Testing queue join...")
    try:
        result = await QueueManager.join_queue(str(lobby.id), you.puuid, 'pug')
        print(f"Queue join result: {result}")
    except Exception as e:
        print(f"❌ Queue join failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check final queue stats
    print("\n4. Final queue stats...")
    queue_stats = await QueueManager.get_queue_stats('pug')
    print(f"Queue stats: {queue_stats}")

if __name__ == '__main__':
    asyncio.run(debug_queue_join())
