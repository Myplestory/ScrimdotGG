# Live Client Testing Guide

## 🎯 **Testing Phase 3 with Your Development Client**

This guide shows you how to test the complete match flow with just YOUR client + 9 simulated bot players.

---

## ⚠️ **Current Issue: "Not authenticated"**

### **What's Happening:**
Your Electron client is trying to join queue but getting "Not authenticated" error.

### **Root Cause:**
The local backend (bootstrap.py) requires authentication before allowing queue operations.

### **Solution:**
Make sure you've completed the authentication flow in your client.

---

## 🔧 **Fix Authentication Issue**

### **Option 1: Re-authenticate (Recommended)**

1. **Make sure Valorant is RUNNING** (not just Riot Client)
   - Launch Valorant game
   - Wait for it to fully load

2. **In your Electron app:**
   - Go to login/authentication screen
   - Select correct region (na, eu, etc.)
   - Click "Authenticate" or "Login"
   - Wait for success message

3. **Verify in Backend Console:**
   Look for:
   ```
   [AUTH] Authenticating with Valorant client...
   [AUTH] User authenticated, heartbeat continues until in-game
   ```

4. **Verify in Frontend Console (F12):**
   ```javascript
   Authenticated: true
   System Status: { authenticated: true, valorant: { status: 'running' } }
   ```

5. **Now try joining queue again**

### **Option 2: Check WebSocket Connection**

If re-authentication doesn't work, check:

1. **Backend is running:**
   ```powershell
   cd client/backend
   pipenv run python bootstrap.py
   ```
   Should show: `WebSocket server: ws://localhost:5888/ws`

2. **Frontend connected:**
   Browser console should show:
   ```
   🔌 Connecting to local backend WebSocket...
   ✅ WebSocket connected to local backend
   ```

3. **Authentication event sent:**
   Should show:
   ```
   📤 Sent: authenticate {}
   📥 Received: authentication_success
   ```

---

## 🧪 **Testing with Bots - Complete Guide**

Once authentication is fixed, follow these steps:

### **Step 1: Start All Services**

```powershell
# Terminal 1: Redis (should already be running)
docker ps | findstr redis-scrimgg

# Terminal 2: Django/Daphne Server (already running)
cd server
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application

# Terminal 3: Celery Worker
cd server
pipenv run celery -A scrimgg worker --loglevel=info

# Terminal 4: Celery Beat
cd server
pipenv run celery -A scrimgg beat --loglevel=info

# Terminal 5: Client Backend
cd client/backend
pipenv run python bootstrap.py

# Terminal 6: Client Frontend
cd client/frontend
npm start
```

### **Step 2: Authenticate in Your Client**

