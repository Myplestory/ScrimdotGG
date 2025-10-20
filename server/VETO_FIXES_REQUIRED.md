# ⚠️ VETO FLOW - MISSING FUNCTIONALITY

## Critical Issues Preventing Veto Flow

### 1. **9 Missing Broadcast Handlers** ❌❌❌
**File:** `server/realtime/consumers.py`

The `RealtimeConsumer` is missing these handlers that exist in original `consumers.py`:

```python
async def server_veto_started(self, event):  # Line 1112 in original
async def server_vetoed(self, event):  # Line 1126 in original  
async def server_veto_complete(self, event):  # Line 1142 in original
async def server_veto_timeout(self, event):  # Line 1169 in original
async def map_vetoed(self, event):  # Line 1203 in original
async def map_veto_started(self, event):  # Line 1219 in original
async def map_veto_timeout(self, event):  # Line 1233 in original
async def side_selection_timeout(self, event):  # Line 1250 in original
```

**Current Error:**
```
ValueError: No handler for message type server_veto_started
→ All 10 WebSocket connections DISCONNECT
```

---

### 2. **Incomplete match_data Handler** ❌❌
**File:** `server/realtime/consumers.py` line 264

**Original (line 1084-1096):**
```python
async def match_data(self, event):
    # Add player to match group for veto updates
    match_id = event.get('match_id')
    if match_id:
        await self.channel_layer.group_add(
            f"match_{match_id}",
            self.channel_name
        )  # ← CRITICAL: Needed for veto broadcasts!
    
    await self.send(...)
```

**Refactored (line 264-266):**
```python
async def match_data(self, event):
    await self.send(text_data=json.dumps({'event': 'match_data', 'payload': event}))
    # ❌ MISSING: group_add call!
```

**Impact:** Players never join `match_{match_id}` group → veto broadcasts don't reach them

---

### 3. **Missing Acceptance Progress Broadcasts** ❌
**File:** `server/realtime/handlers/match_handler.py` line 19-46

**Original (line 716-733):**
```python
# When ANY player accepts, broadcast to ALL lobby groups
for lobby_id in match_lobbies:
    await self.channel_layer.group_send(
        f"lobby_{lobby_id}",
        {
            'type': 'player_accepted',
            'accepted_count': accepted_count,  # 3/10, 4/10, etc.
            'total_players': total_players,
            'timeout_seconds': timeout_seconds
        }
    )
```

**Refactored:**
```python
# Only sends to accepting player
await self.send_event('player_accepted', result)
# ❌ Other players never see acceptance count increase!
```

**Impact:** Other players stuck at "0/10 accepted", no real-time feedback

---

### 4. **Missing match_ready Broadcast** ❌
**File:** `server/realtime/handlers/match_handler.py`

**Original (line 706-713):**
```python
if result.get('match_confirmed'):
    # Broadcast to ALL lobby groups
    for lobby_id in match_lobbies:
        await self.channel_layer.group_send(
            f"lobby_{lobby_id}",
            {'type': 'match_ready', 'message': 'Match is ready!'}
        )
```

**Refactored:**
```python
# ❌ MISSING COMPLETELY
```

**Impact:** Lobbies never notified when match is ready

---

## Quick Fix Summary

| Priority | Fix | File | Lines |
|----------|-----|------|-------|
| **CRITICAL** | Add 9 veto broadcast handlers | `realtime/consumers.py` | Add after line 270 |
| **CRITICAL** | Fix match_data to add player to match group | `realtime/consumers.py` | Modify line 264-266 |
| **HIGH** | Add acceptance broadcasting to all lobbies | `realtime/handlers/match_handler.py` | Modify line 33-40 |
| **HIGH** | Add match_ready broadcast | `realtime/handlers/match_handler.py` | Add in line 33-40 |

---

## Expected Flow After Fixes

```
✅ Player accepts → ALL players see "3/10 accepted"
✅ 10/10 players accept → "Match is ready!" notification
✅ match_data → Players added to match_{match_id} group
✅ server_veto_started → Client shows veto UI
✅ Server veto updates → Real-time progress
✅ Map veto → Real-time progress  
✅ Side selection → Match ready
```

---

## Current Flow (Broken)

```
❌ Player accepts → Only accepting player notified
❌ 10/10 accept → NO notification
❌ match_data → NOT added to match group
❌ server_veto_started → ValueError, WebSocket DISCONNECTS
❌ Flow STOPS
```

---

**See:** `VETO_FLOW_ISSUES_ANALYSIS.md` for complete technical details.


