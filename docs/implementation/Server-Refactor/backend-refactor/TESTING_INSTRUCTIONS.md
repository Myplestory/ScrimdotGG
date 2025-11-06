# Testing the Refactored Backend with Electron

**Status:** Ready to Test  
**Date:** October 13, 2025

---

## ✅ What's Ready

The backend has been successfully refactored to a modular architecture:
- ✅ 32 event handlers registered
- ✅ Health endpoint working
- ✅ ConnectionManager managing state
- ✅ All critical systems preserved
- ✅ Electron main.js updated to use `run.py`

---

## 🚀 How to Test

### Step 1: Start the Backend

**Option A: Using the new entry point (recommended)**
```powershell
cd client/backend
pipenv run python run.py
```

**Option B: Let Electron start it automatically**
Just start Electron (Step 2) - it will launch the backend.

**Expected Output:**
```
[REGISTRY] Registered handler for 'connected'
[REGISTRY] Registered handler for 'get_status'
... (32 handlers registered)
============================================================
Starting Scrim.GG Client Service
============================================================
WebSocket server: ws://127.0.0.1:5888/ws
Health check: http://127.0.0.1:5888/health
Ready to connect to Valorant
============================================================
[HEARTBEAT] Starting...
```

---

### Step 2: Start Electron Frontend

```powershell
cd client/frontend
npm start
```

**What Electron will do:**
1. Kill any existing backend processes
2. Start `run.py` (the new refactored backend)
3. Wait 2 seconds
4. Create window and load React app
5. React app connects to `ws://localhost:5888/ws`

---

### Step 3: Verify Connection

**In Browser Dev Tools (F12):**
1. Go to **Network** tab
2. Filter by **WS** (WebSocket)
3. Click on the WebSocket connection
4. Check **Messages** tab

**Expected Messages:**
```json
// Received from backend on connect:
{
  "event": "connected",
  "payload": {
    "message": "Connected to Scrim.GG client service"
  }
}

// Then status updates every 3 seconds:
{
  "event": "status_update",
  "payload": {
    "backend_connected": true,
    "valorant": {
      "status": "not_running",
      "message": "..."
    },
    "authenticated": false
  }
}
```

---

## ✅ Testing Checklist

### Basic Connection
- [ ] Electron starts without errors
- [ ] Backend console shows 32 handlers registered
- [ ] Frontend connects to WebSocket
- [ ] "connected" event received
- [ ] Status updates appear

### Authentication (If Valorant Running)
- [ ] Click login/authenticate
- [ ] Backend shows "[AUTH] Authenticating..."
- [ ] Frontend receives `authentication_success`
- [ ] Player data appears

### Queue Operations
- [ ] Join queue
- [ ] Backend shows "[PUG QUEUE] Creating lobby..."
- [ ] Frontend receives `queue_joined`
- [ ] Leave queue works

### Match Flow (If Match Found)
- [ ] Match found notification appears
- [ ] Accept/decline buttons work
- [ ] Match progression works

---

## 🐛 Troubleshooting

### Backend doesn't start
**Check:**
```powershell
cd client/backend
pipenv run python -c "from app import create_app; create_app()"
```

**If ModuleNotFoundError:**
```powershell
pipenv install pydantic quart quart-cors
```

---

### WebSocket doesn't connect

**Check backend logs for:**
```
[CONN] Added client {id}
```

**If not appearing:**
1. Check browser console for WebSocket errors
2. Verify URL is `ws://localhost:5888/ws`
3. Check CORS settings in settings.py

---

### Events not working

**Check:**
1. Browser dev tools → Network → WS → Messages
2. Look for `"event": "error"` messages
3. Check backend console for handler errors

**Common issues:**
- Event name typo (check `registry` has the event)
- Payload structure changed
- Missing authentication

---

## 🔄 Rollback (If Needed)

If you encounter issues and want to revert:

### Quick Rollback:
```powershell
cd client/backend
Copy-Item bootstrap.py.backup -Destination bootstrap.py
```

### Update main.js:
Change line 63 back to:
```javascript
const backendPath = path.join(__dirname, '..', 'backend', 'bootstrap.py');
```

And lines 82, 87, 99 back to:
```javascript
pythonArgs = ['bootstrap.py'];  // or ['run', 'python', 'bootstrap.py']
```

Then restart Electron.

---

## 📊 What Changed vs What Stayed Same

### Changed (Organization Only):
- ✅ Code split into 20 modular files
- ✅ Entry point: `run.py` instead of `bootstrap.py`
- ✅ Better error messages
- ✅ Health endpoint added

### Stayed the Same (Logic):
- ✅ All 32 event handlers (identical logic)
- ✅ WebSocket protocol
- ✅ Django communication
- ✅ Valorant integration
- ✅ Heartbeat behavior
- ✅ State management structure

**Your frontend code needs ZERO changes!** Everything should work identically.

---

## 🎯 Expected Behavior

### On Startup:
1. Electron launches
2. Python backend starts (`run.py`)
3. 32 handlers register
4. Heartbeat starts
5. Window appears
6. React app loads
7. WebSocket connects
8. Status updates begin

### During Use:
- Same behavior as before
- Same events
- Same responses
- Just better organized code!

---

## ✅ Success Indicators

**If you see these, it's working:**
- ✅ Electron console: "✅ Python backend process started"
- ✅ Backend console: "32 event handlers" registered
- ✅ Backend console: "[HEARTBEAT] Starting..."
- ✅ Frontend console: WebSocket connected
- ✅ Browser dev tools: WS connection established
- ✅ UI: Status updates appearing

---

## 🎉 Ready to Test!

**Start with:**
```powershell
# Terminal 1: Frontend (Electron will start backend)
cd client/frontend
npm start
```

**Then verify:**
1. Window appears
2. WebSocket connects
3. Status updates work
4. Try authentication (if Valorant running)

**If everything works → Refactor is successful!** 🎉

---

**Good luck! The refactored backend is ready and waiting.** 🚀
