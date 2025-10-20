# Client Authentication Debug Guide

## ❌ Error: "Not authenticated"

### **What This Means**
Your Electron frontend is connected to the local backend (port 5888), but the backend doesn't think you're authenticated yet.

---

## 🔍 **Authentication Flow**

```
Electron Frontend (React)
    ↓ (WebSocket port 5888)
Local Backend (bootstrap.py)
    ↓ (Authenticate with Valorant)
ValClient API
    ↓ (Login to Django)
Django Server (port 8000)
```

### **Required Steps:**
1. ✅ Frontend connects to `ws://localhost:5888/ws`
2. ✅ Frontend sends `authenticate` event with region
3. ✅ Backend calls `valorant_api.login(region)`
4. ✅ ValClient activates and gets PUUID
5. ✅ Backend sets `client_states[client_id]['authenticated'] = True`
6. ✅ Backend connects to Django WebSocket
7. ✅ Now you can join queue

---

## 🐛 **Debugging Steps**

### **Step 1: Check Backend Console**

Look for these messages in your backend console:
```
[OK] Frontend WebSocket connected: {client_id}
[AUTH] Authenticating with Valorant client...
[AUTH] Using region: na
[AUTH] User authenticated, heartbeat continues until in-game
```

**If you see:** `[AUTH] User authenticated...`
- ✅ Authentication worked!

**If you DON'T see it:**
- ❌ Authentication never happened or failed

### **Step 2: Check Frontend Login Flow**

In your `login.jsx`, when you click login:
```jsx
api.authenticate({ region: selectedRegion });
```

This should trigger:
1. WebSocket sends `authenticate` event to backend
2. Backend authenticates with Valorant
3. Backend sends `authentication_success` event back
4. Frontend receives event and updates state

### **Step 3: Verify Authentication State**

Add this to your frontend console:
```javascript
// In browser console
console.log('Authenticated:', authenticated);
console.log('System Status:', systemStatus);
```

Should show:
```javascript
Authenticated: true
System Status: {
  backend_connected: true,
  valorant: { status: 'running', ... },
  authenticated: true
}
```

---

## 🔧 **Common Fixes**

### **Fix 1: Re-authenticate**

In your Electron app:
1. Close the app
2. Make sure Valorant is running
3. Restart your backend: `pipenv run python bootstrap.py`
4. Restart your frontend
5. Login again

### **Fix 2: Check Valorant Status**

Your backend checks if Valorant is running. If it's not:
```
status: 'riot_only'  // Riot Client running but not Valorant game
status: 'not_running'  // Nothing running
```

**Solution:** Launch Valorant game (not just Riot Client)

### **Fix 3: Region Mismatch**

If you selected wrong region:
```
Error: Region mismatch! You selected NA, but your Valorant client is in EU
```

**Solution:** Select the correct region in login screen

### **Fix 4: Manual Authentication Check**

Add logging to `handle_join_pug_queue`:
```python
# In bootstrap.py
async def handle_join_pug_queue(payload: dict, client_id: int, ws):
    print(f"[DEBUG] Client {client_id} authenticated: {client_states[client_id].get('authenticated', False)}")
    print(f"[DEBUG] Client states: {client_states[client_id]}")
    
    if not client_states[client_id]['authenticated']:
        await send_error(ws, "Not authenticated")
        return
```

---

## ✅ **Quick Fix Script**

Run this to verify your authentication state:

```powershell
# In your backend console, add this temporary debug
```

Or check the `client_states` dictionary in bootstrap.py logs.

---

## 🚀 **Testing Authentication**

### **Test 1: Check Backend Connection**
```javascript
// In browser console
console.log('Connected:', connected);
// Should be: true
```

### **Test 2: Check Authentication**
```javascript
console.log('Authenticated:', authenticated);
// Should be: true
```

### **Test 3: Check Player Data**
```javascript
console.log('Player Data:', playerData);
// Should show: { puuid: '...', alias: '...', elo: ... }
```

### **Test 4: Manually Trigger Authentication**
```javascript
api.authenticate({ region: 'na' });
// Watch backend console for authentication messages
```

---

## 🎯 **Recommended Solution**

The simplest fix for your current issue:

### **In Your Electron App:**

1. **Go to Login Screen**
2. **Select Your Region** (make sure it matches Valorant)
3. **Click Login/Authenticate Button**
4. **Wait for "Authentication Success"** message
5. **Then navigate to Queue page**
6. **Now "Find Match" should work**

### **Verify It Worked:**
- Browser console shows `Authenticated: true`
- Backend console shows `[AUTH] User authenticated...`
- System status indicator shows green/running

---

## 💡 **Alternative: Direct Django Queue Join**

If you want to bypass the local backend authentication for testing, you could:

1. Connect directly to Django WebSocket from frontend
2. Or use the legacy approach with modified endpoints

But the **proper solution** is to ensure authentication completes successfully.

---

## 📝 **Debug Checklist**

- [ ] Valorant game is running (not just Riot Client)
- [ ] Backend shows Valorant status: 'running'
- [ ] You clicked login/authenticate in your app
- [ ] Backend shows `[AUTH] User authenticated...`
- [ ] Frontend shows `Authenticated: true`
- [ ] Player data is loaded in frontend
- [ ] Then try joining queue again

---

**Once authenticated properly, the queue join will work and you'll be matched with the 9 bots!** 🎮

