# 🔍 Match Acceptance & Veto Flow Issues - Complete Analysis

## Current Problem

The client UI shows "Loading..." with empty teams and no veto information. WebSocket connections are disconnecting due to missing broadcast handlers, preventing the veto phase from working.

---

## Root Cause Analysis

Comparing the refactored code with the original monolithic `consumers.py` reveals **multiple missing critical pieces** in the match acceptance and veto flow.

---

## Issue 1: Missing Broadcast Handlers in RealtimeConsumer ❌

### Problem
The `RealtimeConsumer` is missing **9 critical broadcast handlers** that exist in the original consumer.

### Original Consumer Has (lines 1080-1275):
```python
# server/matchmaking/consumers.py

async def match_data(self, event):
    """Match data broadcast - adds player to match group"""
    # ✅ CRITICAL: Adds player to match_{match_id} group
    match_id = event.get('match_id')
    if match_id:
        await self.channel_layer.group_add(
            f"match_{match_id}",
            self.channel_name
        )
    await self.send(text_data=json.dumps({
        'event': 'match_data',
        'payload': event.get('payload', {})
    }))

async def server_veto_started(self, event):
    """Server veto phase has begun."""
    await self.send(text_data=json.dumps({
        'event': 'server_veto_started',
        'payload': {
            'match_id': event.get('match_id'),
            'current_turn': event.get('current_turn'),
            'available_servers': event.get('available_servers', []),
            'deadline': event.get('deadline')
        }
    }))

async def server_vetoed(self, event):
    """A server was vetoed."""
    await self.send(text_data=json.dumps({
        'event': 'server_veto_update',
        'payload': {
            'match_id': event.get('match_id'),
            'server_name': event.get('server_name'),
            'vetoed_by': event.get('vetoed_by'),
            'next_turn': event.get('next_turn'),
            'remaining_servers': event.get('remaining_servers', []),
            'deadline': event.get('deadline')
        }
    }))

async def server_veto_complete(self, event):
    """Server veto phase completed - transition to map veto."""
    await self.send(text_data=json.dumps({
        'event': 'server_veto_complete',
        'payload': {
            'match_id': event.get('match_id'),
            'final_server': event.get('final_server'),
            'current_turn': event.get('current_turn'),
            'available_maps': event.get('available_maps', []),
            'veto_deadline': event.get('veto_deadline')
        }
    }))
    
    # Also send map_veto_started if applicable
    if event.get('map_veto_started', False):
        await self.send(text_data=json.dumps({
            'event': 'map_veto_started',
            'payload': {
                'match_id': event.get('match_id'),
                'current_turn': event.get('current_turn'),
                'available_maps': event.get('available_maps', []),
                'deadline': event.get('veto_deadline')
            }
        }))

async def server_veto_timeout(self, event):
    """Server veto timeout - auto-veto occurred."""
    await self.send(text_data=json.dumps({
        'event': 'server_veto_timeout',
        'payload': {
            'match_id': event.get('match_id'),
            'timed_out_team': event.get('timed_out_team'),
            'auto_vetoed_server': event.get('auto_vetoed_server'),
            'next_turn': event.get('next_turn'),
            'remaining_servers': event.get('remaining_servers', []),
            'deadline': event.get('deadline')
        }
    }))

async def map_vetoed(self, event):
    """A map was vetoed."""
    await self.send(text_data=json.dumps({
        'event': 'map_vetoed',
        'payload': {
            'match_id': event.get('match_id'),
            'map': event.get('map_name'),
            'vetoed_by': event.get('vetoed_by'),
            'next_turn': event.get('next_turn'),
            'remaining_maps': event.get('remaining_maps', []),
            'deadline': event.get('deadline')
        }
    }))

async def map_veto_started(self, event):
    """Map veto phase has begun."""
    await self.send(text_data=json.dumps({
        'event': 'map_veto_started',
        'payload': {
            'match_id': event.get('match_id'),
            'current_turn': event.get('current_turn'),
            'available_maps': event.get('available_maps', []),
            'deadline': event.get('deadline')
        }
    }))

async def map_veto_timeout(self, event):
    """Map veto timeout - auto-veto occurred."""
    await self.send(text_data=json.dumps({
        'event': 'map_veto_timeout',
        'payload': {
            'match_id': event.get('match_id'),
            'auto_vetoed_map': event.get('auto_vetoed_map'),
            'veto_complete': event.get('veto_complete', False),
            'next_turn': event.get('next_turn'),
            'remaining_maps': event.get('remaining_maps', []),
            'deadline': event.get('deadline'),
            'final_map': event.get('final_map')
        }
    }))

async def side_selection_timeout(self, event):
    """Side selection timeout - auto-select occurred."""
    await self.send(text_data=json.dumps({
        'event': 'side_selection_timeout',
        'payload': {
            'match_id': event.get('match_id'),
            'auto_selected_side': event.get('auto_selected_side'),
            'side_selection_complete': event.get('side_selection_complete', False),
            'match_ready': event.get('match_ready', False)
        }
    }))
```

