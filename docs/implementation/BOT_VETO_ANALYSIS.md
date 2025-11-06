# Bot V5 Veto Issue Analysis

## Issue Symptoms

Bots are not vetoing properly during the veto phase.

## Investigation

### 1. Bot Script Flow

**Bot connects and receives `match_data` event** (line 168 in bot script):
```python
elif event == 'match_data':
    logger.info(f"🔧 [FIX] Bot {self.bot_alias} received match_data event from server broadcast!")
    await self._handle_match_data(payload)
```

**Bot handles match_data** (line 331):
```python
async def _handle_match_data(self, payload: dict):
    # Checks if state is 'SERVER_VETO' or 'VETO'
    if payload.get('state') == 'SERVER_VETO':
        # Server veto handling
    elif payload.get('state') == 'VETO':
        # Map veto handling
```

### 2. State Names Match

From `match_system/models.py`:
- ✅ `STATE_SERVER_VETO = 'SERVER_VETO'` 
- ✅ `STATE_VETO = 'VETO'`

Bot checks for these exact strings, so state names are correct.

### 3. Captain Detection Logic

Bot determines if it's captain by checking team players (lines 372-387 for server veto, 432-455 for map veto):

```python
# Check team A
for player in team_a_players:
    if player.get('puuid') == self.bot_puuid:
        self.my_team = 'team_a'
        if player.get('is_captain'):
            self.is_captain = True
        break
```

**Key Issue**: The bot checks `player.get('puuid') == self.bot_puuid`

### 4. Debug Logging Shows PUUID Comparison

The bot has extensive debug logging (lines 339-369):
```python
logger.info(f"🔍 [DEBUG] Bot {self.bot_alias} PUUID investigation:")
logger.info(f"   Bot's self.bot_puuid: '{self.bot_puuid}' (type: {type(self.bot_puuid)})")
# ... logs each player's PUUID and compares
logger.info(f"         Match check: '{puuid}' == '{self.bot_puuid}' = {puuid == self.bot_puuid}")
```

## Potential Issues

### Issue 1: PUUID Type Mismatch

**Hypothesis**: The `self.bot_puuid` might be a string, but `player.get('puuid')` from match_data might be a UUID object or vice versa.

**Evidence**: The bot logs show explicit type checking and comparison results.

**Where to check**:
1. `match_system/managers/match_manager.py:get_match_data()` - What type are the PUUIDs in the returned data?
2. Bot initialization (line 60-63) - `self.bot_puuid` is set as a string from the constructor

### Issue 2: Match Data Structure

**Hypothesis**: The `match_data` event payload might not include the player data correctly.

**Where to check**:
1. `match_system/managers/match_manager.py:get_match_data()` - Returns team_a_players and team_b_players
2. How is `match_data` broadcast in `realtime/consumers.py`?

### Issue 3: Bot Never Receives match_data

**Hypothesis**: Bots might not be receiving the `match_data` event at all.

**Evidence**: Look for log message "🔧 [FIX] Bot {alias} received match_data event from server broadcast!"

### Issue 4: Bots Not in Match Group

**Hypothesis**: Bots might not be added to the `match_{match_id}` group, so they never receive veto updates.

**Where to check**: `realtime/consumers.py:match_data()` handler should add players to match group.

## What to Check in Logs

### Server Logs:
1. ✅ Is `get_match_data` being called?
2. ✅ What does the returned match_data look like?
3. ✅ Are players being added to `match_{match_id}` group?
4. ✅ Are veto broadcasts being sent?

### Bot Logs:
1. ❌ Do bots receive `match_data` event?
2. ❌ What is the PUUID comparison result? (check debug logs)
3. ❌ Does `self.is_captain` get set to True for any bot?
4. ❌ Does `self.my_team` get set correctly?
5. ❌ Do bots reach the "IT'S MY TURN!" log message?

## Likely Root Cause

Based on the code structure, the most likely issues are:

### **#1: PUUID Type Mismatch** (MOST LIKELY)

`match_system/managers/match_manager.py:get_match_data()` returns player data from `MatchPlayer` objects:

```python
match_players.append({
    'puuid': player.player_puuid,  # This might be a string
    'alias': player.player_alias,
    'elo': player.player_elo,
    'mmr': player.player_mmr,
    'team': player.team,
    'is_captain': player.is_captain,  # This should be boolean
    # ...
})
```

The `player_puuid` field in `MatchPlayer` model is defined as `CharField`, so it should be a string. But we need to verify what's actually being sent to the bot.

### **#2: Bots Not Receiving match_data Event**

The bot script expects to receive `match_data` automatically after `match_confirmed`, but we need to verify:
- Is the broadcast happening?
- Are bots in the right group to receive it?

## Next Steps

1. **Run the bot script and capture logs**
2. **Look for PUUID debug messages** - they'll show exact comparison results
3. **Check if ANY bot has `is_captain = True`**
4. **Verify bots receive `match_data` event**
5. **Check server logs for veto broadcast messages**

## Expected Fix

If PUUID matching is the issue, ensure:
```python
# In match_system/managers/match_manager.py:get_match_data()
'puuid': str(player.player_puuid),  # Force string conversion
```

Or in bot script:
```python
# In _handle_match_data
if str(player.get('puuid')) == str(self.bot_puuid):
    # ...
```

