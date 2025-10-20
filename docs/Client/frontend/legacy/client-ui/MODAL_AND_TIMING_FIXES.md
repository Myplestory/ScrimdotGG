# Match Modal Indicator & Bot Timing Fixes

## Summary
Fixed two critical issues with the match acceptance flow:
1. Modal indicator showing lobby-specific counts instead of global match counts
2. Bot acceptance timing too fast to properly test the modal indicator

---

## 🔧 **Fix 1: Modal Indicator Shows Global Acceptance Count**

### **Problem:**
- Modal showed "4/10" when 9 players had actually accepted
- The `player_accepted` event was only sent to the accepting player's lobby
- Each lobby only saw its own acceptance updates, not the global match progress

### **Root Cause:**
**Location:** `server/matchmaking/consumers.py:688-702`

The server was sending `player_accepted` events only to the specific lobby that just accepted:
```python
# OLD CODE - Lobby-specific
lobby_id = result.get('lobby_id')
if lobby_id:
    await self.channel_layer.group_send(
        f"lobby_{lobby_id}",  # Only ONE lobby
        {
            'type': 'player_accepted',
            'accepted_count': result.get('accepted_count'),
            'total_players': result.get('total_players'),
            'timeout_seconds': result.get('timeout_seconds')
        }
    )
```

### **Solution:**
**Location:** `server/matchmaking/consumers.py:687-708`

Send `player_accepted` events to **ALL lobbies** involved in the match:
```python
# NEW CODE - Match-wide broadcast
match_lobbies = result.get('match_lobbies', [])
accepted_count = result.get('accepted_count')
total_players = result.get('total_players')
timeout_seconds = result.get('timeout_seconds')

if match_lobbies:
    # Broadcast to all lobbies involved in this match
    for lobby_id in match_lobbies:
        await self.channel_layer.group_send(
            f"lobby_{lobby_id}",  # ALL lobbies in the match
            {
                'type': 'player_accepted',
                'accepted_count': accepted_count,
                'total_players': total_players,
                'timeout_seconds': timeout_seconds
            }
        )
    logger.info(f"Player acceptance update sent to ALL {len(match_lobbies)} lobbies: {accepted_count}/{total_players} accepted")
```

### **Impact:**
✅ **All players now see the same global acceptance count**
- User sees "9/10" when 9 players have accepted (not "4/10")
- Modal indicator updates in real-time as ANY player accepts
- Consistent experience across all lobbies in the match

---

## 🔧 **Fix 2: Bot Acceptance Timing - Random Delays**

### **Problem:**
- Bots accepted sequentially with only 0.5s delay between each
- All 8 bots accepted within ~4 seconds
- Too fast to properly test and visualize the modal indicator updates
- User couldn't see the indicator updating in real-time

### **Root Cause:**
**Location:** `server/testing/bot_auto_acceptor.py:91-117`

Bots were accepting sequentially with fixed delays:
```python
# OLD CODE - Sequential with 0.5s delay
for puuid in bot_puuids:
    await asyncio.sleep(0.5)  # Fixed 0.5s delay
    result = await MatchConfirmationManager.accept_match(match_id, puuid)
```

### **Solution:**
**Location:** `server/testing/bot_auto_acceptor.py:91-125`

Bots now accept **concurrently** with **random delays between 1-15 seconds**:
```python
# NEW CODE - Concurrent with random delays
async def accept_with_delay(puuid: str):
    """Accept match for a bot after random delay"""
    # Random delay between 1-15 seconds (realistic player behavior)
    delay = random.uniform(1.0, 15.0)
    logger.info(f"[BOT_ACCEPTOR] Bot {puuid[:12]} will accept in {delay:.1f}s")
    await asyncio.sleep(delay)
    
    result = await MatchConfirmationManager.accept_match(match_id, puuid)
    # ... acceptance logic ...

# Accept all bots concurrently (each with their own random delay)
await asyncio.gather(*[accept_with_delay(puuid) for puuid in bot_puuids])
```

