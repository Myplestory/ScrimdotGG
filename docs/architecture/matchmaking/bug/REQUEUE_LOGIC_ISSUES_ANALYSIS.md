# Requeue Logic Issues - Root Cause Analysis

## 🔍 **Problems Identified:**

### **Issue 1: Match Not Detected as Expired**

**Evidence from Celery Worker logs (Line 982):**
```
Cleanup completed: 0 expired matches handled out of 1 processed
```

The cleanup task **finds** 1 match confirmation but marks it as **NOT expired** even though 30+ seconds have passed.

**Timeline:**
- **19:23:54**: Match proposed (initiated_at timestamp set)
- **19:24:07**: Last acceptance (9/10 accepted, 17s remaining)
- **19:24:24**: 30 seconds elapsed → Match should be expired
- **19:24:39**: Cleanup runs (19:24:39 in Celery Beat logs)
- **19:24:54**: Cleanup runs (line 862 in Celery logs) → Says "0 expired matches"

**Issue:** The `is_match_expired()` check is returning `False` even though the match is expired.

**Possible Causes:**
1. **Timezone mismatch**: `initiated_at` and `now` might be in different timezones
2. **Time calculation error**: The time diff calculation might be wrong
3. **ACCEPTANCE_TIMEOUT constant**: Might be set to a very large value
4. **initiated_at format**: The datetime parsing might be failing silently

---

### **Issue 2: Wrong Requeue Logic**

**Current Logic (Line 732 in `match_confirmation.py`):**
```python
for lobby_id in lobbies:
    # Requeue ALL lobbies in the match
```

This requeues **ALL lobbies** that were in the match, regardless of whether their players accepted or not.

**Correct Logic Should Be:**
Only requeue lobbies where **ALL players in that lobby accepted**.

**Example Scenario:**
- **Lobby A** (2 players): Both accepted ✅ → Should requeue
- **Lobby B** (1 player): Did not accept ❌ → Should NOT requeue  
- **Lobby C** (3 players): 2 accepted, 1 didn't ❌ → Should NOT requeue
- **Lobby D** (4 players): All accepted ✅ → Should requeue

**Current behavior:** Requeues A, B, C, D (all 4 lobbies)
**Expected behavior:** Requeues only A and D (lobbies where 100% of players accepted)

---

## 🎯 **Root Causes:**

### **Root Cause #1: `is_match_expired()` Always Returns False**

**Location:** `server/matchmaking/match_confirmation.py:646-688`

**The Check:**
```python
initiated_at = match_info.get('initiated_at')

if initiated_at:
    from datetime import datetime
    initiated_time = datetime.fromisoformat(initiated_at.replace('Z', '+00:00'))
    now = timezone.now()
    
    # Check if more than ACCEPTANCE_TIMEOUT seconds have passed
    time_diff = (now - initiated_time).total_seconds()
    return time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT
```

**Potential Issues:**
1. **Timezone-naive vs timezone-aware datetimes**
2. **`ACCEPTANCE_TIMEOUT` value** (should be 30, but might be something else)
3. **`initiated_at` format** (might not parse correctly)

---

### **Root Cause #2: Requeue Logic Doesn't Check Per-Lobby Acceptance**

**Location:** `server/matchmaking/match_confirmation.py:690-782`

**Current Flow:**
1. Get **all lobbies** in match (line 712)
2. For each lobby, requeue it (line 732)
3. **No check** if all players in that lobby accepted

**Missing Logic:**
Need to check:
- Get all players in each lobby
- Check if all those players are in the `accepting_players` list
- Only requeue if 100% of lobby players accepted

---

## 📊 **Data Flow Analysis:**

### **Match Confirmation Data Structure:**
```
match_confirmation:{UUID}:data → {
    initiated_at: "2025-10-12T19:23:54.123456+00:00",
    match_id: "...",
    full_lobby_data: {
        "lobby_id_1": { players: [...] },
        "lobby_id_2": { players: [...] },
        ...
    }
}

match_confirmation:{UUID}:notified → SET of player PUUIDs (all 10 players)
match_confirmation:{UUID}:accepted → SET of player PUUIDs (9 players who accepted)
match_confirmation:{UUID}:lobbies → SET of lobby IDs (all 10 lobbies)
```