### Refactored Consumer Has (lines 264-266):
```python
# server/realtime/consumers.py

async def match_data(self, event):
    """Handle match_data response"""
    await self.send(text_data=json.dumps({'event': 'match_data', 'payload': event}))
    # ❌ MISSING: No group_add for match_{match_id} group!
```

**Status:**
- ✅ `match_data` handler EXISTS but is **incomplete** (missing group_add)
- ❌ `server_veto_started` - **MISSING** (causing WebSocket disconnect)
- ❌ `server_vetoed` - **MISSING**
- ❌ `server_veto_complete` - **MISSING**
- ❌ `server_veto_timeout` - **MISSING**
- ❌ `map_vetoed` - **MISSING**
- ❌ `map_veto_started` - **MISSING**
- ❌ `map_veto_timeout` - **MISSING**
- ❌ `side_selection_timeout` - **MISSING**

### Impact
1. **Immediate Error**: `ValueError: No handler for message type server_veto_started`
2. **WebSocket Disconnect**: All 10 players disconnect when veto starts
3. **No Veto Updates**: Even if players stay connected, they won't receive veto progress
4. **No Match Group**: Players are never added to `match_{match_id}` group, so broadcasts fail

---

## Issue 2: Missing Acceptance Progress Broadcasting ❌

### Problem
When a player accepts a match, OTHER players in the match don't get notified of the acceptance count.

### Original Consumer Logic (lines 716-734):
```python
# server/matchmaking/consumers.py - accept_match handler

if result.get('match_confirmed'):
    # All players accepted - match is ready
    match_lobbies = result.get('match_lobbies', [])
    for lobby_id in match_lobbies:
        await self.channel_layer.group_send(
            f"lobby_{lobby_id}",
            {
                'type': 'player_accepted',  # ← Broadcast to lobby groups
                'accepted_count': accepted_count,
                'total_players': total_players,
                'timeout_seconds': timeout_seconds
            }
        )
else:
    # Send acceptance update to ALL lobbies in the match
    match_lobbies = result.get('match_lobbies', [])
    accepted_count = result.get('accepted_count')
    total_players = result.get('total_players')
    timeout_seconds = result.get('timeout_seconds')
    
    for lobby_id in match_lobbies:
        await self.channel_layer.group_send(
            f"lobby_{lobby_id}",
            {
                'type': 'player_accepted',  # ← Broadcast to ALL lobbies
                'accepted_count': accepted_count,
                'total_players': total_players,
                'timeout_seconds': timeout_seconds
            }
        )
```

### Refactored Handler (lines 33-40):
```python
# server/realtime/handlers/match_handler.py - handle_accept_match

result = await MatchConfirmationManager.accept_match(match_id, self.puuid)

if result['status'] == 'success':
    if result.get('all_accepted'):
        actual_match_id = result.get('match_instance_id')
        if actual_match_id:
            await self.consumer.join_match_group(actual_match_id)
    
    await self.send_event('player_accepted', result)  # ❌ Only to accepting player!
```

### Impact
- ❌ Only the accepting player sees their own acceptance
- ❌ Other players in the match don't see acceptance count increase (stuck at "0/10 accepted")
- ❌ No real-time feedback for match filling up

---

## Issue 3: Incomplete match_data Handler ❌

### Problem
The refactored `match_data` handler doesn't add players to the `match_{match_id}` group.

### Why This Matters
After all players accept, the server broadcasts events to `f"match_{match_id}"` group for veto updates. But players were never added to this group, so they never receive the updates.

