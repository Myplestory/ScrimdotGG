# Captain Detection Root Cause - Investigation Results

## ✅ **Server Code IS Correct**

After investigating the server-side code, I can confirm:

### **1. Captains ARE Being Assigned** ✅

**File:** `server/matchmaking/match_manager.py` (Lines 63-70, 89-90)

```python
# Get captains from matchmaker data (if available) or determine by highest MMR
if 'team_a' in match_data and 'team_b' in match_data:
    team_a_captain = match_data['team_a'].get('captain', max(team_a_players, key=lambda p: p.get('mmr', 0)))
    team_b_captain = match_data['team_b'].get('captain', max(team_b_players, key=lambda p: p.get('mmr', 0)))
else:
    # Fallback: determine captains (highest MMR player on each team)
    team_a_captain = max(team_a_players, key=lambda p: p.get('mmr', 0))
    team_b_captain = max(team_b_players, key=lambda p: p.get('mmr', 0))

# Store captain PUUIDs in match
match = await sync_to_async(Match.objects.create)(
    # ... other fields ...
    team_a_captain_puuid=team_a_captain['puuid'],
    team_b_captain_puuid=team_b_captain['puuid'],
    # ... other fields ...
)
```

**Captain selection logic:**
- Highest MMR player on each team becomes captain
- Stored in `match.team_a_captain_puuid` and `match.team_b_captain_puuid`

### **2. MatchPlayer Entries Include is_captain** ✅

**File:** `server/matchmaking/match_manager.py` (Lines 183-192, 194-203)

```python
for player in team_a_players:
    match_players.append(MatchPlayer(
        match=match,
        player_puuid=player['puuid'],
        player_alias=player['alias'],
        player_elo=player.get('elo', 0),
        player_mmr=player.get('mmr', 0),
        team='team_a',
        is_captain=(player['puuid'] == match.team_a_captain_puuid)  # ✅ Captain flag set!
    ))

for player in team_b_players:
    match_players.append(MatchPlayer(
        match=match,
        player_puuid=player['puuid'],
        player_alias=player['alias'],
        player_elo=player.get('elo', 0),
        player_mmr=player.get('mmr', 0),
        team='team_b',
        is_captain=(player['puuid'] == match.team_b_captain_puuid)  # ✅ Captain flag set!
    ))
```

**Result:**
- Each MatchPlayer has `team` field set ('team_a' or 'team_b')
- Each MatchPlayer has `is_captain` field set (True for captains, False for others)

### **3. Match Data Payload Includes is_captain** ✅

**File:** `server/matchmaking/match_manager.py` (Lines 466-475, 492-493)

```python
# Get all match players
for player in players:
    match_players.append({
        'puuid': player.player_puuid,
        'alias': player.player_alias,
        'elo': player.player_elo,
        'mmr': player.player_mmr,
        'team': player.team,                    # ✅ Team field included!
        'is_captain': player.is_captain,        # ✅ Captain flag included!
        'is_ready': player.is_ready,
        'joined_pregame': player.joined_pregame,
    })

return {
    'match_id': str(match.id),
    'state': match.state,
    'team_a_players': [p for p in match_players if p['team'] == 'team_a'],  # ✅ Filtered by team!
    'team_b_players': [p for p in match_players if p['team'] == 'team_b'],  # ✅ Filtered by team!
    'team_a_captain': match.team_a_captain_puuid,
    'team_b_captain': match.team_b_captain_puuid,
    # ... other fields ...
}
```

**Result:**
- Each player object has `team` and `is_captain` fields
- Players are correctly split into `team_a_players` and `team_b_players` arrays

---

## 🔍 **The Real Problem: Bot Team Detection Logic**

Since the server is sending the correct data, the issue must be in how the bot is parsing it. Let me check the bot logs again:

```
INFO:__main__:🎮 Bot QueueBot1 veto state initialized:
INFO:__main__:   Is captain: False
INFO:__main__:   My team: None   ← THIS IS THE ISSUE!
```

If `my_team` is `None`, it means the bot couldn't find its PUUID in `team_a_players` or `team_b_players`.

### **Possible Causes:**

#### **Issue #1: PUUID Format Mismatch**

**Bot's PUUID:** String format from `uuid.uuid4()` → `"a3881ac1-f434-4a54-8fe2-a5aaca29f861"`

**Server's PUUID in payload:** Could be:
- String: `"a3881ac1-f434-4a54-8fe2-a5aaca29f861"` ✅
- UUID object: `UUID('a3881ac1-f434-4a54-8fe2-a5aaca29f861')` ❌ (would fail equality check)
- Different casing: `"A3881AC1-F434-4A54-8FE2-A5AACA29F861"` ❌

**Current bot comparison** (lines 256-267):
```python
for player in team_a_players:
    if player.get('puuid') == self.bot_puuid:  # Direct equality check
        self.is_captain = True
        self.my_team = 'team_a'
        break
```

This will FAIL if:
- Server sends UUID object instead of string
- Server sends different casing
- There's whitespace

#### **Issue #2: Empty Player Arrays**

If `team_a_players` or `team_b_players` are empty arrays, the bot won't find itself.

**Possible causes:**
- `MatchPlayer.objects.filter(match=match)` returns empty
- Team filtering `[p for p in match_players if p['team'] == 'team_a']` fails
- Database doesn't have MatchPlayer entries yet

#### **Issue #3: Timing Issue**

The bot calls `get_match_data` immediately after receiving `match_confirmed` (line 144-146):

