"""
Check current lobby state for debugging
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby

def check_lobby():
    print("Checking your lobby state...")
    
    # Find your player
    you = Player.objects.filter(username__icontains='evisc').first()
    if not you:
        print("Player not found!")
        return
    
    print(f"Found player: {you.alias}")
    print(f"PUUID: {you.puuid}")
    
    # Find your lobby
    lobby = Lobby.objects.filter(players=you, is_active=True).first()
    if not lobby:
        print("No active lobby found!")
        return
    
    print(f"\nLobby ID: {lobby.id}")
    print(f"Lobby Leader: {lobby.lobby_leader.alias}")
    print(f"Is Active: {lobby.is_active}")
    print(f"In Queue: {lobby.in_queue}")
    print(f"Size: {lobby.size}")
    print(f"Map Preferences: {lobby.map_preferences}")
    print(f"Map Preferences Count: {len(lobby.map_preferences) if lobby.map_preferences else 0}")
    print(f"Players: {[p.alias for p in lobby.players.all()]}")
    
    # Check if lobby can join queue
    from matchmaking.lobby_manager import LobbyManager
    import asyncio
    
    async def validate():
        result = await LobbyManager.validate_queue_eligibility(str(lobby.id))
        print(f"\nQueue Eligibility: {result}")
        return result
    
    result = asyncio.run(validate())
    
    if not result.get('eligible', False):
        print(f"\n❌ CANNOT JOIN QUEUE: {result.get('reason', 'Unknown reason')}")
    else:
        print(f"\n✅ CAN JOIN QUEUE")

if __name__ == '__main__':
    check_lobby()