### Original Logic (lines 1084-1091):
```python
# server/matchmaking/consumers.py

async def match_data(self, event):
    # Add player to match group for veto updates
    match_id = event.get('match_id')
    if match_id:
        await self.channel_layer.group_add(
            f"match_{match_id}",
            self.channel_name
        )
        logger.info(f"Added player {self.puuid} to match group match_{match_id}")
    
    await self.send(text_data=json.dumps({
        'event': 'match_data',
        'payload': event.get('payload', {})
    }))
```

### Refactored Logic (line 264-266):
```python
# server/realtime/consumers.py

async def match_data(self, event):
    """Handle match_data response"""
    await self.send(text_data=json.dumps({'event': 'match_data', 'payload': event}))
    # ❌ MISSING: group_add call!
```

### Impact
- ❌ Players never join `match_{match_id}` group
- ❌ Veto broadcasts to `match_{match_id}` group don't reach players
- ❌ Players see "Loading..." forever because they never receive veto_started events

---

## Issue 4: Missing match_ready Broadcast ❌

### Original Consumer (lines 706-713):
```python
# server/matchmaking/consumers.py - accept_match handler

if result.get('match_confirmed'):
    # All players accepted - match is ready
    match_lobbies = result.get('match_lobbies', [])
    for lobby_id in match_lobbies:
        await self.channel_layer.group_send(
            f"lobby_{lobby_id}",
            {
                'type': 'match_ready',
                'message': 'Match is ready!',
                'match_id': str(result.get('match_id'))
            }
        )
```

### Refactored Handler
```python
# server/realtime/handlers/match_handler.py

# ❌ MISSING: No match_ready broadcast to lobbies
```

### Impact
- ❌ Lobbies don't get notified when match is ready
- ❌ No transition signal for lobby UI to match UI

---

## Complete Flow Comparison

### ✅ ORIGINAL FLOW (Working)
```
1. Player accepts match
   ↓
2. Consumer calls MatchConfirmationManager.accept_match()
   ↓
3. Consumer broadcasts 'player_accepted' to ALL lobby groups
   → Other players see "3/10 accepted", "4/10 accepted", etc.
   ↓
4. All 10 players accept
   ↓
5. Consumer broadcasts 'match_ready' to ALL lobby groups
   ↓
6. MatchConfirmationManager.transition_to_match() executes
   ↓
7. Broadcasts 'match_confirmed' to each player_{puuid} group
   ↓
8. Broadcasts 'match_data' to each player_{puuid} group
   → match_data handler adds player to match_{match_id} group ✅
   → Player receives match data (teams, captains, etc.)
   ↓
9. Broadcasts 'server_veto_started' to each player_{puuid} group
   → server_veto_started handler forwards to client ✅
   → Client shows veto UI with available servers
   ↓
10. Players veto servers
    ↓
11. Broadcasts 'server_vetoed' to match_{match_id} group
    → server_vetoed handler forwards to client ✅
    → Client updates veto progress
    ↓
12. Server veto complete
    ↓
13. Broadcasts 'server_veto_complete' + 'map_veto_started' to match_{match_id} group
    → Handlers forward to client ✅
    → Client transitions to map veto UI
```

### ❌ REFACTORED FLOW (Broken)
```
1. Player accepts match
   ↓
2. MatchHandler calls MatchConfirmationManager.accept_match()
   ↓
3. ❌ NO BROADCAST - only sending to accepting player
   → Other players NEVER see acceptance count increase
   ↓
4. All 10 players accept (each only sees their own acceptance)
   ↓
5. ❌ NO 'match_ready' BROADCAST to lobby groups
   ↓
6. MatchConfirmationManager.transition_to_match() executes
   ↓
7. Broadcasts 'match_confirmed' to each player_{puuid} group ✅
   ↓
8. Broadcasts 'match_data' to each player_{puuid} group
   → match_data handler forwards event ✅
   → ❌ BUT DOESN'T add player to match_{match_id} group!
   → Player receives match data but UI may be incomplete
   ↓
9. Broadcasts 'server_veto_started' to each player_{puuid} group
   → ❌ NO HANDLER - ValueError: No handler for message type server_veto_started
   → WebSocket DISCONNECTS ❌
   ↓
10. FLOW STOPS - All players disconnected
```