### **Key Improvements:**
1. **Random Delays:** Each bot waits 1-15 seconds before accepting
2. **Concurrent Execution:** All bots wait simultaneously (not sequentially)
3. **Realistic Behavior:** Simulates actual player acceptance patterns
4. **Better Testing:** Modal indicator updates are now visible and testable

### **Impact:**
✅ **Modal indicator updates are now visible**
- Acceptances spread over 1-15 second window
- User can see each acceptance update the indicator in real-time
- More realistic simulation of actual player behavior
- Better testing of the acceptance flow

---

## 📊 **Before vs After:**

### **Before:**
```
Time 0s:  Bot1 accepts → User sees 1/10 (only their lobby)
Time 0.5s: Bot2 accepts → User sees 2/10 (only their lobby)
Time 1s:  Bot3 accepts → User sees 3/10 (only their lobby)
Time 1.5s: Bot4 accepts → User sees 3/10 (still only their lobby)
...
User accepts at Time 5s → Modal shows 4/10 (lobby count, not global 9/10)
```

### **After:**
```
Time 0s:   Match found → All players receive proposal
Time 3s:   Bot1 accepts → All lobbies see 1/10 ✅
Time 7s:   Bot2 accepts → All lobbies see 2/10 ✅
Time 10s:  User accepts → All lobbies see 3/10 ✅
Time 12s:  Bot3 accepts → All lobbies see 4/10 ✅
Time 14s:  Bot4 accepts → All lobbies see 5/10 ✅
...
Time 15s:  Bot8 accepts → All lobbies see 9/10 ✅
(Bot9 doesn't accept - match times out)
```

---

## 🎯 **Testing Instructions:**

1. **Start servers:**
   ```bash
   # Terminal 1: Daphne
   cd server
   pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application
   
   # Terminal 2: Celery Worker
   cd server
   pipenv run celery -A scrimgg worker --loglevel=info -Q matchmaking,cleanup -P gevent
   
   # Terminal 3: Celery Beat
   cd server
   pipenv run celery -A scrimgg beat --loglevel=info
   ```

2. **Run test script:**
   ```bash
   # Terminal 4: Test with bots
   cd server/testing
   pipenv run python test_queue_with_bots_v2.py
   ```

3. **Test in client:**
   - Launch Electron client
   - Select 5+ maps
   - Click "FIND MATCH"
   - When modal appears, click "ACCEPT"
   - **Watch the indicator update as bots accept over 1-15 seconds**
   - **Verify indicator shows global count (e.g., 9/10), not lobby count (e.g., 4/10)**

---

## ✅ **Expected Behavior:**

1. **Match Proposal:**
   - Modal appears for all 10 players
   - Timer shows 30 seconds

2. **User Accepts:**
   - User clicks "ACCEPT"
   - Modal shows "Waiting for other players..."
   - Indicator starts at 1/10 or higher (depending on bot timing)

3. **Bots Accept (Over 1-15 seconds):**
   - Indicator updates: 2/10, 3/10, 4/10, ..., 9/10
   - Each update is visible in real-time
   - **All players see the same count**

4. **Timeout:**
   - One bot doesn't accept
   - After 30s, modal closes
   - All lobbies requeued (if requeue fix is working)

---

## 📝 **Files Modified:**

1. **`server/matchmaking/consumers.py`** (Lines 687-708)
   - Changed `player_accepted` broadcast from single lobby to all match lobbies
   - Added logging for multi-lobby broadcasts

2. **`server/testing/bot_auto_acceptor.py`** (Lines 91-125)
   - Changed from sequential to concurrent bot acceptance
   - Added random delays (1-15 seconds) per bot
   - Improved logging to show acceptance timing

---

## 🐛 **Known Remaining Issues:**

1. **Requeue not working:** Lobbies not returning to queue after timeout (separate issue)
2. **Cleanup finding 0 matches:** Match confirmations being deleted before cleanup runs (separate issue)

These will be addressed in separate fixes.

