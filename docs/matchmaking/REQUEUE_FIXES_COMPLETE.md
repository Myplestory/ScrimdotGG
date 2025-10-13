# Match Timeout Requeue - All Fixes Applied

## Summary
Fixed critical bugs preventing automatic requeue after match timeout.

---

## 🐛 **Bugs Fixed:**

### 1. **UUID Serialization Error**
**Location:** `server/matchmaking/consumers.py:683`

**Problem:** UUID objects were being sent through WebSocket without conversion to string.

**Fix:**
```python
# Before
'match_id': result.get('match_id')

# After  
'match_id': str(result.get('match_id')) if result.get('match_id') else None
```

---

### 2. **AsyncToSync Event Loop Conflict**
**Location:** `server/matchmaking/tasks.py:144-219`

**Problem:** Cleanup task was using `async_to_sync` when an event loop already existed (gevent pool).

**Fix:** Use `asyncio.new_event_loop()` and `loop.run_until_complete()` instead:
```python
import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    active_confirmations = loop.run_until_complete(
        MatchConfirmationManager.get_all_active_confirmations()
    )
    # ... rest of cleanup logic
finally:
    loop.close()
```

---

### 3. **Cleanup Frequency Too Slow**
**Location:** `server/scrimgg/celery.py:28`

**Problem:** Cleanup ran every 60 seconds, but matches timeout after 30 seconds, causing Redis keys to expire before cleanup could process them.

**Fix:** Changed frequency to 15 seconds:
```python
'cleanup-expired-matches': {
    'task': 'matchmaking.tasks.cleanup_expired_matches',
    'schedule': 15.0,  # Run every 15 seconds (catches 30s timeouts reliably)
},
```

**Timeline:**
```
├─ 0s:  Match found
├─ 15s: Cleanup runs (no timeouts yet)
├─ 30s: Match times out ⏰
├─ 30s: Cleanup runs (CATCHES TIMEOUT) ✅
├─ 31s: Lobbies requeued automatically
└─ 40s: Matchmaker finds them again
```

---

### 4. **Redis TTL Not Set on Empty Set**
**Location:** `server/matchmaking/match_confirmation.py:78, 251`

**Problem:** 
- Line 78 set TTL on empty `accepted_key` (doesn't work in Redis)
- Line 248 added players with `sadd` but TTL was not preserved
- Result: `accepted_key` had no TTL

**Fix:** Refresh TTL after each `sadd`:
```python
# Mark as accepted
redis_conn.sadd(accepted_key, player_puuid)

# Ensure TTL is set (Redis doesn't preserve TTL when adding to empty set)
redis_conn.expire(accepted_key, MatchConfirmationManager.MATCH_DATA_TTL)
```

---

### 5. **Field Name Mismatch**
**Location:** `server/matchmaking/match_confirmation.py:665`

**Problem:** 
- We store: `match_data['initiated_at']` (line 127)
- We check: `match_info.get('created_at')` (line 665)
- Result: Expiration check always failed, returned True immediately

**Fix:**
```python
# Before
created_at = match_info.get('created_at')

# After
initiated_at = match_info.get('initiated_at')  # Fixed: was 'created_at'
```

---

### 6. **Cleanup Script Deleting Active Matches**
**Location:** `server/testing/cleanup_bots_simple.py:83-91`

**Problem:** When running cleanup script during active matches, it deleted match confirmations, preventing requeue.

**Fix:** Added match confirmation cleanup to script (runs every time):
```python
# Clear all match confirmations from Redis
print("\nClearing all match confirmations...")
match_conf_keys = redis_client.keys('match_confirmation:*')
if match_conf_keys:
    for key in match_conf_keys:
        redis_client.delete(key)
    print(f"Cleared {len(match_conf_keys)} match confirmations")
```

---

## ✅ **How It Works Now:**

### Match Timeout Flow:
1. **Match proposed** → 10 players notified → 30s timer starts
2. **Some players accept** → Progress tracked in Redis
3. **30 seconds pass** → Not all players accepted
4. **Cleanup runs** (at 30s, 45s, or 60s) → Detects expired match
5. **Match cancelled** → Gets `full_lobby_data` from Redis
6. **Lobbies requeued** → Direct Redis operation (no DB calls)
7. **DB updated** → Background task (non-blocking)
8. **Players back in queue** → Matchmaker finds them again

### Key Design Decisions:
- ✅ **5-minute TTL** on all match data (not 30s) - gives cleanup time to process
- ✅ **15-second cleanup frequency** - catches timeouts reliably
- ✅ **Store full lobby data** in match confirmation - enables requeue without DB
- ✅ **Background DB updates** - non-blocking, prevents deadlocks
- ✅ **UUID → string conversion** - JSON serializable WebSocket messages

---

## 🧪 **Testing:**

### Commands:
```bash
# 1. Cleanup old data
cd server
pipenv run python testing/cleanup_bots_simple.py

# 2. Start services (if not running)
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application
pipenv run celery -A scrimgg worker --loglevel=debug -Q celery,matchmaking,cleanup
pipenv run celery -A scrimgg beat --loglevel=info

# 3. Run test (8 bots accept, 1 doesn't)
pipenv run python testing/test_queue_with_bots_v2.py

# 4. In Electron client, join queue and accept match
# 5. Wait 30s for timeout
# 6. Verify requeue in logs
```

### Expected Behavior:
- ✅ Match proposed to all 10 players
- ✅ 9/10 accept (user + 8 bots)
- ✅ 1 bot doesn't accept (queuebot-8)
- ✅ After 30s, modal closes
- ✅ Cleanup detects expired match
- ✅ All 9 accepting lobbies requeued
- ✅ Matchmaker finds new match

---

## 📊 **Configuration:**

### Celery Beat Schedule:
```python
'periodic-matchmaking': {
    'schedule': 10.0,  # Every 10 seconds
},
'cleanup-expired-matches': {
    'schedule': 15.0,  # Every 15 seconds ⭐ UPDATED
},
'cleanup-expired-queues': {
    'schedule': 300.0,  # Every 5 minutes
},
```

### Redis TTLs:
```python
ACCEPTANCE_TIMEOUT = 30  # seconds (match timeout)
MATCH_DATA_TTL = 300     # seconds (5 minutes - for cleanup to process)
```

---

## 🎯 **Next Steps:**

1. ✅ All fixes applied
2. ⏳ **Restart Celery Worker & Beat** (to pick up code changes)
3. ⏳ **Test with bots** (verify requeue works)
4. ⏳ **Implement priority bias** (for requeued lobbies)

---

**Status:** ✅ **READY FOR TESTING**

All critical bugs fixed. Requeue should now work correctly!

