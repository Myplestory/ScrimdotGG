"""Monitor queue and match state in real-time"""
import redis
import json
import time
import sys

r = redis.from_url('redis://localhost:6379/0')

print("=" * 70)
print("MONITORING QUEUE AND MATCH STATE")
print("=" * 70)
print("Press Ctrl+C to stop\n")

prev_lobby_count = 0
prev_match_count = 0

try:
    while True:
        # Get current state
        lobby_ids = r.zrange('matchmaking:queue:pug', 0, -1)
        lobby_count = len(lobby_ids)
        
        match_keys = r.keys('matchmaking:match:*')
        match_count = len([k for k in match_keys if b':data' in k])
        
        accepted_keys = [k for k in match_keys if b':accepted' in k]
        
        # Detect changes
        if lobby_count != prev_lobby_count or match_count != prev_match_count:
            timestamp = time.strftime("%H:%M:%S")
            print(f"\n[{timestamp}] ⚡ STATE CHANGE:")
            print(f"  Lobbies in queue: {lobby_count} (was {prev_lobby_count})")
            print(f"  Active matches: {match_count} (was {prev_match_count})")
            
            if lobby_count > prev_lobby_count:
                print(f"  ➕ {lobby_count - prev_lobby_count} lobby(ies) joined queue")
            elif lobby_count < prev_lobby_count:
                print(f"  ➖ {prev_lobby_count - lobby_count} lobby(ies) left queue")
            
            if match_count > prev_match_count:
                print(f"  🎮 {match_count - prev_match_count} match(es) created!")
                # Show match details
                for k in match_keys:
                    if b':data' in k:
                        match_id = k.decode().split(':')[2]
                        data = r.get(k)
                        if data:
                            match_data = json.loads(data)
                            notified_key = f"matchmaking:match:{match_id}:notified"
                            accepted_key = f"matchmaking:match:{match_id}:accepted"
                            
                            notified_count = r.scard(notified_key)
                            accepted_count = r.scard(accepted_key)
                            
                            print(f"    Match {match_id[:8]}... - Accepted: {accepted_count}/{notified_count}")
            
            prev_lobby_count = lobby_count
            prev_match_count = match_count
        else:
            # Show inline status
            timestamp = time.strftime("%H:%M:%S")
            sys.stdout.write(f"[{timestamp}] Lobbies: {lobby_count} | Matches: {match_count}" + " " * 30 + "\r")
            sys.stdout.flush()
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")

