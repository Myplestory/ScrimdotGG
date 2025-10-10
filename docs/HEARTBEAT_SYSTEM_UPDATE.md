# Heartbeat System Update

## Overview
Updated the Valorant status heartbeat system to run throughout the entire user session until they enter an active game match, rather than stopping at authentication.

## Problem
Previously, the heartbeat system would stop as soon as the user authenticated. This meant:
- ❌ Status wasn't monitored while user was in lobby
- ❌ Status wasn't monitored while user was in queue
- ❌ If Valorant crashed during lobby/queue, no status update would be sent
- ❌ Heartbeat would unnecessarily stop/restart if user didn't enter a match

## Solution
Heartbeat now runs continuously until the user is actually **in an active game match**:
- ✅ Continues monitoring during authentication, lobby, and queue phases
- ✅ Only stops when user enters an active match (playing the game)
- ✅ Automatically restarts when match ends and user returns to lobby
- ✅ Better resource management (only stops when monitoring isn't needed)

---

## Changes Made

### 1. Client State Tracking
Added `in_game` boolean to `client_states` dictionary:

```python
client_states[client_id] = {
    'ws': ws,
    'authenticated': False,  # Tracks if user logged in
    'in_game': False,        # NEW: Tracks if user is in active match
    'puuid': None,
    'match_id': None
}
```

### 2. Updated Heartbeat Docstrings

**Before:**
```python
"""
Start the Valorant status heartbeat monitor.
Only runs when users are not authenticated.
"""
```

**After:**
```python
"""
Start the Valorant status heartbeat monitor.
Runs when users are not in an active game (includes login, lobby, queue).
"""
```

### 3. Updated `handle_authenticate()`
Removed the logic that stopped heartbeat after authentication:

```python
# OLD (removed):
if all_authenticated:
    await stop_valorant_heartbeat()

# NEW:
# NOTE: Heartbeat continues running even after auth
# It only stops when user enters an active game
print("[AUTH] User authenticated, heartbeat continues until in-game")
```

### 4. Updated `handle_connected()`
Changed check from `authenticated` to `in_game`:

```python
# OLD:
if not client_states[client_id].get('authenticated', False):
    await start_valorant_heartbeat()

# NEW:
if not client_states[client_id].get('in_game', False):
    await start_valorant_heartbeat()
```

### 5. Updated Disconnect Handler
Changed to check `in_game` status instead of `authenticated`:

```python
# OLD:
was_authenticated = client_states[client_id].get('authenticated', False)
if was_authenticated:
    unauthenticated_count = sum(...)

# NEW:
was_in_game = client_states[client_id].get('in_game', False)
if was_in_game:
    clients_not_in_game = sum(...)
    if clients_not_in_game > 0:
        await start_valorant_heartbeat()
```

### 6. Added Match Lifecycle Handlers

#### `handle_match_started()`
```python
async def handle_match_started(payload: dict, client_id: int, ws):
    """
    Handle match start event from Django server.
    Sets user as in-game and stops heartbeat.
    """
    client_states[client_id]['in_game'] = True
    
    # Stop heartbeat if all clients are now in-game
    all_in_game = all(
        state.get('in_game', False) 
        for state in client_states.values()
    )
    if all_in_game:
        await stop_valorant_heartbeat()
```

#### `handle_match_ended()`
```python
async def handle_match_ended(payload: dict, client_id: int, ws):
    """
    Handle match end event from Django server or client.
    Sets user as not in-game and restarts heartbeat.
    """
    client_states[client_id]['in_game'] = False
    
    # Restart heartbeat since user is back to lobby
    await start_valorant_heartbeat()
```

---

## Heartbeat Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Session Lifecycle                 │
└─────────────────────────────────────────────────────────────┘

1. Client Connects
   ├─ Heartbeat: START ✅
   └─ Status: Checking Valorant...

2. User Authenticates
   ├─ Heartbeat: CONTINUES ✅
   └─ Status: Authenticated, in lobby

3. User Creates/Joins Lobby
   ├─ Heartbeat: CONTINUES ✅
   └─ Status: In lobby

4. User Queues for Match
   ├─ Heartbeat: CONTINUES ✅
   └─ Status: In queue

5. Match Found → User Accepts
   ├─ Heartbeat: CONTINUES ✅
   └─ Status: Match accepted, waiting for others

6. Match Starts (All Players Accepted)
   ├─ Heartbeat: STOP 🛑
   └─ Status: In-game (playing match)

7. Match Ends
   ├─ Heartbeat: RESTART ✅
   └─ Status: Back to lobby

8. Client Disconnects
   ├─ Heartbeat: Check remaining clients
   └─ If any client not in-game: Keep running
```

---

## When Heartbeat Runs

| User State | Heartbeat Running? | Reason |
|------------|-------------------|---------|
| Not connected | ❌ No | No client to monitor |
| Connected, not authenticated | ✅ Yes | Need to monitor Valorant status for login |
| Authenticated, in lobby | ✅ Yes | Monitor for Valorant crashes |
| In queue | ✅ Yes | Monitor for Valorant crashes |
| Match found, accepting | ✅ Yes | Monitor for Valorant crashes |
| **In active match** | ❌ No | User is playing, no need to check status |
| Match ended, back to lobby | ✅ Yes | Resume monitoring |

---

## Benefits

### Performance
- ✅ Only stops monitoring when absolutely unnecessary (during active gameplay)
- ✅ Reduces unnecessary start/stop cycles
- ✅ Continues monitoring during critical phases (lobby, queue)

### User Experience
- ✅ Detects if Valorant crashes while in lobby/queue
- ✅ Real-time status updates throughout the session
- ✅ Automatic recovery when match ends

### Reliability
- ✅ Ensures status is always up-to-date when user isn't playing
- ✅ Handles edge cases (Valorant crash, disconnect during queue)
- ✅ Proper cleanup when clients disconnect

---

## Integration with Django Server

The Django server should emit these events:

1. **`match_started`** - When all players accept and match begins
   ```json
   {
     "event": "match_started",
     "payload": {
       "match_id": "abc123",
       "server_ip": "1.2.3.4:7777"
     }
   }
   ```

2. **`match_ended`** - When match finishes
   ```json
   {
     "event": "match_ended",
     "payload": {
       "match_id": "abc123",
       "result": "win",
       "elo_change": +15
     }
   }
   ```

The local client backend will:
- Set `in_game = True` when receiving `match_started`
- Set `in_game = False` when receiving `match_ended`
- Manage heartbeat lifecycle automatically

---

## Testing

### Test 1: Authentication Phase
1. Launch client (not authenticated)
2. **Expected:** Heartbeat running (status updates every 5s)
3. Authenticate
4. **Expected:** Heartbeat still running

### Test 2: Lobby/Queue Phase
1. Authenticate and enter lobby
2. **Expected:** Heartbeat still running
3. Queue for match
4. **Expected:** Heartbeat still running

### Test 3: Match Phase
1. Match found and accepted
2. Wait for `match_started` event
3. **Expected:** Heartbeat stops (logs show "Stopping Valorant status monitor (user in-game)...")

### Test 4: Post-Match Phase
1. Match ends (`match_ended` event)
2. **Expected:** Heartbeat restarts (logs show "Starting Valorant status monitor...")

### Test 5: Valorant Crash During Queue
1. Authenticate and queue for match
2. Close Valorant while queued
3. **Expected:** Status updates to "Valorant Not Running" within 5-10 seconds

---

## Future Considerations

- Consider pausing heartbeat during agent select/pre-game (if needed)
- May want different heartbeat intervals for different phases
- Could add "resuming from match" detection if user was disconnected during match

---

**Implementation Date:** October 10, 2025  
**Status:** ✅ Completed - Ready for Testing

