# Frontend Timer and Queue Button Fixes

## Summary
Fixed two critical frontend issues with the queue timer and queue button state after match timeout.

---

## 🐛 **Issues Fixed:**

### **Issue 1: Total Queue Time Timer Stuck at 0:00**

**Problem:**
- The total queue time (how long you've been in queue) was always showing `0:00`
- Timer wasn't counting up

**Root Causes:**
1. **`queueStartTime` not set on queue join**: Line 133 (`queue_joined` event) didn't set `queueStartTime`
2. **Timer interval doesn't trigger re-render**: Lines 311-316 had an empty interval that didn't force component update

**Fixes Applied:**

#### **Fix 1a: Set queue start time on join** (`PugQueue.jsx:140-143`)
```jsx
// OLD CODE - queueStartTime never set on queue_joined event
const unsubscribeQueueJoined = on('queue_joined', (payload) => {
  setQueueStatus({ ... });
  // queueStartTime NOT set here!
});

// NEW CODE - Set queueStartTime when joining queue
const unsubscribeQueueJoined = on('queue_joined', (payload) => {
  setQueueStatus({ ... });
  // Set queue start time if not already set
  if (!queueStartTime) {
    setQueueStartTime(Date.now());
  }
});
```

#### **Fix 1b: Force re-render every second** (`PugQueue.jsx:312-322`)
```jsx
// OLD CODE - Empty interval, no re-render
useEffect(() => {
  let interval;
  if (queueStatus.in_queue && queueStartTime) {
    interval = setInterval(() => {
      // Force re-render to update timer display
      // ❌ Empty - doesn't do anything!
    }, 1000);
  }
  return () => clearInterval(interval);
}, [queueStatus.in_queue, queueStartTime]);

// NEW CODE - Force re-render using state update
const [, forceUpdate] = useState(0);
useEffect(() => {
  let interval;
  if (queueStatus.in_queue && queueStartTime) {
    interval = setInterval(() => {
      // Force re-render to update timer display
      forceUpdate(prev => prev + 1); // ✅ Triggers re-render
    }, 1000);
  }
  return () => clearInterval(interval);
}, [queueStatus.in_queue, queueStartTime]);
```

---

### **Issue 2: Queue Button Deactivated After Match Timeout**

**Problem:**
- When match timed out, queue button became inactive (grayed out)
- This happened even if user accepted (but another player didn't)
- User expected to stay in queue if they accepted

**Root Cause:**
**Location:** `PugQueue.jsx:182-204` (before fix)

The `match_timeout` handler **always** called `api.leavePugQueue()`, regardless of whether the user accepted or not.

```jsx
// OLD CODE - Always leaves queue on timeout
const unsubscribeMatchTimeout = on('match_timeout', (payload) => {
  setMatchFound(false);
  // ...
  
  // ❌ ALWAYS removes from queue, even if user accepted!
  if (queueStatus.in_queue) {
    api.leavePugQueue();
    setQueueStartTime(null);
  }
});
```

**Fix Applied:**

```jsx
// NEW CODE - Only leave queue if user didn't accept
const unsubscribeMatchTimeout = on('match_timeout', (payload) => {
  console.log('Match acceptance timed out:', payload);
  
  // Check if user accepted before timing out
  const userDidAccept = userAccepted;
  
  setMatchFound(false);
  setMatchData(null);
  setAcceptedCount(0);
  setTotalPlayers(10);
  setUserAccepted(false);
  
  // Only remove from queue if user DIDN'T accept
  // If user accepted, they should be requeued automatically by the server
  if (!userDidAccept && queueStatus.in_queue) {
    console.log('User did not accept - leaving queue');
    api.leavePugQueue();
    setQueueStartTime(null);
  } else if (userDidAccept) {
    console.log('User accepted - staying in queue for automatic requeue');
  }
});
```

---

## ✅ **Expected Behavior After Fixes:**

### **Scenario 1: User Joins Queue**
1. User clicks "FIND MATCH"
2. Timer starts at `0:00` and counts up: `0:01`, `0:02`, `0:03`, etc.
3. Timer continues counting while in queue

### **Scenario 2: Match Found, User Accepts, Match Times Out**
1. Match proposed (9/10 accept, 1 doesn't)
2. User accepts → `userAccepted = true`
3. Match times out after 30s
4. Modal closes
5. **User stays in queue** ✅
6. Queue button stays active (not grayed out) ✅
7. Timer continues counting ✅
8. Server automatically requeues user's lobby ✅

### **Scenario 3: Match Found, User Doesn't Accept, Match Times Out**
1. Match proposed
2. User doesn't click accept → `userAccepted = false`
3. Match times out after 30s
4. Modal closes
5. **User removed from queue** ✅
6. Queue button becomes inactive ✅
7. Timer resets to `0:00` ✅

---

## 📁 Files Modified

1. **`client/frontend/src/pages/PugQueue.jsx`**:
   - Lines 140-143: Set `queueStartTime` on `queue_joined` event
   - Lines 312-322: Force re-render every second for timer update
   - Lines 182-204: Conditional queue leave based on user acceptance

---

## 🧪 **Testing Instructions:**

### **Test 1: Queue Timer Counts Up**
1. Join queue
2. Verify timer shows `0:00` → `0:01` → `0:02` → etc.
3. Wait 1 minute
4. Verify timer shows `1:00`, `1:01`, `1:02`, etc.

### **Test 2: Stay in Queue After Accepting (Match Timeout)**
1. Join queue with bots (9 bots + you = 10)
2. Match found
3. **Accept the match**
4. Wait for match to timeout (1 bot doesn't accept)
5. Modal closes
6. **Verify:**
   - ✅ Queue button is still active (not grayed out)
   - ✅ Timer continues counting
   - ✅ You're still in queue (can see queue status)

### **Test 3: Leave Queue After Not Accepting**
1. Join queue
2. Match found
3. **Don't accept** (let timer expire)
4. **Verify:**
   - ✅ Queue button is inactive (grayed out)
   - ✅ Timer shows `0:00`
   - ✅ You're out of queue

---

## 🎯 **Key Improvements:**

1. **Better UX**: Users who accept matches aren't punished if others don't accept
2. **Accurate Timer**: Queue time accurately reflects how long user has been waiting
3. **Automatic Requeue**: Server-side requeue logic now works correctly with frontend state
4. **Consistent State**: Queue state matches server state more accurately

---

## 🔗 **Related Fixes:**

- **Server-side requeue fix**: `server/REQUEUE_FIX_FINAL.md`
- **WebSocket bot implementation**: `server/BOT_WEBSOCKET_IMPLEMENTATION_COMPLETE.md`
- **Modal indicator fix**: `server/MODAL_AND_TIMING_FIXES.md`

---

**Status:** ✅ **COMPLETE** - All frontend timer and queue button issues resolved