### **Current Requeue Flow:**
1. `handle_expired_match()` calls `get_match_lobbies()` → Returns **all 10 lobbies**
2. Iterates through all 10 lobbies
3. Requeues all 10 lobbies

### **Correct Requeue Flow Should Be:**
1. `handle_expired_match()` gets **all lobbies** and **accepting players**
2. For each lobby:
   a. Get all players in that lobby from `full_lobby_data`
   b. Check if **all** those players are in `accepting_players`
   c. Only requeue if **100% acceptance**
3. Result: Requeue only 9 lobbies (8 bots + 1 user), NOT the bot that didn't accept

---

## 🔧 **Required Fixes:**

### **Fix #1: Debug `is_match_expired()` Check**

**Steps:**
1. Add logging to see actual values:
   ```python
   logger.info(f"initiated_at: {initiated_at}")
   logger.info(f"initiated_time: {initiated_time}")
   logger.info(f"now: {now}")
   logger.info(f"time_diff: {time_diff}")
   logger.info(f"ACCEPTANCE_TIMEOUT: {MatchConfirmationManager.ACCEPTANCE_TIMEOUT}")
   logger.info(f"expired: {time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT}")
   ```
2. Run test and check Celery Worker logs
3. Identify which value is causing the issue

### **Fix #2: Implement Per-Lobby Acceptance Check**

**Pseudocode:**
```python
# Get all lobbies and accepting players
lobbies = await MatchConfirmationManager.get_match_lobbies(match_id)
accepting_players = await MatchConfirmationManager.get_accepting_players(match_id)

# Get full lobby data
match_data = await MatchConfirmationManager.get_match_data(match_id)
full_lobby_data = match_data.get('full_lobby_data', {})

# Determine which lobbies to requeue
lobbies_to_requeue = []

for lobby_id in lobbies:
    lobby_data = full_lobby_data.get(lobby_id)
    if not lobby_data:
        continue
    
    # Get all players in this lobby
    lobby_players = lobby_data.get('players', [])
    lobby_player_puuids = [p['puuid'] for p in lobby_players]
    
    # Check if ALL players in this lobby accepted
    all_accepted = all(puuid in accepting_players for puuid in lobby_player_puuids)
    
    if all_accepted:
        lobbies_to_requeue.append(lobby_id)
        logger.info(f"   Lobby {lobby_id[:8]}... - ALL {len(lobby_player_puuids)} players accepted ✅")
    else:
        accepting_count = sum(1 for puuid in lobby_player_puuids if puuid in accepting_players)
        logger.info(f"   Lobby {lobby_id[:8]}... - Only {accepting_count}/{len(lobby_player_puuids)} players accepted ❌")

# Only requeue the lobbies where all players accepted
logger.info(f"🔄 Requeuing {len(lobbies_to_requeue)}/{len(lobbies)} lobbies (only those with 100% acceptance)")

for lobby_id in lobbies_to_requeue:
    # ... existing requeue logic ...
```

---

## 🧪 **Testing Expected Behavior:**

### **Scenario: 9/10 Players Accept**

**Setup:**
- 10 solo lobbies (1 player each)
- 9 players accept (8 bots + 1 user)
- 1 player doesn't accept (queuebot-8)

**Expected Cleanup Behavior:**
1. Match detected as expired (30s elapsed)
2. Get accepting players: 9 PUUIDs
3. Check each lobby:
   - Lobbies 1-9: 1 player, that player accepted ✅ → Requeue
   - Lobby 10: 1 player, that player didn't accept ❌ → Don't requeue
4. Result: 9 lobbies requeued, 1 lobby not requeued
5. Next matchmaking cycle: 9 lobbies in queue (can't make a match, need 10)

---

## 📝 **Summary:**

**Two critical bugs:**

1. **Match expiration not detected**: The `is_match_expired()` check is failing, so cleanup doesn't run
   - **Impact**: Matches never timeout, lobbies never requeued
   - **Priority**: HIGH - Must fix first

2. **Wrong requeue logic**: All lobbies requeued instead of only those with 100% acceptance
   - **Impact**: Players who didn't accept get requeued (unfair)
   - **Priority**: HIGH - Must fix after #1

**Next Steps:**
1. Add debug logging to `is_match_expired()` to see why it returns False
2. Fix the expiration detection issue
3. Then implement per-lobby acceptance checking for requeue

---

**Status:** ⚠️ **NOT FIXED** - Analysis complete, code changes needed

