# Comprehensive Requeue Issue Analysis

## 🎯 **CRITICAL FINDINGS:**

After thorough code review and log analysis, I've identified **3 major issues** and their root causes.

---

## **Issue #1: Match Expiration Not Detected** 🔴 **CRITICAL**

### **Evidence:**
- **Celery Worker Line 982**: `Cleanup completed: 0 expired matches handled out of 1 processed`
- **Timeline**: Match initiated at 19:23:54, cleanup ran at 19:25:39 (105 seconds later), still not marked as expired

### **Root Cause Analysis:**

#### **The Expiration Check** (`match_confirmation.py:646-688`):
```python
def is_match_expired(match_id: str) -> bool:
    # Get match data
    match_data = redis_conn.get(data_key)
    if not match_data:
        return True  # No data = expired
    
    match_info = json.loads(match_data)
    initiated_at = match_info.get('initiated_at')
    
    if initiated_at:
        initiated_time = datetime.fromisoformat(initiated_at.replace('Z', '+00:00'))
        now = timezone.now()
        time_diff = (now - initiated_time).total_seconds()
        return time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT  # 30 seconds
    
    return True  # No timestamp = expired
```

#### **The initiated_at Value** (`match_confirmation.py:127`):
```python
match_data['initiated_at'] = timezone.now().isoformat()
```

### **Potential Causes:**

#### **Theory #1: Timezone Issue** ⭐ **MOST LIKELY**
- `timezone.now()` returns timezone-aware datetime (UTC+00:00 or local timezone)
- `datetime.fromisoformat()` might parse differently than how `isoformat()` formats
- The comparison might be failing due to timezone mismatch

**Example:**
```python
# What's stored:
initiated_at = "2025-10-12T19:23:54.123456+00:00"  # UTC

# What's compared:
initiated_time = datetime.fromisoformat("2025-10-12T19:23:54.123456+00:00")
now = timezone.now()  # Might be different timezone

# If timezones don't match, time_diff might be negative or wrong!
```

#### **Theory #2: Celery Worker OLD Code**
- Celery Worker might have old code from before the `created_at` → `initiated_at` fix
- If worker is looking for `created_at`, it won't find it and returns True (expired)
- But logs show "0 expired" which means it's returning False!
- **Verdict**: Not the issue, worker has new code

#### **Theory #3: Manual Cleanup Interference**
- User ran `cleanup_bots_simple.py` which deleted match confirmation keys
- This might have corrupted the data, causing incomplete matches
- **Verdict**: Likely contributing factor but not root cause

---

## **Issue #2: Wrong Requeue Logic** 🔴 **CRITICAL**

