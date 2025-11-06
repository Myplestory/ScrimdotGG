# 🔍 What to Check in Bot Logs

## Quick Diagnosis

Run your bot v5 script and search the logs for these specific messages:

---

## 1. Are Bots Receiving match_data? ✅/❌

**Search for:**
```
🔧 [FIX] Bot QueueBot
```

**Expected:** Should see this message for each bot when the match is confirmed.

**If missing:** Bots aren't receiving the match_data broadcast. This means:
- Bots weren't added to match group
- WebSocket broadcast failed
- Check `realtime/consumers.py:match_data()` handler

---

## 2. What State is in match_data? ✅/❌

**Search for:**
```
Payload: {'state':
```

**Expected:** Should see `'state': 'SERVER_VETO'` first, then later `'state': 'VETO'` for map veto.

**If wrong state:** The match didn't transition to veto phase correctly.

---

## 3. PUUID Debug Results 🔍

**Search for:**
```
🔍 [DEBUG] Bot QueueBot0 PUUID investigation:
```

**Look for these lines:**
```
Bot's self.bot_puuid: 'abc-def-123' (type: <class 'str'>)
Team A players (5):
  [0] PUUID: 'abc-def-123' (type: <class 'str'>), Captain: True, Alias: QueueBot0
      Match check: 'abc-def-123' == 'abc-def-123' = True  ← Should be True!
```

**Key things to check:**
- ✅ Are the PUUID types the same? (both should be `<class 'str'>`)
- ✅ Is `Match check: ... = True` for at least one player?
- ✅ Is `Captain: True` for at least one player per team?

**Common issues:**
- ❌ `Match check: ... = False` for ALL players → PUUID mismatch
- ❌ `Captain: False` for ALL players → Captain assignment broken
- ❌ PUUID types differ (str vs UUID) → Type mismatch

---

## 4. Captain Detection Success? ✅/❌

**Search for:**
```
Bot QueueBot0 server veto state initialized:
   Is captain:
```

**Expected:** 
- ONE bot per team should have `Is captain: True`
- That bot should also have `My team: team_a` or `My team: team_b`

**Example (GOOD):**
```
✓ Bot QueueBot2 server veto state initialized:
   Is captain: True  ← YES!
   My team: team_a
   Current turn: team_a
   Available servers: ['Virginia', 'Illinois', ...]
```

**Example (BAD):**
```
✗ Bot QueueBot2 server veto state initialized:
   Is captain: False  ← NO!
   My team: team_a
   Current turn: team_a
```

---

## 5. Is Bot Attempting to Veto? ✅/❌

**Search for:**
```
IT'S MY TURN! Making server veto decision
```
or
```
IT'S MY TURN! Making map veto decision
```

**Expected:** Captain bot whose turn it is should log this.

**Then search for:**
```
🌐 Bot QueueBot2 vetoing server:
```
or
```
🗺️ Bot QueueBot2 vetoing map:
```

**Expected:** 2-3 seconds later, bot should actually veto.

**If missing:** Captain detection or turn logic is broken.

---

## 6. Common Failure Patterns

### Pattern A: Bots Never See match_data
```
[NO LOGS] - No "received match_data event" messages
```
**Diagnosis:** Bots not in match group or broadcast failed.

---

### Pattern B: All Bots See match_data But None Are Captains
```
✓ Bot QueueBot0 received match_data event
🔍 [DEBUG] Bot QueueBot0 PUUID investigation:
   ...
   [0] PUUID: 'xxx', Captain: False  ← All False!
   [1] PUUID: 'yyy', Captain: False
   ...
✗ Bot QueueBot0 server veto state initialized:
   Is captain: False  ← Should be True for ONE bot!
```
**Diagnosis:** Captain assignment in `create_match_from_confirmation` is broken.

---

### Pattern C: PUUIDs Don't Match
```
✓ Bot QueueBot0 received match_data event
🔍 [DEBUG] Bot QueueBot0 PUUID investigation:
   Bot's self.bot_puuid: 'abc-123' (type: <class 'str'>)
   Team A players:
     [0] PUUID: 'xyz-789', Captain: True, Alias: QueueBot1
         Match check: 'xyz-789' == 'abc-123' = False  ← Never True!
     [1] PUUID: 'def-456', Captain: False, Alias: QueueBot2
         Match check: 'def-456' == 'abc-123' = False
```
**Diagnosis:** Bot's PUUID doesn't match any player in the match. This means:
- Match was created with different players
- PUUID format mismatch
- Bot connected with wrong PUUID

---

### Pattern D: Captain Assigned But Wrong Turn
```
✓ Bot QueueBot0 server veto state initialized:
   Is captain: True  ← Correct!
   My team: team_a
   Current turn: team_b  ← Not my turn!
✗ Not my turn (is_captain=True, current_turn=team_b, my_team=team_a)
```
**Diagnosis:** Captain is on wrong team or turn logic is incorrect. This is actually CORRECT behavior - bot waits for their turn.

---

## 7. What Should Happen (Ideal Flow)

### Server Veto Phase (First)
```
1. ✓ Bot QueueBot2 received match_data event
2. 🔍 [DEBUG] Shows bot is captain of team_a
3. ✓ Bot QueueBot2 - IT'S MY TURN! Making server veto decision...
4. 🌐 Bot QueueBot2 vetoing server: Virginia
5. (3 seconds later, team_b captain vetos)
6. (Repeat until only 1 server remains)
7. ✓ Bot QueueBot2 server veto phase completed!
   Final server: Illinois
```

### Map Veto Phase (Second)
```
1. ✓ Bot QueueBot7 map veto phase starting!
   Is captain: True, My team: team_b
2. ✓ Bot QueueBot7 - IT'S MY TURN! Making map veto decision...
3. 🗺️ Bot QueueBot7 vetoing map: Ascent (strategy: random)
4. (team_a captain vetos)
5. (Repeat until only 1 map remains)
6. ✓ Bot QueueBot7 veto phase completed!
   Final map: Bind
```

---

## Quick Test Command

Run bot script and capture logs:
```bash
python testing/test_queue_with_bots_v5.py 2>&1 | tee bot_test.log
```

Then search the log file:
```bash
# Check if match_data received
grep "received match_data event" bot_test.log

# Check PUUID debug info
grep -A 20 "PUUID investigation" bot_test.log

# Check captain status
grep "Is captain: True" bot_test.log

# Check veto attempts
grep "IT'S MY TURN" bot_test.log
grep "vetoing" bot_test.log
```

---

## Expected Results

For a 10-player match (9 bots + you):

- ✅ 9 bots should receive `match_data`
- ✅ 2 bots should have `is_captain: True` (one per team)
- ✅ Those 2 bots should alternate vetoing
- ✅ Should see ~5-6 server vetos (leaving 1 server)
- ✅ Should see ~8-9 map vetos (leaving 1 map)

---

## If You See No Vetos At All

**Most likely:**
1. ❌ No bot has `is_captain: True`
2. ❌ PUUID matching is failing (`Match check: ... = False`)
3. ❌ Bots not receiving `match_data` at all

**Next step:** Share the relevant log sections and I can pinpoint the exact issue.