```python
elif event == 'match_confirmed':
    self.match_confirmed = True
    self.current_match_id = payload.get('match_id')
    # Request match data immediately
    await self._send_message('get_match_data', {
        'match_id': self.current_match_id
    })
```

**Potential race condition:**
1. Match is confirmed
2. Bot requests match data
3. Server hasn't finished creating MatchPlayer entries yet
4. `get_match_data` returns empty player arrays

---

## 🧪 **Next Steps: Add Debug Logging**

To find the exact cause, we need to see what the server is actually sending. Here's what to add:

### **1. Server-Side Logging**

**File:** `server/matchmaking/match_manager.py` (After line 475)

```python
# Get all match players
for player in players:
    match_players.append({
        'puuid': player.player_puuid,
        'alias': player.player_alias,
        'elo': player.player_elo,
        'mmr': player.player_mmr,
        'team': player.team,
        'is_captain': player.is_captain,
        'is_ready': player.is_ready,
        'joined_pregame': player.joined_pregame,
    })

# ADD THIS DEBUG LOGGING:
logger.info(f"[GET_MATCH_DATA] Match {match_id}:")
logger.info(f"  Total MatchPlayer entries: {len(match_players)}")
logger.info(f"  Team A players: {[p['alias'] + ' (' + p['puuid'][:8] + '...)' for p in match_players if p['team'] == 'team_a']}")
logger.info(f"  Team B players: {[p['alias'] + ' (' + p['puuid'][:8] + '...)' for p in match_players if p['team'] == 'team_b']}")
logger.info(f"  Team A captain PUUID: {match.team_a_captain_puuid[:8]}...")
logger.info(f"  Team B captain PUUID: {match.team_b_captain_puuid[:8]}...")
logger.info(f"  Team A captains: {[p['alias'] for p in match_players if p['team'] == 'team_a' and p['is_captain']]}")
logger.info(f"  Team B captains: {[p['alias'] for p in match_players if p['team'] == 'team_b' and p['is_captain']]}")
```

### **2. Bot-Side Logging (Already Suggested)**

**File:** `server/testing/test_queue_with_bots_v4.py` (In `_handle_match_data` method)

```python
async def _handle_match_data(self, payload: dict):
    """Handle match data (veto phase initialization)"""
    logger.info(f"🎮 Bot {self.bot_alias} received match data")
    
    # ADD THIS DEBUG LOGGING:
    logger.info(f"📦 RAW PAYLOAD:")
    logger.info(f"  Match ID: {payload.get('match_id')}")
    logger.info(f"  State: {payload.get('state')}")
    logger.info(f"  Team A players: {len(payload.get('team_a_players', []))} players")
    logger.info(f"  Team B players: {len(payload.get('team_b_players', []))} players")
    logger.info(f"  Team A captain: {payload.get('team_a_captain')}")
    logger.info(f"  Team B captain: {payload.get('team_b_captain')}")
    
    # Log player PUUIDs for comparison
    logger.info(f"  Bot PUUID: {self.bot_puuid}")
    logger.info(f"  Bot PUUID type: {type(self.bot_puuid)}")
    for i, player in enumerate(payload.get('team_a_players', [])):
        logger.info(f"  Team A Player {i}: {player.get('alias')} - PUUID: {player.get('puuid')} (type: {type(player.get('puuid'))})")
    for i, player in enumerate(payload.get('team_b_players', [])):
        logger.info(f"  Team B Player {i}: {player.get('alias')} - PUUID: {player.get('puuid')} (type: {type(player.get('puuid'))})")
    
    # ... rest of the method ...
```

---

## 🎯 **Expected Debug Output**

With these logs, we'll see:

### **If PUUIDs are correct:**
```
[GET_MATCH_DATA] Match abc123:
  Total MatchPlayer entries: 10
  Team A players: ['QueueBot0 (a3881ac1...)', 'QueueBot2 (ccb8d48f...)', ...]
  Team B players: ['QueueBot1 (53597ac6...)', 'QueueBot3 (c156903b...)', ...]
  Team A captains: ['QueueBot0']
  Team B captains: ['QueueBot1']

Bot QueueBot0 PUUID: a3881ac1-f434-4a54-8fe2-a5aaca29f861
Bot PUUID type: <class 'str'>
Team A Player 0: QueueBot0 - PUUID: a3881ac1-f434-4a54-8fe2-a5aaca29f861 (type: <class 'str'>)
  ✅ MATCH! Bot should find itself in team_a
```

### **If there's a mismatch:**
```
Bot QueueBot0 PUUID: a3881ac1-f434-4a54-8fe2-a5aaca29f861
Bot PUUID type: <class 'str'>
Team A Player 0: QueueBot0 - PUUID: <UUID: a3881ac1-f434-4a54-8fe2-a5aaca29f861> (type: <class 'UUID'>)
  ❌ MISMATCH! String != UUID object
```

### **If arrays are empty:**
```
[GET_MATCH_DATA] Match abc123:
  Total MatchPlayer entries: 0  ← Problem!
  Team A players: []
  Team B players: []
```

---

## 💡 **Recommendation**

1. **Add the server-side debug logging** to `match_manager.py` (line ~475)
2. **Add the bot-side debug logging** to `test_queue_with_bots_v4.py` (in `_handle_match_data`)
3. **Run the test again** and capture the logs
4. **Compare the PUUIDs** - look for:
   - Type mismatches (str vs UUID)
   - Casing differences
   - Empty arrays
   - Missing is_captain flags

Once we see the actual data being sent/received, we'll know exactly what's wrong and can fix it.

