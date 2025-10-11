"""
Quick cleanup script for bot players
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
from matchmaking.queue_manager import QueueManager
from asgiref.sync import sync_to_async
import asyncio

async def cleanup():
    print("Cleaning up old bot players...")
    
    # Remove from queue first
    def get_bot_lobbies():
        return list(Lobby.objects.filter(lobby_leader__puuid__startswith='queuebot-'))
    
    bot_lobbies = await sync_to_async(get_bot_lobbies)()
    print(f"Found {len(bot_lobbies)} bot lobbies in queue")
    
    for lobby in bot_lobbies:
        try:
            await QueueManager.leave_queue(lobby.id, lobby.lobby_leader.puuid)
            print(f"Removed {lobby.lobby_leader.alias} from queue")
        except Exception as e:
            print(f"Error removing {lobby.lobby_leader.alias}: {e}")
    
    # Delete lobbies
    def delete_lobbies_and_players():
        lobby_count = Lobby.objects.filter(lobby_leader__puuid__startswith='queuebot-').count()
        player_count = Player.objects.filter(puuid__startswith='queuebot-').count()
        
        Lobby.objects.filter(lobby_leader__puuid__startswith='queuebot-').delete()
        Player.objects.filter(puuid__startswith='queuebot-').delete()
        
        return lobby_count, player_count
    
    lobby_count, player_count = await sync_to_async(delete_lobbies_and_players)()
    
    print(f"Cleaned up {lobby_count} lobbies and {player_count} players")

if __name__ == '__main__':
    asyncio.run(cleanup())