### **Current Behavior:**
All 10 lobbies requeued (including the lobby that didn't accept)

### **Expected Behavior:**
Only requeue lobbies where **ALL players in that lobby accepted**

### **Code Location:** `match_confirmation.py:690-782`

```python
async def handle_expired_match(match_id: str) -> Dict:
    # Get ALL lobbies in match
    lobbies = await MatchConfirmationManager.get_match_lobbies(match_id)  # Returns all 10
    
    # Requeue ALL lobbies (WRONG!)
    for lobby_id in lobbies:
        # ... requeue logic ...
```

### **Missing Logic:**

#### **What's Needed:**
1. Get **accepting_players** list (9 players who accepted)
2. For each lobby:
   - Get all players in that lobby from `full_lobby_data`
   - Check if **ALL** players in lobby are in `accepting_players`
   - Only requeue if 100% of lobby players accepted

#### **Example with Solo Lobbies:**
- **Match**: 10 solo lobbies (1 player each)
- **Accepting**: 9 players (bots 0-7 + user)
- **Not Accepting**: 1 player (queuebot-8)
- **Should Requeue**: 9 lobbies (where the 1 player accepted)
- **Should NOT Requeue**: 1 lobby (queuebot-8's lobby)

#### **Example with Parties:**
- **Lobby A**: 3 players, all 3 accepted ✅ → Requeue
- **Lobby B**: 2 players, both accepted ✅ → Requeue
- **Lobby C**: 2 players, only 1 accepted ❌ → Do NOT requeue
- **Lobby D**: 3 players, 2 accepted 1 didn't ❌ → Do NOT requeue

### **Implementation Pseudocode:**
```python
async def handle_expired_match(match_id: str) -> Dict:
    # Get match data and players
    match_data = await get_match_data(match_id)
    all_lobbies = await get_match_lobbies(match_id)
    accepting_players = await get_accepting_players(match_id)  # Those who clicked accept
    
    full_lobby_data = match_data.get('full_lobby_data', {})
    
    # Determine which lobbies to requeue
    lobbies_to_requeue = []
    
    for lobby_id in all_lobbies:
        lobby_data = full_lobby_data.get(lobby_id)
        if not lobby_data:
            continue
        
        # Get all players in this lobby
        lobby_players = lobby_data.get('players', [])
        lobby_player_puuids = [p['puuid'] for p in lobby_players]
        
        # Check if ALL players in this lobby accepted
        all_players_accepted = all(puuid in accepting_players for puuid in lobby_player_puuids)
        
        if all_players_accepted:
            lobbies_to_requeue.append(lobby_id)
            logger.info(f"✅ Lobby {lobby_id[:8]} - ALL {len(lobby_player_puuids)} players accepted")
        else:
            accepted_in_lobby = sum(1 for p in lobby_player_puuids if p in accepting_players)
            logger.info(f"❌ Lobby {lobby_id[:8]} - Only {accepted_in_lobby}/{len(lobby_player_puuids)} accepted")
    
    # Requeue only qualifying lobbies
    logger.info(f"🔄 Requeuing {len(lobbies_to_requeue)}/{len(all_lobbies)} lobbies")
    
    for lobby_id in lobbies_to_requeue:
        # ... existing requeue code ...
```

---

## **Issue #3: Bot Lobby Destruction on Disconnect** 🟡 **MEDIUM**

### **Evidence:**
**Daphne Logs Lines 985-1011**:
```
[DISCONNECT] User QueueBot2 is solo lobby leader, destroying lobby
[DISCONNECT] User QueueBot3 is solo lobby leader, destroying lobby
... (9 total lobby destructions)
```

### **Problem:**
When bots disconnect (test script exits), the `disconnect()` handler in `consumers.py` calls `_cleanup_user_lobby()` which **destroys solo lobbies** (lines 91-103).

### **Why This Matters:**
Even if the cleanup task runs and requeues lobbies, if bots disconnect **before** the requeue happens, their lobbies are destroyed and can't be requeued.

### **Timeline Problem:**
1. **19:23:54**: Match proposed
2. **19:24:07**: Last acceptance (9/10, 17s remaining)
3. **19:24:24**: 30s timeout should trigger
4. **19:24:30**: User manually Ctrl+C test script
5. **19:24:30**: All 9 bot connections close
6. **19:24:30**: All 9 bot lobbies destroyed  ← **BEFORE cleanup runs!**
7. **19:24:39**: Cleanup task runs ← Lobbies already gone!

### **Why Lobbies Appear in Queue Sometimes:**
Looking at **cleanup script lines 660-667**:
- Line 661: `9 lobbies, 9 players` 
- Line 663: `Found 0 matches`
- Line 666: `0 lobbies, 0 players`

The lobbies disappear between script runs! This is because:
1. Bots are recreated by test script
2. They join queue
3. Matchmaking finds them
4. Cleanup script manually clears them

---

## 🔧 **PRIORITIZED FIX ORDER:**

### **PRIORITY 1: Fix Match Expiration Detection** ⚠️ **MUST FIX FIRST**

**Why First:**
Without this, cleanup will NEVER run automatically, regardless of requeue logic.

**Action Items:**
1. Add debug logging to `is_match_expired()` to see actual values:
   - `initiated_at` string value
   - `initiated_time` parsed datetime
   - `now` current datetime
   - `time_diff` calculated difference
   - `ACCEPTANCE_TIMEOUT` constant value
   - Final boolean result

2. Run test and examine Celery Worker logs

3. Based on logs, identify the exact issue:
   - If `time_diff` is negative → Timezone issue
   - If `time_diff` is correct but boolean is False → Logic error
   - If `initiated_at` is None → Storage issue

**Likely Fix:**
```python
# Ensure both datetimes are timezone-aware and in same timezone
initiated_time = datetime.fromisoformat(initiated_at.replace('Z', '+00:00'))
now = timezone.now()

# Make sure both are aware and in UTC
if initiated_time.tzinfo is None:
    initiated_time = timezone.make_aware(initiated_time)
if now.tzinfo is None:
    now = timezone.make_aware(now)

# Now compare
time_diff = (now - initiated_time).total_seconds()
```

---

### **PRIORITY 2: Implement Per-Lobby Acceptance Check** ⚠️ **FIX AFTER #1**

**Why Second:**
Once cleanup works, we need correct requeue logic to avoid requeueing non-accepting lobbies.

**Implementation:**
Modify `handle_expired_match()` to:
1. Get `accepting_players` set
2. For each lobby, check if all players accepted
3. Only requeue lobbies with 100% acceptance

**Code Change Location:** `match_confirmation.py:717-763`

---

### **PRIORITY 3: Prevent Lobby Destruction During Active Match** ⚠️ **FIX AFTER #1 & #2**

**Why Third:**
This is only needed if natural timeout isn't working. If #1 is fixed, cleanup will run before disconnect.

**Possible Solutions:**

#### **Option A: Check for Active Match Before Destroying**
```python
# In _cleanup_user_lobby() before destroying solo lobby
# Check if lobby is in an active match confirmation
active_match = await check_if_lobby_in_active_match(lobby_id)
if active_match:
    logger.info(f"[DISCONNECT] Lobby {lobby_id} is in active match, not destroying")
    return
```

#### **Option B: Use Redis TTL Instead of Manual Destroy**
- Let lobbies naturally expire via Redis TTL
- Don't manually destroy on disconnect if in match

#### **Option C: Mark Lobby for Deletion, Don't Delete Immediately**
- Set a flag `lobby.pending_deletion = True`
- Cleanup task handles actual deletion after match resolves

**Recommended:** Option A (simplest and most explicit)

---

## 📊 **Data Flow Diagram:**

### **Current Flow (Broken):**
```
1. Match Proposed (10 lobbies)
2. 9 Players Accept, 1 Doesn't
3. 30s Elapses
4. Cleanup Task Runs:
   → is_match_expired() returns FALSE ❌
   → No action taken
5. Test Script Exits (user Ctrl+C)
6. All Bot Connections Close
7. _cleanup_user_lobby() Destroys All 9 Bot Lobbies
8. Result: 0 lobbies in queue, match never timed out properly
```

### **Expected Flow (After Fixes):**
```
1. Match Proposed (10 lobbies)
2. 9 Players Accept, 1 Doesn't
3. 30s Elapses
4. Cleanup Task Runs:
   → is_match_expired() returns TRUE ✅
   → handle_expired_match() called
   → Checks per-lobby acceptance
   → Requeues 9 lobbies (those that accepted)
   → Does NOT requeue queuebot-8's lobby
5. Result: 9 lobbies in queue, queuebot-8 removed
6. Broadcasts match_timeout to all 10 lobbies
7. User client stays in queue (because they accepted)
```

---

## 🧪 **Testing Plan:**

### **Phase 1: Debug Expiration Detection**
1. Add debug logging to `is_match_expired()`
2. Run test with bots
3. Examine Celery Worker logs during cleanup
4. Identify exact issue (timezone, parsing, logic)
5. Apply fix

### **Phase 2: Implement Per-Lobby Acceptance**
1. Modify `handle_expired_match()` to check per-lobby acceptance
2. Add logging for which lobbies qualify for requeue
3. Run test with bots
4. Verify only 9/10 lobbies requeued

### **Phase 3: Add Lobby Protection (If Needed)**
1. Only if natural timeout still fails
2. Add active match check before destroying lobby
3. Test with bots disconnecting mid-match

---

## 📋 **Code Files to Modify:**

### **Priority 1: Expiration Detection**
- **File**: `server/matchmaking/match_confirmation.py`
- **Method**: `is_match_expired()` (lines 646-688)
- **Change**: Add debug logging, fix timezone handling

### **Priority 2: Requeue Logic**
- **File**: `server/matchmaking/match_confirmation.py`
- **Method**: `handle_expired_match()` (lines 690-782)
- **Change**: Add per-lobby acceptance check

### **Priority 3: Lobby Protection (Optional)**
- **File**: `server/matchmaking/consumers.py`
- **Method**: `_cleanup_user_lobby()` (lines 60-103)
- **Change**: Check for active match before destroying

---

## 🔍 **Specific Issues Found:**

### **A. Constants Confirmed Correct:**
- `ACCEPTANCE_TIMEOUT = 30` ✅ (line 30)
- `MATCH_DATA_TTL = 300` ✅ (line 31)

### **B. Timestamp Storage Confirmed:**
- `initiated_at` stored via `timezone.now().isoformat()` ✅ (line 127)
- Should produce: `"2025-10-12T19:23:54.123456+00:00"`

### **C. Cleanup Script Interference:**
- `cleanup_bots_simple.py` clears match confirmations
- This can corrupt ongoing matches
- **Solution**: Don't run cleanup script during active test

### **D. Disconnect Handler:**
- Solo lobbies destroyed on disconnect (line 92-103)
- Happens BEFORE cleanup can requeue
- **Solution**: Either fix expiration timing OR protect lobbies in matches

---

## 🎯 **Next Actions:**

### **IMMEDIATE: Add Debug Logging**
Add to `is_match_expired()` method:
```python
logger.info(f"[EXPIRATION CHECK] Match {match_id[:8]}")
logger.info(f"  initiated_at (string): {initiated_at}")
logger.info(f"  initiated_time (parsed): {initiated_time}")
logger.info(f"  initiated_time.tzinfo: {initiated_time.tzinfo}")
logger.info(f"  now: {now}")
logger.info(f"  now.tzinfo: {now.tzinfo}")
logger.info(f"  time_diff: {time_diff} seconds")
logger.info(f"  ACCEPTANCE_TIMEOUT: {MatchConfirmationManager.ACCEPTANCE_TIMEOUT}")
logger.info(f"  time_diff > ACCEPTANCE_TIMEOUT: {time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT}")
logger.info(f"  RESULT: {'EXPIRED' if time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT else 'NOT EXPIRED'}")
```

This will reveal the exact issue.

---

## 📝 **Summary:**

**3 Critical Issues:**
1. ✅ **Identified**: Match expiration check always returns False
   - **Fix**: Debug logging → identify timezone/parsing issue → fix comparison
   - **Priority**: P0 (blocks everything else)

2. ✅ **Identified**: Wrong requeue logic (requeues all lobbies, not just accepting ones)
   - **Fix**: Add per-lobby acceptance validation
   - **Priority**: P1 (fix after #1)

3. ✅ **Identified**: Bot lobbies destroyed on disconnect before cleanup runs
   - **Fix**: Either fix cleanup timing OR add lobby protection
   - **Priority**: P2 (may not be needed if #1 fixes timing)

**Root Cause of "Lobbies Not Requeued":**
Issue #1 (expiration not detected) is blocking Issue #2 (requeue logic) from ever running!

---

**Status:** ⚠️ **READY FOR FIXES** - Analysis complete, priority order established

