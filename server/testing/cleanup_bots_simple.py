"""
Simple cleanup script for bot players
"""
import os
import sys
import django

# Add server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
import redis
from django.conf import settings
from django.db.models import Q

print("Cleaning up ALL test/bot players...")

# Connect to Redis
redis_client = redis.from_url(settings.CACHES['default']['LOCATION'])

# Define all bot/test prefixes
BOT_PREFIXES = [
    'queuebot-',
    'bot-',
    'bot-player-',
    'sim-player-',
    'test-player-',
    'test-celery-'
]

# Build a query to find all bot/test lobbies
lobby_query = Q()
for prefix in BOT_PREFIXES:
    lobby_query |= Q(lobby_leader__puuid__startswith=prefix)

bot_lobbies = Lobby.objects.filter(lobby_query)
lobby_count = bot_lobbies.count()
print(f"Found {lobby_count} test/bot lobbies in database")

# Remove each bot lobby from Redis queue
queue_key = "matchmaking:queue:pug"
removed_from_queue = 0

for lobby in bot_lobbies:
    # Remove from sorted set
    result = redis_client.zrem(queue_key, str(lobby.id))
    if result:
        removed_from_queue += 1
    
    # Remove lobby data
    lobby_data_key = f"matchmaking:lobby_data:{lobby.id}"
    redis_client.delete(lobby_data_key)
    
    # Remove queue time
    queue_time_key = f"matchmaking:queue_time:{lobby.id}"
    redis_client.delete(queue_time_key)

print(f"Removed {removed_from_queue} lobbies from Redis queue (found in database)")

# Now check for orphaned entries in Redis (lobbies that don't exist in database)
print("\nChecking for orphaned Redis entries...")
all_queue_entries = redis_client.zrange(queue_key, 0, -1)
orphaned_count = 0

for lobby_id_bytes in all_queue_entries:
    lobby_id = lobby_id_bytes.decode('utf-8') if isinstance(lobby_id_bytes, bytes) else lobby_id_bytes
    
    # Check if this lobby exists in database
    lobby_exists = Lobby.objects.filter(id=lobby_id).exists()
    
    if not lobby_exists:
        # This is an orphaned entry - remove it
        redis_client.zrem(queue_key, lobby_id)
        redis_client.delete(f"matchmaking:lobby_data:{lobby_id}")
        redis_client.delete(f"matchmaking:queue_time:{lobby_id}")
        orphaned_count += 1

print(f"Removed {orphaned_count} orphaned lobbies from Redis queue")

# Build a query to find all bot/test players
player_query = Q()
for prefix in BOT_PREFIXES:
    player_query |= Q(puuid__startswith=prefix)

player_count = Player.objects.filter(player_query).count()
print(f"Found {player_count} test/bot players in database")

# Delete everything from database
bot_lobbies.delete()
Player.objects.filter(player_query).delete()

print(f"\n=== CLEANUP SUMMARY ===")
print(f"Database: Cleaned up {lobby_count} lobbies and {player_count} players")
print(f"Redis: Cleaned up {removed_from_queue + orphaned_count} total lobbies from queue")
print(f"  - {removed_from_queue} lobbies with database entries")
print(f"  - {orphaned_count} orphaned lobbies (no database entry)")
print("Done!")
