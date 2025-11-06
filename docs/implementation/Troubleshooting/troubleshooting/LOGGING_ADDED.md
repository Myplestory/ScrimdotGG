# Enhanced Logging for Matchmaking Debugging

## ✅ What Was Added

Enhanced logging throughout the matchmaking flow with emojis and clear structure for easier debugging.

---

## 📊 **Logging Output You'll Now See**

### **When Matchmaking Runs (Every 10 seconds):**

```
======================================================================
🔄 PERIODIC MATCHMAKING STARTED
======================================================================
📊 Queue Status: 2 lobbies, 10 players
🎯 Running MMR-based matchmaker (MatchmakerV2)...
✅ Matchmaking completed: 1 matches found
🎮 Processing 1 match(es)...
📋 Match 1/1:
   Match data keys: ['lobby1', 'lobby2', 'team_a', 'team_b', 'map_pool', 'server_pool', 'timeout_seconds']
   Lobby 1: 5 players
   Lobby 2: 5 players
   Creating match confirmation...
   ✅ Created confirmation: a3f4b2e1...
   Using lobby1/lobby2 format: ['uuid-1', 'uuid-2']
   📢 Notifying 2 lobbies...
   📨 Sending to lobby 1/2: uuid-1
   📨 Sending to lobby 2/2: uuid-2
   ✅ All notifications sent for match a3f4b2e1
🎉 MATCHMAKING SUCCESS: 1 confirmations created
======================================================================
```

---

### **When No Matches Found:**

```
======================================================================
🔄 PERIODIC MATCHMAKING STARTED
======================================================================
📊 Queue Status: 1 lobbies, 5 players
⏸️  Not enough lobbies in queue for matchmaking (need 2+)
```

Or:

```
======================================================================
🔄 PERIODIC MATCHMAKING STARTED
======================================================================
📊 Queue Status: 2 lobbies, 10 players
🎯 Running MMR-based matchmaker (MatchmakerV2)...
✅ Matchmaking completed: 0 matches found
⚠️  No matches found this cycle
======================================================================
```

---

### **When Errors Occur:**

```
❌ ERROR in periodic matchmaking: Error message here
Full traceback...
======================================================================
```

---

### **Notification Details:**

```
Attempting to notify lobby uuid-123 about match a3f4b2e1
Channel layer obtained, sending to group lobby_uuid-123
Sent match found notification to lobby uuid-123
```

---

## 🔍 **What Each Log Tells You**

| Log Line | Meaning |
|----------|---------|
| `🔄 PERIODIC MATCHMAKING STARTED` | Matchmaker cycle starting |
| `📊 Queue Status: X lobbies, Y players` | Current queue state |
| `⏸️  Not enough lobbies` | Need more players |
| `🎯 Running MMR-based matchmaker` | Starting match algorithm |
| `✅ Matchmaking completed: X matches found` | Algorithm finished |
| `🎮 Processing X match(es)` | Creating confirmations |
| `📋 Match 1/1:` | Details for each match |
| `✅ Created confirmation:` | Match confirmation created |
| `📢 Notifying X lobbies` | Sending WebSocket notifications |
| `📨 Sending to lobby` | Individual notification sent |
| `✅ All notifications sent` | All players notified |
| `🎉 MATCHMAKING SUCCESS` | Cycle completed successfully |
| `⚠️  No matches found` | No compatible lobbies |
| `❌ ERROR` | Something went wrong |

---

## 🎯 **How to Debug**

### **Issue: Match not appearing in client**

Look for:
1. `🎮 Processing 1 match(es)` - Match found?
2. `✅ Created confirmation` - Confirmation created?
3. `📨 Sending to lobby` - Notifications sent?
4. `Attempting to notify lobby` - WebSocket working?
5. `Channel layer obtained` - Channel layer connected?

If any step is missing, that's where the issue is.

---

### **Issue: Bots not matching**

Look for:
1. `📊 Queue Status: X lobbies` - Are bots in queue?
2. `🎯 Running MMR-based matchmaker` - Is matchmaker running?
3. `✅ Matchmaking completed: 0 matches found` - Why no matches?

Check MatchmakerV2 logs for tolerance/MMR mismatch.

---

### **Issue: Notifications not reaching client**

Look for:
1. `Channel layer is None!` - Channel layer not configured
2. `Error sending match found notification` - WebSocket error
3. Check Daphne logs for WebSocket disconnections

---

## 📁 **Files Modified**

- `server/matchmaking/tasks.py` - Enhanced logging for matchmaking cycles
- `server/TESTING_COMMANDS.md` - Updated with correct queue flags
- `server/LOGGING_ADDED.md` - This documentation

---

## 🚀 **Next Steps**

1. **Restart Celery Worker** with debug logging and correct queues:
   ```powershell
   cd server
   pipenv run celery -A scrimgg worker --loglevel=debug --pool=gevent -Q celery,matchmaking,cleanup
   ```

2. **Watch the logs** as matchmaking runs every 10 seconds

3. **Queue bots** and see the entire flow logged clearly

4. **Debug issues** by following the log trail

---

**Your matchmaking flow is now fully instrumented for debugging!** 🔍

