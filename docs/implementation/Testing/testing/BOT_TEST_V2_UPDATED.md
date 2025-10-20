# Bot Test V2 Script - Updated with Phase 2

## ✅ **Implementation Complete**

Updated the bot test script to include automatic rematch testing after requeueing.

---

## 🎯 **What Changed:**

### **1. Modified `monitor_match_and_timeout()`**
- **Change:** Now returns `requeued_count` instead of boolean
- **Purpose:** Main function can decide whether to run Phase 2

### **2. Added `spawn_10th_bot_and_test_rematch()`**
- **Purpose:** Create replacement bot and verify rematch works
- **Timing:** Runs after 1-minute wait (ensures stability)

### **3. Updated Main Flow**
- **Change:** Checks `requeued_count` and conditionally runs Phase 2
- **Safety:** Fixed `acceptor_task` None issue with fallback

---

## 📋 **Complete Test Flow:**

### **PHASE 1: Timeout and Requeue** (0-90 seconds)
```
00:00 - Create 9 bots, queue them
00:10 - User joins queue (10 total)
00:20 - Match found
00:25 - 9/10 players accept (queuebot-8 doesn't)
00:55 - Match times out (30s elapsed)
01:05 - Cleanup runs, detects expiration
01:05 - 9 lobbies requeued (queuebot-8 removed)
```

### **WAIT PERIOD** (90-150 seconds)
```
01:05 - Phase 1 complete
01:05 - "Waiting 1 minute before spawning 10th bot..."
02:05 - 1 minute wait complete
```

### **PHASE 2: Rematch Test** (150-210 seconds)
```
02:05 - Create queuebot-9 (replacement bot)
02:06 - Connect queuebot-9 to WebSocket
02:07 - Add queuebot-9 to queue
02:08 - Queue complete: 10 lobbies
02:10 - Matchmaker runs (10s frequency)
02:15 - New match created!
02:16 - All 10 bots accept
02:16 - Match ready! ✅
```

---

## 🧪 **Expected Output:**

```
======================================================================
Queue Test V2 - Partial Accept + Rematch Test
======================================================================

[PHASE 1] Timeout and Requeue Test:
  1. Create 9 bot players with similar MMR to you
  ...
  8. Match times out → 9 lobbies requeued!

[PHASE 2] Rematch Test:
  9. Spawn 10th bot (replaces the one that didn't accept)
 10. Queue completes (9 requeued + 1 new = 10 total)
 11. New match triggered automatically
 12. All 10 bots auto-accept → Match ready!

... Phase 1 runs ...

[SUCCESS] ✅ Timeout and requeue flow completed!
[INFO] 9 lobbies successfully requeued

[INFO] Waiting 1 minute before spawning 10th bot...
(60 second countdown)

[INFO] Starting Phase 2: Testing rematch with requeued lobbies...

======================================================================
PHASE 2: Spawning 10th Bot for Rematch Test
======================================================================

[INFO] Creating 10th bot to complete the queue...
[SUCCESS] Created queuebot-9 (PUUID: xxxxxxxxxxxx...)
[SUCCESS] Lobby created and queued for queuebot-9
[INFO] Connecting queuebot-9 to WebSocket...
[SUCCESS] queuebot-9 connected and monitoring for matches

[QUEUE STATUS] 10 lobbies, 10 players
[SUCCESS] ✅ Queue complete! Should trigger match soon...

[MONITORING] Watching for rematch...
   [SUCCESS] ✅ Rematch created: yyyyyyyy...
   [INFO] This confirms requeueing worked correctly!
   [INFO] All 10 bots will auto-accept this match

[SUCCESS] ✅✅ REMATCH SUCCESSFUL!
[INFO] Requeueing system is working perfectly!

======================================================================
Test Complete!
======================================================================
```

---

## 🔧 **Key Implementation Details:**

### **1-Minute Wait Period:**
```python
await asyncio.sleep(60)  # 1 minute stability buffer
```
**Why:** Ensures system is stable after requeueing before spawning new bot

### **Automatic Bot Creation:**
```python
bot_data = await create_bot_with_lobby(9, you_elo, you_mmr, you_region)
```
**Uses:** Same function as initial bots (creates player, lobby, and queues automatically)

### **WebSocket Connection:**
```python
await acceptor.ws_manager.connect_bot(bot_puuid)
acceptor.add_bots([bot_puuid])
```
**Purpose:** New bot can receive match proposals and auto-accept

### **Safe Task Handling:**
```python
if acceptor_task:
    await acceptor_task
else:
    await asyncio.Event().wait()  # Fallback
```
**Purpose:** Prevents "None can't be awaited" error

---

## ⏱️ **Timeline:**

| Time | Event |
|------|-------|
| 0:00 | Script starts, creates 9 bots |
| 0:10 | User joins, match found |
| 0:25 | 9/10 accept |
| 0:55 | Match times out |
| 1:05 | 9 lobbies requeued ✅ |
| **1:05** | **Wait 1 minute...** |
| **2:05** | **Spawn queuebot-9** |
| **2:10** | **New match created** |
| **2:16** | **All accept, match ready** ✅ |

**Total test time:** ~2-3 minutes

---

## ✅ **What This Tests:**

### **Correctness:**
- ✅ All 10 lobby data preserved
- ✅ Only 9/10 lobbies requeued (fair)
- ✅ Requeued lobbies retain MMR/ELO
- ✅ New bot can join requeued lobbies

### **Stability:**
- ✅ 1-minute wait ensures no race conditions
- ✅ System ready for new match
- ✅ WebSocket connections stable

### **End-to-End:**
- ✅ Timeout → Requeue → Rematch → Ready
- ✅ Full matchmaking cycle works
- ✅ No data loss or corruption

---

## 🚀 **Usage:**

Just run the script:
```bash
python testing/test_queue_with_bots_v2.py
```

**The script will:**
1. Run Phase 1 (timeout test)
2. Wait 1 minute
3. Automatically run Phase 2 (rematch test)
4. Report results

**No manual intervention needed!**

---

**Status:** ✅ **READY FOR TESTING** - Safe, stable implementation with 1-minute buffer