---

## Summary of Missing Pieces

| Component | Original | Refactored | Status |
|-----------|----------|------------|--------|
| **Broadcast Handlers** |
| `server_veto_started` | ✅ Line 1112 | ❌ Missing | **CRITICAL** |
| `server_vetoed` | ✅ Line 1126 | ❌ Missing | **CRITICAL** |
| `server_veto_complete` | ✅ Line 1142 | ❌ Missing | **CRITICAL** |
| `server_veto_timeout` | ✅ Line 1169 | ❌ Missing | **HIGH** |
| `map_vetoed` | ✅ Line 1203 | ❌ Missing | **CRITICAL** |
| `map_veto_started` | ✅ Line 1219 | ❌ Missing | **CRITICAL** |
| `map_veto_timeout` | ✅ Line 1233 | ❌ Missing | **HIGH** |
| `side_selection_timeout` | ✅ Line 1250 | ❌ Missing | **MEDIUM** |
| `match_data` (group_add) | ✅ Line 1084-1091 | ❌ Incomplete | **CRITICAL** |
| **Acceptance Broadcasting** |
| Broadcast to lobby groups | ✅ Line 724-733 | ❌ Missing | **HIGH** |
| `match_ready` broadcast | ✅ Line 706-713 | ❌ Missing | **HIGH** |

---

## Required Fixes

### Fix 1: Add Missing Broadcast Handlers to RealtimeConsumer

**File:** `server/realtime/consumers.py`

**Add 9 handlers:**
1. `async def server_veto_started(self, event)`
2. `async def server_vetoed(self, event)`
3. `async def server_veto_complete(self, event)`
4. `async def server_veto_timeout(self, event)`
5. `async def map_vetoed(self, event)`
6. `async def map_veto_started(self, event)`
7. `async def map_veto_timeout(self, event)`
8. `async def side_selection_timeout(self, event)`

**Fix match_data handler:**
9. Modify `async def match_data(self, event)` to add player to match group

---

### Fix 2: Add Acceptance Broadcasting to MatchHandler

**File:** `server/realtime/handlers/match_handler.py`

**Modify `handle_accept_match`** to broadcast to ALL lobby groups involved:

```python
async def handle_accept_match(self, data):
    # ... existing code ...
    result = await MatchConfirmationManager.accept_match(match_id, self.puuid)
    
    if result['status'] == 'success':
        # Get all lobbies involved in this match
        match_lobbies = result.get('match_lobbies', [])
        accepted_count = result.get('accepted_count')
        total_players = result.get('total_players')
        timeout_seconds = result.get('timeout_seconds')
        
        if result.get('match_confirmed'):
            # All players accepted - broadcast match_ready
            for lobby_id in match_lobbies:
                await self.channel_layer.group_send(
                    f"lobby_{lobby_id}",
                    {
                        'type': 'match_ready',
                        'message': 'Match is ready!',
                        'match_id': str(result.get('match_id'))
                    }
                )
        else:
            # Broadcast acceptance progress to ALL lobbies
            for lobby_id in match_lobbies:
                await self.channel_layer.group_send(
                    f"lobby_{lobby_id}",
                    {
                        'type': 'player_accepted',
                        'accepted_count': accepted_count,
                        'total_players': total_players,
                        'timeout_seconds': timeout_seconds
                    }
                )
        
        # Send acknowledgment to accepting player
        await self.send_event('match_accepted', result)
```

---

## Validation Checklist

After fixes are applied, verify:

- [ ] WebSocket stays connected after all players accept
- [ ] Acceptance counter updates for all players ("1/10", "2/10", etc.)
- [ ] "Match is ready!" notification appears when 10/10 accept
- [ ] Match data loads (team assignments, captains visible)
- [ ] Server veto UI appears with available servers
- [ ] Server veto progress updates in real-time
- [ ] Map veto UI appears after server selection
- [ ] Map veto progress updates in real-time
- [ ] Side selection UI appears after map selection
- [ ] Match transitions to "ready" state after complete veto flow

---

**Priority:** **CRITICAL** - This breaks the entire match flow after queue.

**Effort:** **Medium** - Need to add 9 broadcast handlers + modify 2 existing handlers.

**Risk:** **Low** - Just restoring original functionality that was accidentally removed.


