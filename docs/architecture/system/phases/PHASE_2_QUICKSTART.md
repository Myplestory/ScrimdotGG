# Phase 2 Quick Start Guide

## 🎯 Overview
Phase 2 implements the queue and matchmaking system that finds 10 players from queued lobbies and creates balanced matches.

---

## ⚡ Quick Setup

### Step 1: Install Redis

**Choose ONE option:**

**Option A: WSL2 (Recommended)**
```bash
# In Ubuntu/WSL terminal
sudo apt update && sudo apt install redis-server -y
sudo service redis-server start
redis-cli ping  # Should return: PONG
```

**Option B: Docker**
```powershell
docker run -d --name redis-scrimgg -p 6379:6379 redis:alpine
docker exec -it redis-scrimgg redis-cli ping  # Should return: PONG
```

**Option C: Memurai (Native Windows)**
- Download from: https://www.memurai.com/get-memurai
- Install and it auto-starts as a service

📖 **Full guide:** `docs/REDIS_SETUP_WINDOWS.md`

---

### Step 2: Test Redis Connection

```bash
cd server
python test_redis.py
```

**Expected output:**
```
✅ ALL TESTS PASSED (5/5)
🚀 Redis is ready for Phase 2 implementation!
```

---

### Step 3: Implementation Components

Phase 2 adds these new services:

1. **QueueManager** (`server/matchmaking/queue_manager.py`)
   - Add/remove lobbies from queue
   - Priority-based matching
   - Queue statistics

2. **Matchmaker** (`server/matchmaking/matchmaker.py`)
   - Find 10 players from queue
   - Balance teams by ELO
   - Match quality scoring

3. **MatchConfirmationManager** (`server/matchmaking/match_confirmation.py`)
   - 30-second acceptance window
   - Track player responses
   - Handle dodges/timeouts

4. **Celery Tasks** (`server/matchmaking/tasks.py`)
   - Background matchmaking (every 5 seconds)
   - Timeout handling
   - Queue cleanup

---

## 🚀 What Gets Implemented

### Queue Operations
- ✅ Lobby joins queue with preferences
- ✅ Redis sorted set for ELO-based priority
- ✅ Queue position tracking
- ✅ Estimated wait times

### Matchmaking
- ✅ Find compatible lobbies (10 players total)
- ✅ ELO range validation (starts at ±100, expands with time)
- ✅ Map preference matching
- ✅ Team balancing algorithm

### Match Confirmation
- ✅ All 10 players notified
- ✅ 30-second countdown
- ✅ Accept/Decline tracking
- ✅ Auto-cancel on timeout
- ✅ Requeue accepting players

---

## 📊 Architecture Flow

```
Player → Join Queue
    ↓
Lobby added to Redis (sorted by ELO)
    ↓
Celery Task (runs every 5s)
    ↓
Matchmaker finds 10 players
    ↓
Balance into 2 teams
    ↓
Create Match Confirmation
    ↓
Notify all players (30s timer)
    ↓
Players Accept/Decline
    ↓
If all accept: Match Ready!
If timeout: Cancel + Requeue
```

---

## ✅ Success Criteria

After Phase 2 implementation, you should be able to:

1. **Queue Lobby**
   - Select maps (min 5)
   - Join queue
   - See queue position

2. **Find Match**
   - System finds 10 compatible players
   - Teams are balanced by ELO
   - Match confirmation sent

3. **Accept Match**
   - 30-second timer displayed
   - Accept/Decline options
   - See acceptance count (X/10)

4. **Match Created**
   - All players accept
   - Match details provided
   - Ready for veto phase (Phase 3)

---

## 🧪 Testing

After implementation, test with:

```bash
# Test queue operations
cd server
python test_queue_operations.py

# Test matchmaking
python test_matchmaking.py

# Full integration test
python test_full_match_flow.py
```

---

## 📝 Next Steps

1. ✅ Redis installed and tested
2. 🔄 Implement QueueManager
3. 🔄 Implement Matchmaker
4. 🔄 Implement MatchConfirmationManager
5. 🔄 Update Consumer with queue events
6. 🔄 Setup Celery tasks
7. 🧪 Test Phase 2

---

**Estimated Time:** 2-3 hours of implementation  
**Complexity:** Medium (Redis + async operations)  
**Prerequisites:** Phase 1 complete ✅, Redis running ✅

