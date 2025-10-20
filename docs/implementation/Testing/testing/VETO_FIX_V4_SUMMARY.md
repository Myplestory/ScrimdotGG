# V4 Bot Veto System - Fixes Applied

## 🎯 Overview
Applied critical fixes to `test_queue_with_bots_v4.py` to ensure bots properly participate in the map veto phase.

---

## ✅ Fixes Applied

### **Fix #1: Auto-Request Match Data After Confirmation**
**Location:** Lines 137-144
**Problem:** Bots weren't joining the match WebSocket group, so they never received veto updates.

**Before:**
```python
elif event == 'match_confirmed':
    self.current_match_id = payload.get('match_id')
    logger.info(f"✅ Bot {self.bot_alias} match confirmed!")
```

**After:**
```python
elif event == 'match_confirmed':
    self.current_match_id = payload.get('match_id')
    logger.info(f"✅ Bot {self.bot_alias} match confirmed!")
    
    # Request match data to join match group and receive veto updates
    await self._send_message('get_match_data', {
        'match_id': self.current_match_id
    })
```

**Impact:** 
- ✅ Bots now join the match WebSocket group
- ✅ Bots receive `match_data` with initial veto state
- ✅ Bots can receive subsequent `veto_update` events

---

### **Fix #2: Handle Both Field Names for Veto Turn**
**Location:** Lines 280-288
**Problem:** Server uses different field names in different events (`veto_turn` vs `next_turn`).

**Before:**
```python
self.current_turn = payload.get('veto_turn')
```

**After:**
```python
# Handle both 'veto_turn' (from match_data) and 'next_turn' (from veto_update)
self.current_turn = payload.get('veto_turn') or payload.get('next_turn')
```

**Impact:**
- ✅ Bots correctly track whose turn it is in both initial state and updates
- ✅ Turn detection works for both event types

---

### **Fix #3: Simplified Veto Payload**
**Location:** Lines 331-335
**Problem:** Bots were sending an unused `action_type` field that the server ignores.

**Before:**
```python
await self._send_message('veto_map', {
    'match_id': self.current_match_id,
    'map_name': map_to_veto,
    'action_type': 'ban'  # ❌ Server doesn't use this
})
```

**After:**
```python
# Send veto action (server accepts both 'map' and 'map_name')
await self._send_message('veto_map', {
    'match_id': self.current_match_id,
    'map_name': map_to_veto
})
```

**Impact:**
- ✅ Cleaner payload matching server expectations
- ✅ No unnecessary fields sent
- ✅ Still uses `map_name` which server accepts

---

## 🎮 How It Works Now

### **Complete Veto Flow:**

1. **Match Confirmation** (Lines 137-144)
   - Bot receives `match_confirmed` event
   - Bot immediately requests `get_match_data`
   - Server adds bot to `match_{match_id}` group

2. **Initial Veto State** (Lines 232-273)
   - Bot receives `match_data` event
   - Bot parses team assignments and captain status
   - Bot extracts initial `veto_turn`, `remaining_maps`, `vetoed_maps`
   - If bot is captain and it's their turn → make veto decision

3. **Veto Decision** (Lines 305-335)
   - Bot chooses map based on strategy (random/aggressive/strategic)
   - Bot adds realistic delay (1-3 seconds)
   - Bot sends `veto_map` with `match_id` and `map_name`

4. **Veto Update** (Lines 280-295)
   - Bot receives `veto_update` event after each veto
   - Bot updates `remaining_maps`, `vetoed_maps`, `next_turn`
   - If bot is captain and it's their turn → make next veto decision

5. **Veto Complete** (Lines 292-303)
   - Bot receives `veto_complete` event
   - Bot logs final map
   - Bot resets veto state

---

## 🧪 Testing

### **Test the Fixed Script:**

```bash
# Terminal 1: Start Django server
cd server
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application

# Terminal 2: Start Celery worker
cd server
pipenv run celery -A scrimgg worker --loglevel=info --pool=gevent

# Terminal 3: Start Celery beat
cd server
pipenv run celery -A scrimgg beat --loglevel=info

# Terminal 4: Run bot test
cd server
pipenv run python testing/test_queue_with_bots_v4.py
```

### **Expected Behavior:**

1. ✅ 9 bots create lobbies and join queue
2. ✅ User joins queue via Electron client (10th player)
3. ✅ Matchmaker finds match after ~30 seconds
4. ✅ All 9 bots auto-accept immediately
5. ✅ User accepts via client
6. ✅ Match confirmed → redirect to match page
7. ✅ **Veto phase starts automatically**
8. ✅ **Captain bots take turns vetoing maps**
9. ✅ **Each veto is logged with bot alias and strategy**
10. ✅ **Final map is selected after veto complete**

---

## 📊 Verification Checklist

After running the test, verify these logs:

### **Match Confirmation:**
```
✅ Bot QueueBot0 match confirmed! Match ID: a3f4b2e1
📤 Bot QueueBot0 sent: get_match_data
```

### **Match Data Received:**
```
🎮 Bot QueueBot0 received match data
🎮 Bot QueueBot0 veto state initialized:
   Is captain: True
   My team: team_a
   Current turn: team_a
   Available maps: ['Ascent', 'Bind', 'Breeze', 'Haven', 'Icebox', 'Lotus', 'Pearl']
   Veto strategy: aggressive
```

### **Veto Action:**
```
🗺️ Bot QueueBot0 vetoing map: Haven (strategy: aggressive)
📤 Bot QueueBot0 sent: veto_map
```

### **Veto Update:**
```
🎮 Bot QueueBot0 received veto update
   Remaining maps: ['Ascent', 'Bind', 'Breeze', 'Icebox', 'Lotus', 'Pearl']
   Vetoed maps: ['Haven']
   Current turn: team_b
```

### **Veto Complete:**
```
🎮 Bot QueueBot0 veto phase completed!
   Final map: Breeze
```

---

## 🐛 Troubleshooting

### **Bots don't receive veto updates:**
- ❌ Check that bots are requesting `get_match_data` after match confirmation
- ❌ Verify Django server is running and WebSocket connections are stable
- ❌ Check Celery logs for errors

### **Bots don't veto when it's their turn:**
- ❌ Verify captain detection logic (`is_captain` and `my_team`)
- ❌ Check that `current_turn` matches `my_team`
- ❌ Ensure `available_maps` list is not empty

### **Veto doesn't progress:**
- ❌ Check server logs for `process_veto` errors
- ❌ Verify `MatchManager.process_veto` is implemented
- ❌ Check that map names match exactly (case-sensitive)

---

## 🎉 Success Criteria

✅ All 9 bots connect and queue successfully  
✅ Match found and all bots auto-accept  
✅ Bots receive match data and join match group  
✅ Captain bots identify themselves correctly  
✅ Captain bots veto maps when it's their turn  
✅ Non-captain bots wait patiently  
✅ Veto phase completes with final map selected  
✅ All bots remain connected throughout the process  

---

**Status:** ✅ READY FOR TESTING

**Next Steps:** 
1. Run the test script with the fixes
2. Monitor bot logs for veto actions
3. Verify veto completes successfully
4. Test with your live client as the 10th player

---

*Fixes applied: October 13, 2025*  
*Script: server/testing/test_queue_with_bots_v4.py*
