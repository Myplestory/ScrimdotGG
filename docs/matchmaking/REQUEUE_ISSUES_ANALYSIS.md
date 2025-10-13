# Requeueing Issues - Analysis

## Current Status

### ✅ **What's Working:**
1. Cleanup task NOW finds match confirmations (fixed Redis key pattern)
2. Cleanup task detects expired matches
3. Some requeueing happens (2 out of 10 lobbies)
4. Match timeout detected and handled

### ❌ **What's NOT Working:**
1. Only 2/10 lobbies requeued (should be all 10)
2. Queue button deactivated after user accepts
3. Timer stuck at 0:00 (not counting down)

---

## Issue 1: Only 2/10 Lobbies Requeued

### **Evidence:**
Test bot logs line 972: "Queue now has 2 lobbies" (should be 10)

### **Possible Causes:**

#### **A. Lobby Data Not Stored Correctly**
- `full_lobby_data` might be missing for some lobbies
- Check if `initiate_confirmation` stores data for all 10 lobbies

#### **B. Lobbies Already Destroyed**
- Bots disconnected before requeueing happened
- WebSocket disconnect destroys solo lobbies
- Requeueing tries to enqueue destroyed lobbies

#### **C. Celery Worker Has Old Code**
- Worker needs restart to pick up the new Redis key pattern fix
- Still using old code that can't find matches

#### **D. Requeueing Logic Error**
- Error during `enqueue_lobby` for some lobbies
- Check Celery Worker logs for error messages

### **Next Steps:**
1. **Restart Celery Worker** (pick up new code)
2. Check Celery Worker logs around 19:12:08 for requeueing details
3. Look for errors like "No lobby data found" or "Failed to requeue"

---

## Issue 2: Queue Button Deactivated After Accepting

### **Root Cause:**
**Location:** `client/frontend/src/pages/PugQueue.jsx:178-192`

When `match_timeout` event is received, the handler calls:
```javascript
api.leavePugQueue();  // ← This deactivates the queue button!
```

### **The Problem:**
1. User accepts match → stays in queue (correct)
2. Match times out → `match_timeout` event sent
3. Frontend receives `match_timeout`
4. Frontend calls `leavePugQueue()` → **User removed from queue** ❌
5. Queue button becomes "Find Match" instead of "Cancel"

### **The Fix:**
The `match_timeout` handler should **NOT** remove the user from the queue because:
- User has already accepted
- Timeout happened due to OTHER players not accepting
- User should be automatically requeued by the server
- Frontend should wait for `lobby_queued` event confirmation

**Remove lines 188-191**:
```javascript
// OLD CODE - REMOVE THIS
if (queueStatus.in_queue) {
  api.leavePugQueue();  // ← DON'T DO THIS!
  setQueueStartTime(null);
}
```

**New code - just close modal**:
```javascript
// Match timed out - just close modal and wait for requeue
// Server will handle requeueing automatically
console.log('Match timed out - waiting for automatic requeue');
```

---

## Issue 3: Timer Stuck at 0:00

### **Root Cause:**
**Location:** `client/frontend/src/pages/PugQueue.jsx:209-234`

The timer countdown logic works, BUT:
- Line 156: Initial `timeLeft` set from `payload.accept_deadline`
- Line 168: `timeLeft` updated from `payload.timeout_seconds` on each `player_accepted` event

### **The Problem:**
If `payload.accept_deadline` or `payload.timeout_seconds` is **0 or undefined**, timer starts at 0.

### **Check:**
1. Does `pug_match_found` event include `accept_deadline` field?
2. Does `player_accepted` event include `timeout_seconds` field?

### **Expected Flow:**
```
Match Found → timeLeft = 30
1 second passes → timeLeft = 29
Player accepts → timeLeft updated from payload.timeout_seconds = 28
1 second passes → timeLeft = 27
...
```

### **Actual Flow (if timer stuck):**
```
Match Found → timeLeft = 0 (if accept_deadline missing)
OR
Match Found → timeLeft = 30
Player accepts → timeLeft = 0 (if timeout_seconds = 0 in payload)
```

### **The Fix:**
Check what the server is sending in the `match_found` event payload.

---

## Investigation Needed

### **1. Check Celery Worker Logs:**
Look for lines around **19:12:08** (when cleanup ran after match timeout):
```
[INFO] 🔄 Requeuing 10 lobbies after match timeout...
[INFO]    Found complete data for X lobbies
[INFO]    ✅ Lobby XXXXX... back in queue
[WARNING]    No data for lobby YYYYY..., skipping
[ERROR]    Error requeuing lobby ZZZZZ...
```

### **2. Check Match Found Payload:**
In browser console, check:
```javascript
🎮 [DEBUG] pug_match_found event received: {
  match_id: "...",
  accept_deadline: ???,  // ← Should be 30
  timeout_seconds: ???   // ← Should be 30
}
```

### **3. Check Player Accepted Payload:**
```javascript
🔔 [DEBUG] player_accepted event received: {
  accepted_count: X,
  total_players: 10,
  timeout_seconds: ???  // ← Should be remaining time
}
```

---

## Summary

**The core requeueing logic is NOW working** (cleanup finds matches!), but:
1. **Only 2/10 lobbies requeued** → Need to check why 8 failed
2. **Queue button issue** → Frontend removing user from queue on timeout (should wait for server)
3. **Timer issue** → Check what values server is sending in events

**Next Action:** Restart Celery Worker to pick up the new code, then test again.