1. Open Electron app (should auto-open at http://localhost:3000)
2. Go to login page
3. Select region: **na** (or your actual region)
4. Click authenticate
5. Wait for success

### **Step 3: Run Bot Queue Script**

```powershell
# New terminal
cd server
pipenv run python test_queue_with_bots.py
```

**What it does:**
- Finds your player (ELO: 6400)
- Creates 9 bots with similar ELO (6350-6450)
- Puts all 9 bots in queue
- Waits for YOU to join

### **Step 4: Join Queue in Your Client**

1. Navigate to PUG Queue page
2. Select at least 5 maps
3. Click "FIND MATCH"
4. Watch script detect you joined!

### **Step 5: Wait for Match**

- Matchmaker runs every 30 seconds
- When 10 players in queue, it finds a match
- You receive "match_found" event
- Accept button appears

### **Step 6: Accept Match**

- Click "Accept"
- Bot players auto-accept (simulated)
- When all 10 accept → match starts

### **Step 7: Match Starts**

If you're the constructor (highest ELO):
- Your client automatically creates Valorant custom game
- Bots "join" (simulated)
- Match goes live

If you're not constructor:
- You receive join instruction
- Your client joins the custom game
- Match goes live

---

## 🎮 **What You'll Experience**

### **In Your Electron Client:**

**1. Queue Phase:**
```
Status: In Queue
Time: 0:15... 0:30... 0:45...
Players in queue: 10
```

**2. Match Found:**
```
[Popup] Match Found!
Time remaining: 30s
Average ELO: 6400
Accept | Decline
```

**3. Match Starting:**
```
[Notification] Match starting...
Creating custom game... (if you're constructor)
OR
Joining custom game... (if you're not)
```

**4. Match Live:**
```
[Match Room]
Team A: 0 - 0 Team B
Round: 1/24
```

---

## 📊 **Test Scripts Available**

### **1. Quick Match Test** - `test_quick_match_with_me.py`
Creates instant match without queue (for direct testing)
```powershell
pipenv run python test_quick_match_with_me.py
```

### **2. Queue with Bots** - `test_queue_with_bots.py` ⭐ RECOMMENDED
Puts 9 bots in queue, you join via client
```powershell
pipenv run python test_queue_with_bots.py
```

### **3. Full Simulation** - `test_match_flow_simulation.py`
Complete automated test (no client needed)
```powershell
pipenv run python test_match_flow_simulation.py
```

---

## 🐛 **Troubleshooting**

### **Error: "Not authenticated"**

**Check:**
1. Valorant is running?
2. You clicked authenticate in client?
3. Backend console shows authentication success?
4. Frontend shows `authenticated: true`?

**Fix:**
- Re-authenticate in your client
- Check Valorant is actually running
- Restart backend if needed

### **Error: "WebSocket not connected"**

**Check:**
1. Backend running on port 5888?
2. Frontend connected to `ws://localhost:5888/ws`?

**Fix:**
- Restart backend
- Refresh frontend
- Check for port conflicts

### **Error: No match found**

**Check:**
1. Celery beat running? (schedules matchmaking every 30s)
2. Celery worker running? (executes matchmaking)
3. 10+ players in queue?

**Fix:**
- Start Celery services
- Wait 30 seconds for next matchmaking cycle
- Check queue status: see if bots are actually queued

---

## 📝 **Authentication Verification Commands**

### **Check Your Player Exists:**
```powershell
pipenv run python manage.py shell
```
```python
from scrimgg.models import Player
you = Player.objects.exclude(puuid__startswith='bot-').exclude(puuid__startswith='sim-').latest('id')
print(f"Name: {you.alias}")
print(f"PUUID: {you.puuid}")
print(f"ELO: {you.elo}")
```

### **Check If You're in a Lobby:**
```python
from scrimgg.models import Lobby
lobby = Lobby.objects.filter(players=you, is_active=True).first()
if lobby:
    print(f"In lobby: {lobby.id}")
else:
    print("Not in lobby - create one first!")
```

### **Check Queue Status:**
```python
import asyncio
from matchmaking.queue_manager import QueueManager

status = asyncio.run(QueueManager.get_queue_status('pug'))
print(f"Players in queue: {status.get('players_in_queue', 0)}")
```

---

## ✅ **Step-by-Step Success Path**

1. ✅ Start all services (Django, Celery, Redis, Backend, Frontend)
2. ✅ Launch Valorant game
3. ✅ Open Electron app
4. ✅ **Authenticate** in login screen
5. ✅ Verify authentication success (check console)
6. ✅ Run `test_queue_with_bots.py`
7. ✅ Join queue in your client
8. ✅ Wait for match (30s max)
9. ✅ Accept match
10. ✅ Match starts!

---

## 🚀 **Quick Commands**

```powershell
# Run bot queue test
cd server
pipenv run python test_queue_with_bots.py

# Check queue status
pipenv run python -c "import asyncio, os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings'); django.setup(); from matchmaking.queue_manager import QueueManager; print(asyncio.run(QueueManager.get_queue_status('pug')))"

# Clean up bots
pipenv run python manage.py shell
>>> from scrimgg.models import Player, Lobby
>>> Lobby.objects.filter(lobby_leader__puuid__startswith='queuebot-').delete()
>>> Player.objects.filter(puuid__startswith='queuebot-').delete()
```

---

**Follow the authentication fix first, then run the bot queue test!** 🎯

