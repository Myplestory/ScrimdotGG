# Testing Commands - MMR System with Bot Auto-Accept

## 🚀 Full Test Flow

### **Step 1: Start Server Stack** (3 terminals)

**Terminal 1 - Daphne (Django WebSocket Server):**
```powershell
cd server
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application
```

**Terminal 2 - Celery Worker (with correct queues):**
```powershell
cd server
pipenv run celery -A scrimgg worker --loglevel=debug --pool=gevent -Q celery,matchmaking,cleanup
```
⚠️ **Important**: The `-Q celery,matchmaking,cleanup` flag is required to listen to all task queues!

**Terminal 3 - Celery Beat (Matchmaker runs every 10s):**
```powershell
cd server
pipenv run celery -A scrimgg beat --loglevel=info
```

---

### **Step 2: Queue Bots with Auto-Accept** (Terminal 4)

```powershell
cd server
pipenv run python testing/test_queue_with_bots.py
```

**What this does**:
1. Creates 9 bots with MMR matching yours (~6170)
2. Puts all 9 bots in queue
3. **Starts bot auto-acceptor** (bots will auto-accept matches)
4. Waits for YOU to join queue
5. When match found, bots auto-accept
6. YOU accept in your client → Match ready!

**Keep this terminal running** - the bot auto-acceptor continues monitoring for new matches.

---

### **Step 3: Join Queue in Your Electron Client**

1. Open your Electron client
2. Select at least 5 maps
3. Click "FIND MATCH"
4. Wait ~30 seconds for matchmaker

---

### **Step 4: Accept Match**

When match found:
1. Modal appears in your client
2. Bots auto-accept (watch Terminal 4 logs)
3. **YOU click "Accept"**
4. Match ready! → Navigate to Match Room

---

## 📊 What to Watch For

### **Terminal 2 (Celery Worker) - Matchmaking Logs**

Look for these MMR system indicators:

```
[MATCHMAKER_V2] Finding matches using MMR...
[ADAPTIVE] Lobby abc123: Team Rating = 6180
  ├─ MMR: 6168, Display: 6493
  ├─ Weight: 85% MMR / 15% Display
  └─ State: converged

[TOLERANCE] MMR 6175, Tier: elite, Time: 30s
  └─ Tolerance: ±960

[MATCH_FOUND] Rating diff: 15, Tolerance: 960
  └─ Quality: EXCELLENT

[BALANCE] Team A MMR: 6170, Team B MMR: 6185
  └─ Difference: 15 (well balanced!)
```

---

### **Terminal 4 (Bot Auto-Acceptor) - Acceptance Logs**

```
[BOT_ACCEPTOR] Found match a3f4b2e1 with 9 bots
[BOT_ACCEPTOR] Bot queuebot-0 accepted [1/10]
[BOT_ACCEPTOR] Bot queuebot-1 accepted [2/10]
[BOT_ACCEPTOR] Bot queuebot-2 accepted [3/10]
...
[BOT_ACCEPTOR] Bot queuebot-8 accepted [9/10]
[BOT_ACCEPTOR] Waiting for user to accept... [9/10]
[BOT_ACCEPTOR] Match a3f4b2e1 fully accepted! All players ready.
```

---

## 🧪 Optional: Test MMR System First

Before live testing, verify calculations:

```powershell
cd server
pipenv run python testing/test_mmr_system.py
```

**Expected output**:
```
✅ Model defaults correct
✅ MMR/TrueSkill conversions working
✅ Uncertainty decay functioning
✅ Adaptive weighting calculating correctly
✅ Tolerance system working
✅ Match quality validation passing
✅ Player journey simulations complete
```

---

## 🎯 Success Criteria

You'll know everything is working when:

- ✅ Bots are created with **MMR values** (not just ELO)
- ✅ Celery logs show **adaptive weighting calculations**
- ✅ Matchmaker uses **MMR for team balance**
- ✅ Match found with **rating difference < 400**
- ✅ Bots **auto-accept** within 1-2 seconds
- ✅ After YOU accept → **match_ready event** fires
- ✅ Client navigates to **Match Room page**

---

## 🛠️ Troubleshooting

### Bots not auto-accepting?

Check Terminal 4 logs. If you see:
```
[BOT_ACCEPTOR] Error accepting for bot...
```

This means Redis or WebSocket connection issue. Restart Daphne (Terminal 1).

---

### Match not found after 2 minutes?

Check Celery Beat (Terminal 3) is running. Matchmaker runs every 30 seconds.

You should see:
```
Scheduler: Sending due task periodic-matchmaking (matchmaking.tasks.periodic_matchmaking)
```

---

### "No players in queue" in Celery logs?

The bots might have timed out. Rerun:
```powershell
cd server
pipenv run python testing/test_queue_with_bots.py
```

---

## 🧹 Cleanup Commands

### Remove all bots:
```powershell
cd server
pipenv run python testing/cleanup_bots_simple.py
```

### Check current queue:
```powershell
cd server
pipenv run python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings'); import django; django.setup(); from matchmaking.queue_manager import QueueManager; import asyncio; print(asyncio.run(QueueManager.get_queue_stats('pug')))"
```

---

## 📋 After Successful Match Acceptance

Once match is accepted and `match_ready` event fires, you'll need:

1. **Match Room page** - See `docs/MATCH_ROOM_SPECIFICATION.md`
2. **Navigation to `/match/:matchId`**
3. **Display teams, veto system, live stats**

**Next phase**: Implement Match Room! 🎮

