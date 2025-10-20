# Debug Logging Added for Expiration Check

## ✅ **Debug Logging Implemented**

Added comprehensive debug logging to `is_match_expired()` method to diagnose why matches aren't being detected as expired.

---

## 📁 **Files Modified:**

### **`server/matchmaking/match_confirmation.py`** (Lines 664-705)

Added detailed logging at each step of the expiration check:

```python
@staticmethod
async def is_match_expired(match_id: str) -> bool:
    # ... existing code ...
    
    logger.info(f"[EXPIRATION CHECK] Match {match_id[:8]}...")
    
    if not match_data:
        logger.info(f"  No match data found - returning True (expired)")
        return True
    
    match_info = json.loads(match_data)
    initiated_at = match_info.get('initiated_at')
    
    logger.info(f"  initiated_at (from Redis): {initiated_at}")
    
    if initiated_at:
        initiated_time = datetime.fromisoformat(initiated_at.replace('Z', '+00:00'))
        now = timezone.now()
        time_diff = (now - initiated_time).total_seconds()
        
        # DEBUG LOGGING
        logger.info(f"  initiated_time (parsed): {initiated_time}")
        logger.info(f"  initiated_time.tzinfo: {initiated_time.tzinfo}")
        logger.info(f"  now: {now}")
        logger.info(f"  now.tzinfo: {now.tzinfo}")
        logger.info(f"  time_diff: {time_diff} seconds")
        logger.info(f"  ACCEPTANCE_TIMEOUT: {MatchConfirmationManager.ACCEPTANCE_TIMEOUT}")
        logger.info(f"  time_diff > ACCEPTANCE_TIMEOUT: {time_diff} > {MatchConfirmationManager.ACCEPTANCE_TIMEOUT} = {time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT}")
        logger.info(f"  RESULT: {'EXPIRED' if time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT else 'NOT EXPIRED'}")
        
        return time_diff > MatchConfirmationManager.ACCEPTANCE_TIMEOUT
```

---

## 🧪 **Debug Test Results:**

Ran `testing/debug_expiration_check.py` which confirmed:

### **Test 1: 5 Second Elapsed**
```
initiated_at: 2025-10-12T23:41:38.474797+00:00
now:          2025-10-12T23:41:43.475667+00:00
time_diff:    5.00087 seconds
Result:       5 > 30 = False ✅ CORRECT
```

### **Test 2: 35 Second Elapsed**
```
initiated_at: 2025-10-12T23:41:08.475667+00:00
now:          2025-10-12T23:41:43.475667+00:00
time_diff:    35.0 seconds
Result:       35 > 30 = True ✅ CORRECT
```

**Conclusion:** The timezone and datetime parsing logic works perfectly!

---

## 🔍 **Next Steps for Testing:**

### **1. Restart Celery Worker**
The worker needs to pick up the new debug logging:

```bash
# In Celery Worker terminal, press Ctrl+C
# Then restart:
cd server
pipenv run celery -A scrimgg worker --loglevel=info --pool=gevent
```

### **2. Run Fresh Test**
```bash
# Clean everything
cd server/testing
python cleanup_bots_simple.py

# Run test (DON'T run cleanup script during test!)
python test_queue_with_bots_v2.py

# In user client:
# 1. Join queue
# 2. Accept match when proposed
# 3. Wait for natural timeout (30s)
# 4. DON'T press Ctrl+C - let cleanup run naturally
```

### **3. Check Celery Worker Logs**

When cleanup task runs (~15s after timeout), you should see:

```
[EXPIRATION CHECK] Match xxxxxxxx...
  initiated_at (from Redis): 2025-10-12T19:XX:XX.XXXXXX+00:00
  initiated_time (parsed): 2025-10-12 19:XX:XX.XXXXXX+00:00
  initiated_time.tzinfo: UTC
  now: 2025-10-12 19:XX:XX.XXXXXX+00:00
  now.tzinfo: UTC
  time_diff: XX.XX seconds
  ACCEPTANCE_TIMEOUT: 30
  time_diff > ACCEPTANCE_TIMEOUT: XX.XX > 30 = True/False
  RESULT: EXPIRED / NOT EXPIRED
```

This will reveal:
- ✅ If `initiated_at` is present
- ✅ If parsing works correctly
- ✅ If timezone info matches
- ✅ If time_diff calculation is correct
- ✅ The exact reason for True/False result

---

## 🎯 **Expected Outcomes:**

### **Scenario A: initiated_at is Missing**
```
  initiated_at (from Redis): None
  No initiated_at field - returning True (expired)
```
**Fix:** Check why `initiated_at` isn't being stored

### **Scenario B: Time Diff Negative**
```
  time_diff: -XX.XX seconds
  RESULT: NOT EXPIRED
```
**Fix:** Timezone mismatch issue, need to normalize

### **Scenario C: Everything Correct, Still Returns False**
```
  time_diff: 45.0 seconds
  time_diff > 30 = 45.0 > 30 = False  ← Should be True!
```
**Fix:** Logic error or type issue

### **Scenario D: Works Correctly Now**
```
  time_diff: 45.0 seconds
  time_diff > 30 = True
  RESULT: EXPIRED
```
**Status:** Issue resolved by Celery restart!

---

## ⚠️ **Important Notes:**

### **Don't Run Cleanup Script During Test!**
The cleanup script (`cleanup_bots_simple.py`) deletes match confirmations, which will interfere with the natural timeout flow.

**Only run cleanup script:**
- Before starting a new test
- After test completes
- NOT during an active match

### **Let Test Run Naturally:**
- Don't press Ctrl+C until after cleanup runs
- Wait at least 60 seconds after last acceptance
- This allows cleanup task to process the expired match

---

## 📊 **What Debug Logs Will Reveal:**

The new logging will show us **exactly** why `is_match_expired()` is returning `False`:

1. **Is data missing?** → Will see "No match data found"
2. **Is `initiated_at` missing?** → Will see "No initiated_at field"
3. **Is parsing failing?** → Will see error message
4. **Is timezone mismatched?** → Will see different tzinfo values
5. **Is time_diff wrong?** → Will see the actual calculation
6. **Is comparison failing?** → Will see the boolean result

---

**Status:** ✅ **DEBUG LOGGING ADDED** - Ready for test run with fresh Celery Worker

