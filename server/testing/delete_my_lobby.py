"""
Delete your existing lobby to test the complete flow from scratch
"""
import os
import sys
import django

# Add parent directory to Python path so Django can find the settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
import redis
from django.conf import settings

def delete_lobby():
    print("Deleting your existing lobby...")
    
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
    
    print(f"Found lobby: {lobby.id}")
    print(f"Lobby leader: {lobby.lobby_leader.alias}")
    print(f"Is active: {lobby.is_active}")
    print(f"In queue: {lobby.in_queue}")
    
    # Connect to Redis to remove from queue if it's there
    redis_client = redis.from_url(settings.CACHES['default']['LOCATION'])
    queue_key = "matchmaking:queue:pug"
    
    # Remove from Redis queue if present
    removed_from_queue = redis_client.zrem(queue_key, str(lobby.id))
    if removed_from_queue:
        print(f"Removed lobby from Redis queue")
        
        # Clean up Redis data
        lobby_data_key = f"matchmaking:lobby_data:{lobby.id}"
        queue_time_key = f"matchmaking:queue_time:{lobby.id}"
        redis_client.delete(lobby_data_key, queue_time_key)
        print(f"Cleaned up Redis lobby data")
    else:
        print(f"Lobby was not in Redis queue")
    
    # Delete the lobby from database
    lobby_id = lobby.id
    lobby.delete()
    
    print(f"Deleted lobby {lobby_id} from database")
    print("SUCCESS: Your lobby has been completely removed!")
    print("\nNow you can test the complete flow:")
    print("1. Click 'Find Match' in your client")
    print("2. Client should create a new lobby")
    print("3. Client should join the queue")
    print("4. You should see 10 players in queue (9 bots + you)")

if __name__ == '__main__':
    delete_lobby()
