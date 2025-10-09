# Quick Start - WebSocket Refactor

## 🚀 Installation & Cleanup

### 1. Clean Up Unused Packages

```bash
cd Scrim.GG_Client/scrimgg/frontend/scrimgg
npm uninstall axios socket.io-client websocket
```

### 2. Verify Dependencies

```bash
# Should show no errors
npm install
```

---

## 🏃 Running the Application

### Terminal 1: Backend

```bash
cd Scrim.GG_Client/scrimgg/backend
pipenv shell
python bootstrap.py
```

**Expected output:**
```
============================================================
🚀 Starting Scrim.GG Client Service
============================================================
📡 WebSocket server: ws://localhost:5888/ws
🎮 Ready to connect to Valorant
============================================================
 * Running on http://0.0.0.0:5888
```

### Terminal 2: Frontend

```bash
cd Scrim.GG_Client/scrimgg/frontend/scrimgg
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view scrimgg in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

---

## ✅ Testing Checklist

### Connection Test
- [ ] Open app, login page shows "🟢 Connected to local backend"
- [ ] Open browser console (F12), should see: `✅ WebSocket connected to local backend`

### Authentication Test
- [ ] Start Valorant
- [ ] Click "Authenticate" button
- [ ] Should see loading spinner, then redirect to landing page
- [ ] Backend console shows: `🔐 Authenticating with Valorant client...`

### Lobby Test
- [ ] Navigate to lobby
- [ ] Lobby auto-creates on load
- [ ] Your player appears in a slot
- [ ] Console shows: `📥 Received: lobby_created`

### Chat Test
- [ ] Type "test message" in chat
- [ ] Press Enter
- [ ] Message appears instantly with your name and timestamp

### Queue Test
- [ ] Select at least one map
- [ ] Select at least one server
- [ ] Click "Q" button
- [ ] Button changes to "In Queue..."
- [ ] Status shows "🔍 In Queue..."

---

## 🐛 If Something Doesn't Work

### Backend not connecting?
```bash
# Check if port 5888 is in use
netstat -ano | findstr :5888

# Kill process if needed
taskkill /PID <PID> /F

# Restart backend
python bootstrap.py
```

### Frontend not connecting?
```bash
# Clear React cache
npm run clean  # or manually delete node_modules/.cache

# Reinstall
npm install

# Restart
npm start
```

### Valorant not detected?
1. Close backend
2. Start Valorant
3. Wait for it to fully load
4. Start backend
5. Try authenticate again

---

## 📊 Performance Check

### Check Resource Usage

**Task Manager (Windows):**
- Scrim.GG Client: ~30-50MB RAM, <1% CPU idle
- Backend (python): ~50-70MB RAM, <1% CPU idle

**With Valorant running:**
- Should not notice any performance impact
- FPS drop < 5 frames (negligible)

### Check Latency

Open browser console and watch for:
```
📤 Sent: lobby_chat
📥 Received: lobby_message
```

Time between these should be < 20ms.

---

## 🎯 What Changed (Quick Reference)

| File | Change |
|------|--------|
| `src/contexts/WebSocketContext.jsx` | NEW - WebSocket hook |
| `src/index.js` | Added WebSocketProvider |
| `src/pages/login.jsx` | Uses WebSocket for auth |
| `src/components/lobby/lobby.jsx` | Uses WebSocket for all actions |
| `src/components/home/home.jsx` | Uses WebSocket for player data |
| `backend/bootstrap.py` | Rewritten for WebSocket |

---

## 💡 Common Patterns

### Get Data
```javascript
const { playerData, lobbyData, matchData } = useWebSocket();
```

### Send Action
```javascript
const { api } = useWebSocket();
api.createLobby();
api.queueLobby(['Ascent'], ['NA-East']);
```

### Listen to Events
```javascript
const { on } = useWebSocket();

useEffect(() => {
  const unsubscribe = on('custom_event', (payload) => {
    // Handle event
  });
  return unsubscribe;
}, [on]);
```

---

## 🎉 You're All Set!

If everything above works, your client is successfully refactored to use WebSocket!

**Next Steps:**
1. Read `IMPLEMENTATION_ROADMAP.md` for Phase 2 (Game Monitor)
2. Read `ARCHITECTURE_IMPROVEMENTS.md` for full system design
3. Start implementing advanced features!

