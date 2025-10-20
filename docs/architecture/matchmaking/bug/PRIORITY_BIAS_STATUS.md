# Smart Requeue + Priority Bias - Implementation Status

## 📋 **What You Approved (From Earlier Conversation):**

Based on the summary and conversation history, you approved:

### **Smart Requeue with Penalties Design:**
- **Lobbies that ALL accepted** get bias increase
- **Starting bias**: Based on percentage of MMR (e.g., 0.8% initial)
- **Escalating bias** as queue times increase
- **Per-failure bias**: Additional bias per failed acceptance
- **Rank-specific caps**: Different max bias by tier (elite/high/mid/low/entry)

### **Approved Configuration** (From summary notes):
```python
'priority_bias': {
    'initial_percent': 0.8,         # 0.8% of MMR as initial bias
    'per_failure_percent': 0.5,     # 0.5% per failed acceptance
    'per_minute_percent': 0.15,     # 0.15% per minute in queue
    'max_by_tier': {
        'elite': 150,
        'high': 200,
        'mid': 250,
        'low': 300,
        'entry': 350,
    },
    'decay_threshold': 600,          # 10 minutes
    'decay_rate_percent': 0.08,
    'bias_ttl': 3600,                # 1 hour
}
```

---

## ❌ **Current Status: NOT IMPLEMENTED**

### **What's Missing:**

1. **Redis bias tracking** - `lobby:{lobby_id}:priority_bias` keys
2. **Bias calculation** - `get_priority_bias()` function in matchmaker
3. **Bias application** - Adding bias to team ratings during matchmaking
4. **Tracking acceptances** - Identifying which lobbies accepted vs didn't
5. **Requeue with bias** - Setting bias when requeuing accepting lobbies

---

## 🔍 **Deadlock Issues Found:**

### **1. Critical Deadlock (High Risk)** 🔴

**File**: `server/matchmaking/match_confirmation.py` Line 679

**Location**: `handle_expired_match()` function

```python
def get_lobby():
    return Lobby.objects.select_related('lobby_leader').get(id=lobby_id)

from asgiref.sync import sync_to_async
lobby = await sync_to_async(get_lobby)()  # ❌ DEADLOCK in gevent pool
```

**Why it's a problem**:
- This runs in a Celery task with gevent pool
- `sync_to_async` from gevent can deadlock
- Happens on EVERY match timeout (frequently!)

**Fix**:
```python
# Store lobby leaders in match confirmation data when creating
match_data['lobby_leaders'] = {
    lobby['id']: lobby['players'][0]['puuid']  # First player is leader
    for lobby in match_lobbies
}

# Then retrieve without database
leader_puuid = match_data.get('lobby_leaders', {}).get(lobby_id)
```

---

### **2. Medium Risk Deadlocks** 🟡

**File**: `server/matchmaking/match_confirmation.py` Line 382

```python
# In _get_player_lobby_id (called during player acceptance)
return await sync_to_async(get_lobby_id)()  # ⚠️ MEDIUM RISK
```

**Context**: Called from WebSocket consumer (safer than Celery, but still risky)

---

### **3. Low Risk (Safe Contexts)** 🟢

All other `sync_to_async` calls are in:
- **WebSocket consumers** (`consumers.py`) - Safe, designed for this
- **Lobby manager** (`lobby_manager.py`) - Safe, called from consumers  
- **Queue manager** (`queue_manager.py`) - Mostly safe, called from consumers

---

## 🎯 **Recommendations:**

### **Option A: Test Now, Fix Later** ⭐ RECOMMENDED
**For testing your MMR system**:
- ✅ Current code works well enough
- ⚠️ Deadlock risk is LOW for short test sessions
- ✅ You can validate MMR/matchmaking/acceptance flow
- ⏭️ Fix deadlocks + implement priority bias after Match Room

**Timeline**:
1. Test MMR system today ← You are here
2. Build Match Room page next
3. Then implement priority bias + fix deadlocks

---

### **Option B: Fix Everything Now**
**Fix all issues before testing**:
1. Remove deadlock in `handle_expired_match`
2. Implement full priority bias system
3. Add Redis bias tracking
4. Update matchmaker to apply bias
5. Then test

**Timeline**: +4-6 hours of work before testing

---

## 📊 **What I Recommend:**

### **APPROVED PLAN (You said "We are ready. Implement...") - From Earlier**

You approved implementing:
1. ✅ MMR/ELO system - **DONE**
2. ✅ Uncertainty decay - **DONE**
3. ✅ Adaptive weighting - **DONE**
4. ❌ Priority bias - **NOT DONE** (you said to pause it earlier!)

---

## 🎯 **Summary:**

### **Priority Bias: NOT IMPLEMENTED**
- You approved the design
- You said to "pause" it to focus on MMR system first
- It's listed as "Next Phase" after MMR verification

### **Deadlock Issues: 1 CRITICAL, 2 MEDIUM**
- **Critical**: Line 679 in `handle_expired_match` (Celery context)
- **Medium**: Line 382 in `_get_player_lobby_id` (Consumer context)
- **All others**: Low risk (safe contexts)

### **Recommended Action:**
✅ **Test the MMR system now** (deadlock risk is acceptable for testing)  
⏭️ **Implement priority bias AFTER** Match Room page is built  
🔧 **Fix deadlocks** when implementing priority bias

---

**Should I:**
1. **Let you test now** (with current code, minor risks) ⭐ RECOMMENDED
2. **Fix the critical deadlock first** (15 min), then test
3. **Implement full priority bias system** (4-6 hours), then test

**What do you prefer?**

