# Veto Frontend Communication Fix

## 🐛 **Root Cause Analysis**

The bot vetoes were working on the server side but not reaching the frontend due to **three critical issues** in the communication chain:

### **Issue #1: Missing Pugsocket Property Exposure**
**Location:** `client/backend/app/services/valorant.py`

**Problem:**
```python
# ConnectionManager was trying to access:
data = getattr(valorant_service.api, attr_name, None)  # ❌ Wrong object
```

**Root Cause:** The `ValorantService` didn't expose the `pugsocket` property, so pending veto events were never accessible.

**Fix Applied:**
```python
class ValorantService:
    def __init__(self):
        self.api = ValorantAPI()
    
    @property
    def pugsocket(self):
        """Expose pugsocket for pending events."""
        return self.api.pugsocket  # ✅ Now accessible
```

---

### **Issue #2: Wrong Object Access in ConnectionManager**
**Location:** `client/backend/app/sockets/manager.py:138`

**Problem:**
```python
# Was accessing from api instead of pugsocket
data = getattr(valorant_service.api, attr_name, None)  # ❌ Wrong path
```

**Root Cause:** Pending veto events are stored on the `pugsocket` object, not the `api` object.

**Fix Applied:**
```python
# Access pending events from pugsocket, not api
data = getattr(valorant_service.pugsocket, attr_name, None)  # ✅ Correct path
if data:
    setattr(valorant_service.pugsocket, attr_name, None)  # ✅ Clear from pugsocket
```

---

### **Issue #3: Missing Frontend Event Handlers**
**Location:** `client/frontend/src/contexts/WebSocketContext.jsx`

**Problem:** The frontend had no handlers for veto events:
- ❌ No `match_data` handler
- ❌ No `veto_update` handler  
- ❌ No `veto_complete` handler

**Root Cause:** Frontend was never updated to handle the new veto events.

**Fix Applied:**
```javascript
case 'match_data':
  console.log('📥 [FRONTEND] Received match data:', payload);
  setMatchData(payload);
  break;
  
case 'veto_update':
  console.log('📥 [FRONTEND] Received veto update:', payload);
  setMatchData(prev => ({
    ...prev,
    veto_state: {
      ...prev?.veto_state,
      ...payload,
      last_update: Date.now()
    }
  }));
  break;
  
case 'veto_complete':
  console.log('📥 [FRONTEND] Veto phase completed:', payload);
  setMatchData(prev => ({
    ...prev,
    veto_state: {
      ...prev?.veto_state,
      completed: true,
      final_map: payload.final_map
    }
  }));
  break;
```

---

## 🔄 **Complete Communication Flow (Fixed)**

### **Before Fixes:**
```
Django Server → Bot Veto → Django WebSocket
     ↓
PugSocketClient (Django) → Receives veto_update
     ↓
Stores in _pending_veto_update_data
     ↓
ConnectionManager._drain_pending_events() → ❌ Can't access pugsocket
     ↓
Frontend → ❌ No veto event handlers
     ↓
UI shows no veto updates
```

### **After Fixes:**
```
Django Server → Bot Veto → Django WebSocket
     ↓
PugSocketClient (Django) → Receives veto_update
     ↓
Stores in _pending_veto_update_data ✅
     ↓
ConnectionManager._drain_pending_events() → ✅ Accesses pugsocket correctly
     ↓
Broadcasts veto_update to frontend ✅
     ↓
Frontend → ✅ Handles veto_update event
     ↓
UI updates with veto information ✅
```

---

## 🧪 **Testing the Fix**

### **Expected Log Flow:**

**1. Django Server (Working):**
```
Map Icebox vetoed by team_a in match 7c1a0142...
Map vetoed event received: {'type': 'map_vetoed'...}
```

**2. Client Backend (Now Working):**
```
[PUGAPI] Received message: {'event': 'veto_update'...}
[VETO UPDATE] Received veto update: {...}
[HEARTBEAT] Broadcasted veto_update
```

**3. Frontend (Now Working):**
```
📥 [FRONTEND] Received veto update: {
  match_id: "7c1a0142...",
  map_name: "Icebox",
  vetoed_by: "team_a",
  next_turn: "team_b",
  remaining_maps: ["Lotus", "Pearl", "Breeze", "Ascent", "Haven", "Bind"]
}
```

### **Expected UI Changes:**

**Before:** 
- ❌ Maps show no veto status
- ❌ No indication of whose turn it is
- ❌ No visual feedback of veto actions

**After:**
- ✅ Vetoed maps are visually marked (greyed out/crossed out)
- ✅ Turn indicator shows current captain
- ✅ Real-time updates as bots veto maps
- ✅ Final map displayed when veto complete

---

## 📊 **Files Modified**

### **Backend Fixes:**
1. **`client/backend/app/services/valorant.py`**
   - Added `pugsocket` property to expose pending events

2. **`client/backend/app/sockets/manager.py`**
   - Fixed `_drain_pending_events()` to access `pugsocket` instead of `api`

### **Frontend Fixes:**
3. **`client/frontend/src/contexts/WebSocketContext.jsx`**
   - Added `match_data` event handler
   - Added `veto_update` event handler
   - Added `veto_complete` event handler

---

## 🎯 **Verification Checklist**

After applying fixes, verify:

- [ ] **Backend logs show:** `[HEARTBEAT] Broadcasted veto_update`
- [ ] **Frontend logs show:** `📥 [FRONTEND] Received veto update:`
- [ ] **UI updates in real-time** as bots veto maps
- [ ] **Vetoed maps are visually marked** (greyed out/crossed out)
- [ ] **Turn indicator updates** to show current captain
- [ ] **Final map is displayed** when veto phase completes
- [ ] **No console errors** in browser DevTools

---

## 🚀 **Next Steps**

1. **Test the fixes** by running the bot script and observing the UI
2. **Verify veto flow** works end-to-end
3. **Check UI components** that display veto information are working
4. **Test with real user** as captain to ensure manual veto works too

---

## 🔍 **Debugging Tips**

If veto updates still don't appear:

1. **Check backend logs** for `[HEARTBEAT] Broadcasted veto_update`
2. **Check frontend console** for `📥 [FRONTEND] Received veto update:`
3. **Verify WebSocket connection** is stable
4. **Check browser DevTools Network tab** for WebSocket messages

---

**Status:** ✅ **READY FOR TESTING**

The communication chain is now complete - bot vetoes should reach the frontend and update the UI in real-time!

---

*Fixes applied: October 13, 2025*  
*Issue: Bot vetoes not reaching frontend*  
*Root cause: Missing pugsocket exposure + missing frontend handlers*
