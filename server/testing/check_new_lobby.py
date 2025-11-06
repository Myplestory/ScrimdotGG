"""
Check the state of your new lobby
"""
import os
import sys
import django

# Add parent directory to Python path so Django can find the settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
from matchmaking.lobby_manager import LobbyManager
from asgiref.sync import sync_to_async
import asyncio

async def check_lobby():
    print("Checking your new lobby state...")
    
    # Find your player
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
    print(f"Map Preferences Count: {len(lobby.map_preferences) if lobby.map_preferences else 0}")
    
    # Test validation
    validation = await LobbyManager.validate_queue_eligibility(str(lobby.id))
    print(f"\nQueue Eligibility: {validation}")
    
    if not validation.get('eligible', False):
        print(f"❌ CANNOT JOIN QUEUE: {validation.get('reason', 'Unknown reason')}")
    else:
        print(f"✅ CAN JOIN QUEUE")

if __name__ == '__main__':
    asyncio.run(check_lobby())
