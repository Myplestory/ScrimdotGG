# Bot Veto Completion Fix

## ✅ **Fix Implemented: Wait for Veto Completion**

### **Changes Made**

**File:** `server/testing/test_queue_with_bots_v4.py`

### **1. Added State Tracking Flags** (Lines 60-62)
```python
self.match_found = False
self.match_confirmed = False  # NEW - Track when match is confirmed
self.veto_complete = False    # NEW - Track when veto phase completes
```

### **2. Set Flags on Events** (Lines 140, 303)
```python
# When match is confirmed
elif event == 'match_confirmed':
    self.match_confirmed = True  # NEW
    self.current_match_id = payload.get('match_id')
    # ... existing code ...

# When veto completes
async def _handle_veto_complete(self, payload: dict):
    self.veto_complete = True  # NEW
    logger.info(f"🎮 Bot {self.bot_alias} veto phase completed!")
    # ... existing code ...
```

### **3. New Function: `wait_for_veto_completion`** (Lines 504-531)
```python
async def wait_for_veto_completion(bot_clients: List[BotWebSocketClient], timeout_seconds: int = 300):
    """Wait for veto phase to complete across all bots"""
    print(f"\n[4/4] Waiting for veto phase completion (timeout: {timeout_seconds}s)...")
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        
        if elapsed >= timeout_seconds:
            print(f"   ⏰ Veto timeout reached ({timeout_seconds}s)")
            return False
        
        # Check if veto is complete (at least one bot should have veto_complete)
        veto_complete_count = sum(1 for bot in bot_clients if bot.veto_complete)
        
        if veto_complete_count > 0:
            print(f"   ✅ Veto phase completed! ({veto_complete_count} bots confirmed)")
            return True
        
        # Show progress every 5 seconds
        if int(elapsed) % 5 == 0 and int(elapsed) > 0:
            remaining = timeout_seconds - int(elapsed)
            confirmed = sum(1 for bot in bot_clients if bot.match_confirmed)
            print(f"   ⏳ Waiting for veto... {confirmed}/{len(bot_clients)} bots confirmed match ({remaining}s remaining)")
        
        await asyncio.sleep(1)
```

**Features:**
- Waits up to 300 seconds (5 minutes) for veto completion
- Checks if ANY bot has received `veto_complete` event
- Shows progress every 5 seconds with match confirmation count
- Returns `True` when veto completes, `False` on timeout

### **4. Updated Main Flow** (Lines 602-626)
```python
match_found = await wait_for_match_or_timeout(bot_clients, timeout_seconds=300)

if match_found:
    print("\n🎉 SUCCESS! Match was found and bots auto-accepted")
    print("   💡 Check your client - you should see the match confirmation")
    print("   💡 Accept the match to proceed to veto phase")
    
    # Wait for veto phase to complete (with extended timeout)
    print("\n   ⏳ Waiting for veto phase to complete...")
    veto_completed = await wait_for_veto_completion(bot_clients, timeout_seconds=300)
    
    if veto_completed:
        print("\n   ✅ Veto phase completed successfully!")
        print("   💡 Bots will disconnect in 10 seconds...")
        await asyncio.sleep(10)
    else:
        print("\n   ⚠️  Veto phase did not complete within timeout")
        print("   💡 Check Celery worker logs for auto-veto activity")
        print("   💡 Bots will disconnect in 10 seconds...")
        await asyncio.sleep(10)
```

**Before:**
- Bots disconnected after 60 seconds regardless of veto status
- Script couldn't tell if veto completed or not
- No visibility into veto progress

**After:**
- Bots stay connected until veto completes
- Script monitors veto progress with live updates
- Clear feedback about veto completion status
- 10-second grace period before disconnect

## 📊 **Expected Behavior**

### **Timeline:**
1. ✅ Match found → Bots auto-accept
2. ✅ User accepts match → Match confirmed
3. ✅ Script waits for veto completion (up to 5 minutes)
4. ✅ Veto phase completes (either manually or via auto-veto timeouts)
5. ✅ Script detects completion → "Veto phase completed!"
6. ✅ 10-second grace period
7. ✅ Bots disconnect cleanly

### **Progress Output:**
```
[4/4] Waiting for veto phase completion (timeout: 300s)...
   ⏳ Waiting for veto... 10/9 bots confirmed match (295s remaining)
   ⏳ Waiting for veto... 10/9 bots confirmed match (290s remaining)
   ⏳ Waiting for veto... 10/9 bots confirmed match (285s remaining)
   ✅ Veto phase completed! (9 bots confirmed)

   ✅ Veto phase completed successfully!
   💡 Bots will disconnect in 10 seconds...
```

## 🎯 **What This Fixes**

1. ✅ **Bots no longer disconnect prematurely** - They wait for veto to complete
2. ✅ **Auto-veto timeout system can work** - Bots stay alive long enough to see timeouts
3. ✅ **Clear visibility** - Script shows what's happening during veto phase
4. ✅ **Graceful cleanup** - 10-second delay before disconnect

## ⚠️ **What Still Needs Investigation**

The captain detection issue - bots showing `Is captain: False` and `My team: None` - needs to be investigated on the **server side**, not in the bot script.

See: **CAPTAIN_DETECTION_INVESTIGATION.md** for details.

