"""
Simple cleanup script for bot players

This script cleans up:
- Bot/test players and lobbies
- ALL Match instances (including READY state matches)
- Redis queue entries and match confirmations

READY State Matches:
- These are matches where side selection has completed
- They are waiting for match execution to start
- A constructor would be assigned to create the custom game
- If left uncleaned, they can cause issues with new matches
"""
import os
import sys
import django

# Add server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player, Lobby
from matchmaking.models_match import Match, MatchPlayer, VetoAction
import redis
from django.conf import settings
from django.db.models import Q

print("Cleaning up ALL test/bot players...")

# Connect to Redis
redis_client = redis.from_url(settings.CACHES['default']['LOCATION'])

# Define all bot/test patterns (both PUUID prefixes and alias patterns)
BOT_PUUID_PREFIXES = [
    'queuebot-',
    'bot-',
    'bot-player-',
    'sim-player-',
    'test-player-',
    'test-celery-'
]

BOT_ALIAS_PATTERNS = [
    'QueueBot',
    'Bot',
    'TestBot',
    'SimBot'
]

# Build a query to find all bot/test lobbies (both old and new format)
lobby_query = Q()

# Old format: PUUID-based bots
for prefix in BOT_PUUID_PREFIXES:
    lobby_query |= Q(lobby_leader__puuid__startswith=prefix)

# New format: UUID-based bots with recognizable aliases
for pattern in BOT_ALIAS_PATTERNS:
    lobby_query |= Q(lobby_leader__alias__startswith=pattern)
    lobby_query |= Q(lobby_leader__username__startswith=pattern)

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

# Clear all match confirmations from Redis
print("\nClearing all match confirmations...")
match_conf_keys = redis_client.keys('match_confirmation:*')
if match_conf_keys:
    for key in match_conf_keys:
        redis_client.delete(key)
    print(f"Cleared {len(match_conf_keys)} match confirmations")
else:
    print("No match confirmations to clear")

# Clean up ALL Match instances (not just bot matches)
print("\nCleaning up ALL Match instances...")
try:
    all_matches = Match.objects.all()
    match_count = all_matches.count()

    if match_count > 0:
        print(f"Found {match_count} total match(es) in database")
        
        # Group matches by state for better reporting
        matches_by_state = {}
        for match in all_matches:
            state = match.state
            if state not in matches_by_state:
                matches_by_state[state] = []
            matches_by_state[state].append(match)
        
        # Show match details by state
        for state, matches in matches_by_state.items():
            print(f"  - {len(matches)} match(es) in state '{state}':")
            for match in matches:
                print(f"    • Match {match.id}: created={match.created_at}")
                
                # Safely access fields that might not exist yet
                try:
                    final_map = match.final_map
                    print(f"      - Final map: {final_map}")
                except AttributeError:
                    print(f"      - Final map: (field not available)")
                
                if state == 'READY':
                    try:
                        constructor = match.constructor_puuid
                        side = match.selected_side
                        server = getattr(match, 'final_server', None) or getattr(match, 'server_region', None)
                        print(f"      - Constructor: {constructor}")
                        print(f"      - Side: {side}")
                        print(f"      - Server: {server}")
                    except AttributeError as e:
                        print(f"      - Additional fields: (not available - {e})")
    
        # Delete related MatchPlayer and VetoAction records first
        match_ids = list(all_matches.values_list('id', flat=True))
        veto_count = VetoAction.objects.filter(match_id__in=match_ids).count()
        player_count_in_matches = MatchPlayer.objects.filter(match_id__in=match_ids).count()
        
        VetoAction.objects.filter(match_id__in=match_ids).delete()
        MatchPlayer.objects.filter(match_id__in=match_ids).delete()
        all_matches.delete()
        
        print(f"  ✅ Deleted {match_count} Match instances")
        print(f"  ✅ Deleted {player_count_in_matches} MatchPlayer records")
        print(f"  ✅ Deleted {veto_count} VetoAction records")
        
        # Special note for READY state matches
        if 'READY' in matches_by_state:
            ready_count = len(matches_by_state['READY'])
            print(f"  ⚠️  {ready_count} match(es) were in 'READY' state (side selection complete, waiting for match execution)")
    else:
        print("  No matches found in database")
        
except Exception as e:
    print(f"  Error accessing matches: {e}")
    print("  This might be due to pending database migrations.")
    print("  Run: python manage.py migrate")
    
    # Try to delete matches using raw SQL as fallback
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM matchmaking_match")
            deleted_count = cursor.rowcount
            print(f"  Fallback: Deleted {deleted_count} match(es) using raw SQL")
    except Exception as fallback_error:
        print(f"  Fallback deletion also failed: {fallback_error}")

# Build a query to find all bot/test players (both old and new format)
player_query = Q()

# Old format: PUUID-based bots
for prefix in BOT_PUUID_PREFIXES:
    player_query |= Q(puuid__startswith=prefix)

# New format: UUID-based bots with recognizable aliases
for pattern in BOT_ALIAS_PATTERNS:
    player_query |= Q(alias__startswith=pattern)
    player_query |= Q(username__startswith=pattern)

player_count = Player.objects.filter(player_query).count()
print(f"Found {player_count} test/bot players in database")

# Delete everything from database
bot_lobbies.delete()
Player.objects.filter(player_query).delete()

print(f"\n{'='*60}")
print(f"CLEANUP SUMMARY")
print(f"{'='*60}")
print(f"\nDatabase:")
print(f"  - Lobbies:        {lobby_count}")
print(f"  - Players:        {player_count}")
print(f"  - Matches:        {match_count}")
if match_count > 0:
    print(f"    • MatchPlayers: {player_count_in_matches}")
    print(f"    • VetoActions:  {veto_count}")
    # Show state breakdown
    if 'matches_by_state' in locals():
        print(f"    • Match States:")
        for state, matches in matches_by_state.items():
            print(f"      - {state}: {len(matches)} match(es)")
print(f"\nRedis:")
print(f"  - Queue lobbies:          {removed_from_queue + orphaned_count}")
print(f"    • With DB entries:      {removed_from_queue}")
print(f"    • Orphaned (no DB):     {orphaned_count}")
print(f"  - Match confirmations:    {len(match_conf_keys) if match_conf_keys else 0}")
print(f"\n{'='*60}")
print(f"[NOTE] WebSocket Cleanup:")
print(f"  - Bot connections auto-close when test script exits")
print(f"  - If crashed: connections timeout naturally (30-60s)")
print(f"  - Or restart Daphne to force close all connections")
print(f"\n[NOTE] READY State Matches:")
print(f"  - These were matches where side selection completed")
print(f"  - They were waiting for match execution to start")
print(f"  - Constructor would have been assigned to create custom game")
print(f"{'='*60}")
print(f"\n[SUCCESS] Cleanup complete! System is clean for next test.\n")
