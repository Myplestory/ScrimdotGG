"""
Fix lobby map preferences for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby

def fix_lobby():
    print("Fixing your lobby map preferences...")
    
    # Find your player
    you = Player.objects.filter(username__icontains='evisc').first()
    if not you:
        print("Player not found!")
        return
    
    print(f"Found player: {you.alias}")
    
    # Find your lobby
    lobby = Lobby.objects.filter(players=you, is_active=True).first()
    if not lobby:
        print("No active lobby found!")
        return
    
    print(f"Lobby ID: {lobby.id}")
    print(f"Current map preferences: {lobby.map_preferences}")
    
    # Set all 9 maps as selected (same as your client UI)
    all_maps = [
        "Ascent", "Bind", "Breeze", "Fracture", "Haven", 
        "Icebox", "Lotus", "Pearl", "Split"
    ]
    
    lobby.map_preferences = all_maps
    lobby.save()
    
    print(f"Updated map preferences to: {lobby.map_preferences}")
    print(f"Map count: {len(lobby.map_preferences)}")
    
    # Check eligibility again
    from matchmaking.lobby_manager import LobbyManager
    import asyncio
    
    async def validate():
        result = await LobbyManager.validate_queue_eligibility(str(lobby.id))
        return result
    
    result = asyncio.run(validate())
    
    if result.get('eligible', False):
        print("SUCCESS: Lobby can now join queue!")
    else:
        print(f"STILL CANNOT JOIN: {result.get('reason', 'Unknown reason')}")

if __name__ == '__main__':
    fix_lobby()
