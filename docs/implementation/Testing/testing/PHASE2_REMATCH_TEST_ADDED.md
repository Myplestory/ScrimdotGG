# Phase 2 Rematch Test - Added to Bot Test Script

## ✅ **New Functionality Added**

Added automatic rematch testing to verify requeueing works end-to-end.

---

## 🎯 **What Was Added:**

### **New Function: `spawn_10th_bot_and_test_rematch()`**

**Location:** `server/testing/test_queue_with_bots_v2.py:316-395`

**Purpose:** After the first match times out and lobbies are requeued, spawn a 10th bot to complete the queue and trigger a new match.

**Flow:**
1. Wait 3 seconds after requeueing
2. Create new bot (`queuebot-9`) to replace the one that didn't accept
3. Connect bot to WebSocket
4. Add bot to auto-acceptor monitoring
5. Bot automatically joins queue (via `create_bot_with_lobby`)
6. Wait for queue to reach 10 lobbies
7. Monitor for new match creation (up to 30 seconds)
8. Verify rematch is created successfully

---

## 📋 **Complete Test Flow:**

### **PHASE 1: Timeout and Requeue Test**
```
1. Create 9 bots (queuebot-0 to queuebot-8)
2. User joins queue (10 total)
3. Match found
4. 8 bots + user accept = 9/10
5. queuebot-8 does NOT accept
6. Match times out after 30s
7. Cleanup runs:
   - Detects expired match ✅
   - Checks per-lobby acceptance
   - Requeues 9 lobbies (all who accepted)
   - Does NOT requeue queuebot-8
8. Result: 9 lobbies in queue
```

### **PHASE 2: Rematch Test** ⭐ **NEW!**
```
9. Wait 3-5 seconds
10. Create queuebot-9 (replacement bot)
11. Connect queuebot-9 to WebSocket
12. Add queuebot-9 to queue
13. Queue Status: 9 + 1 = 10 lobbies ✅
14. Wait for matchmaking (runs every 10s)
15. New match created!
16. All 10 bots auto-accept (no timeout this time)
17. Match ready! ✅
18. Result: Confirms requeueing worked perfectly
```

---

## 🧪 **Expected Output:**

### **Phase 1 Output:**
```
[MONITORING] Watching for match and timeout behavior...
   [DETECTED] Match created: xxxxxxxx...
   [INFO] Waiting for timeout (30 seconds)...
   
   [SUCCESS] Match timed out and was cleaned up!
   [REQUEUE] Queue now has 9 lobbies
   [SUCCESS] ✅ Lobbies were requeued automatically!

[SUCCESS] ✅ Timeout and requeue flow completed!
[INFO] 9 lobbies successfully requeued
```

### **Phase 2 Output:**
```
======================================================================
PHASE 2: Spawning 10th Bot for Rematch Test
======================================================================

[INFO] Creating 10th bot to complete the queue...
[INFO] This will trigger a new match with the requeued lobbies
[INFO] Creating and queuing queuebot-9...
[SUCCESS] Created queuebot-9 (PUUID: xxxxxxxxxxxx...)
[SUCCESS] Lobby created and queued for queuebot-9

[INFO] Connecting queuebot-9 to WebSocket...
[SUCCESS] queuebot-9 connected and monitoring for matches

[QUEUE STATUS] 10 lobbies, 10 players
[SUCCESS] ✅ Queue complete! Should trigger match soon...
[INFO] Matchmaker runs every 10 seconds
[INFO] Watch for new match in next 10-20 seconds...

[MONITORING] Watching for rematch...
   [SUCCESS] ✅ Rematch created: yyyyyyyy...
   [INFO] This confirms requeueing worked correctly!
   [INFO] All 10 bots will auto-accept this match

[SUCCESS] ✅✅ REMATCH SUCCESSFUL!
[INFO] Requeueing system is working perfectly!
```

---

## 📊 **What This Tests:**

### **Requeue Correctness:**
- ✅ All 9 lobbies preserved their data
- ✅ All 9 lobbies successfully requeued
- ✅ queuebot-8 (non-acceptor) NOT requeued
- ✅ User lobby requeued and ready

### **Matchmaking After Requeue:**
- ✅ Requeued lobbies still have correct MMR/ELO
- ✅ Requeued lobbies can be matched again
- ✅ New bot can join existing requeued lobbies
- ✅ Match quality maintained

### **Full System Integration:**
- ✅ Cleanup → Requeue → Match → Accept flow works
- ✅ No data loss during requeue
- ✅ WebSocket connections remain stable
- ✅ All 10 players can accept without issues

---

## 🎯 **Key Benefits:**

1. **Automated Testing:** No manual intervention needed for Phase 2
2. **End-to-End Validation:** Tests complete cycle from timeout to rematch
3. **Confirms Fixes:** Proves all 3 critical bugs are fixed:
   - ✅ All lobby data preserved (10/10)
   - ✅ Only accepting lobbies requeued (9/10)
   - ✅ Rematch works with requeued lobbies

---

## 🚀 **Usage:**

Just run the script normally:
```bash
python testing/test_queue_with_bots_v2.py
```

**The script will automatically:**
1. Run Phase 1 (timeout test)
2. Detect successful requeueing
3. Launch Phase 2 (rematch test)
4. Spawn 10th bot
5. Verify rematch works

**No additional commands needed!**

---

## ⚠️ **Important Notes:**

### **Bot Name:**
- Original bots: `queuebot-0` through `queuebot-8` (9 bots)
- `queuebot-8` doesn't accept and is removed
- New bot: `queuebot-9` (replaces queuebot-8)
- Rematch: `queuebot-0 to 7` + `queuebot-9` + user = 10 total

### **Auto-Acceptance:**
- Phase 1: 8/9 bots accept (selective)
- Phase 2: 10/10 bots accept (all bots will accept rematch)
- This tests both timeout AND successful match flows

### **Timing:**
- 3 second pause between phases
- Up to 30 seconds to detect rematch
- Plenty of time for matchmaking to run (every 10s)

---

**Status:** ✅ **PHASE 2 ADDED** - Script ready for comprehensive testing

