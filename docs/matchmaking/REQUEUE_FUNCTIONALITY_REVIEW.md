# Requeue Functionality Review

## ✅ **Requeue Functionality EXISTS and is Implemented**

---

## 📋 **Where It's Implemented:**

### **File**: `server/matchmaking/match_confirmation.py`

---

## 🔄 **Requeue Scenarios:**

### **1. Match Timeout (No one accepts in 30 seconds)**

**Function**: `handle_expired_match(match_id)` (Line 636)

**Flow**:
1. Match confirmation expires (30 seconds)
2. `cleanup_expired_matches` Celery task detects it
3. Calls `handle_expired_match`
4. Cancels the match
5. **Requeues ALL lobbies** that were in the match

**Code**:
```python
for lobby_id in lobbies:
    # Get lobby leader
    lobby = await sync_to_async(get_lobby)()
    
    if lobby.lobby_leader:
        # Try to requeue
        requeue_result = await QueueManager.join_queue(lobby_id, lobby.lobby_leader.puuid)
        
        if requeue_result['status'] == 'success':
            requeued_lobbies.append(lobby_id)
            logger.info(f"Requeued lobby {lobby_id} after match timeout")
```

**Status**: ✅ **WORKING** - All lobbies automatically requeued

---

### **2. Player Declines Match**

**Function**: `decline_match(match_id, player_puuid)` (Line 435)

**Flow**:
1. Player clicks decline/close button
2. Calls `decline_match`
3. Cancels the match
4. Returns affected lobbies
5. **Does NOT automatically requeue** (by design)

**Code**:
```python
# Cancel the match
cancel_result = await MatchConfirmationManager.cancel_match(match_id, 'Player declined match')

if cancel_result['status'] == 'cancelled':
    return {
        'status': 'success',
        'message': 'Match declined successfully',
        'affected_lobbies': match_lobbies,  # Returned but NOT requeued
        'match_id': match_id
    }
```

**Status**: ⚠️ **PARTIALLY IMPLEMENTED** - Cancels match but doesn't requeue

**Expected Behavior**: Players who **did accept** should be requeued (smart requeue with priority bias - not yet implemented)

---

## ⚠️ **Issue Found: Database Call in Requeue**

**Problem**: Line 679 in `handle_expired_match`:
```python
lobby = await sync_to_async(get_lobby)()  # ❌ BLOCKING
```

This is a `sync_to_async` call that could cause deadlocks in gevent pool.

**Better Approach**:
Store lobby leader PUUID in match data so we don't need to query database.

---

## 🎯 **Current State:**

### **Working:**
- ✅ Match timeout detection
- ✅ Match cancellation
- ✅ Lobby requeue after timeout
- ✅ `match_timeout` event sent to clients

### **Not Implemented:**
- ❌ Smart requeue with priority bias
- ❌ Requeue after player decline (only cancels)
- ❌ Tracking which lobbies accepted vs didn't
- ❌ Separate handling for accepting vs non-accepting lobbies

---

## 📊 **Requeue Flow (Current):**

```
Match Timeout (30s):
├─ cleanup_expired_matches task runs
├─ Detects expired match
├─ Cancels match
├─ Gets all 10 lobbies
├─ For each lobby:
│  ├─ Query database for lobby leader (BLOCKING)
│  ├─ Call QueueManager.join_queue
│  └─ Lobby back in queue
└─ All lobbies requeued (no priority bias)
```

---

## 🚀 **Recommended Improvements:**

### **1. Remove Database Call** (High Priority)
Store lobby leader PUUID in match confirmation data to avoid sync_to_async.

### **2. Implement Smart Requeue** (From your earlier design)
- Track which lobbies accepted
- Give priority bias to accepting lobbies
- Don't requeue non-accepting lobbies (or give them penalties)

### **3. Add Requeue Logging**
```python
logger.info(f"🔄 REQUEUING: {len(lobbies)} lobbies after match timeout")
for lobby_id in requeued_lobbies:
    logger.info(f"   ✅ Lobby {lobby_id[:8]}... back in queue")
```

---

## 🎯 **Verdict:**

**Basic requeue functionality IS implemented** but:
- ⚠️ Has a potential deadlock (sync_to_async)
- ⚠️ Missing smart requeue/priority bias
- ⚠️ Missing penalties for dodgers
- ⚠️ Requeues ALL lobbies equally (no fairness)

**For MVP testing**: ✅ It works (requeues on timeout)

**For production**: ❌ Needs improvements (remove database call, add priority bias)

---

**Current functionality is GOOD ENOUGH for testing, but will need enhancement for production.**

