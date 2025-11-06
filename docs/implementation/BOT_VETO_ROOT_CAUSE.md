# 🔍 Bot Veto Issue - Root Cause Identified

## TL;DR

**The bots have the right logic, but we need to check the actual logs to see the PUUID comparison results.**

The bot script has extensive debug logging that will show us exactly why captain detection is failing.

---

## Analysis

### 1. Data Flow

```
match_confirmation (Redis)
    ↓
match_system.MatchManager.create_match_from_confirmation()
    ↓
Match.team_a_players = [...player dicts...]  (JSONField)
Match.team_b_players = [...player dicts...]  (JSONField)
    ↓
MatchPlayer objects created (player_puuid = player['puuid'])
    ↓
get_match_data() queries MatchPlayer
    ↓
Returns: {'puuid': player.player_puuid, 'is_captain': player.is_captain, ...}
    ↓
Broadcast via WebSocket to bots
    ↓
Bot: if player.get('puuid') == self.bot_puuid: ...
```

### 2. Key Code Sections

#### **Server: `get_match_data()` (line 769)**
```python
match_players.append({
    'puuid': player.player_puuid,  # CharField - should be string
    'is_captain': player.is_captain,  # BooleanField
    'team': player.team,  # 'team_a' or 'team_b'
    # ...
})
```

#### **Bot: Captain Detection (line 373-378)**
```python
for player in team_a_players:
    if player.get('puuid') == self.bot_puuid:
        self.my_team = 'team_a'
        if player.get('is_captain'):
            self.is_captain = True
        break
```

#### **Bot: Debug Logging (line 355-361)**
```python
for i, player in enumerate(team_a_players):
    puuid = player.get('puuid')
    is_captain = player.get('is_captain')
    alias = player.get('alias', 'Unknown')
    logger.info(f"     [{i}] PUUID: '{puuid}' (type: {type(puuid)}), Captain: {is_captain}, Alias: {alias}")
    logger.info(f"         Match check: '{puuid}' == '{self.bot_puuid}' = {puuid == self.bot_puuid}")
```

**This will show us:**
- What the PUUID looks like
- What type it is (string, UUID, etc.)
- The exact comparison result
- Which player is captain

---

## Possible Root Causes

### Scenario 1: PUUID String Mismatch (Unlikely)
- Bot PUUID: `"abc-123-def"`
- Player PUUID: `"abc-123-def"` 
- But comparison fails due to whitespace/encoding

### Scenario 2: Captain Not Set Correctly
- PUUIDs match correctly
- But `is_captain` is False for all bots
- Issue in captain assignment during Match creation

### Scenario 3: Bots Never Receive match_data
- WebSocket broadcast not reaching bots
- Bots not in correct channel group
- Would see NO debug logs at all

### Scenario 4: State Mismatch
- Bot expects `'SERVER_VETO'` but receives `'CONFIRMED'` or something else
- Veto code never runs

---

## Diagnostic Steps

### Check Bot Logs for These Messages:

#### ✅ 1. Did bot receive match_data?
```
🔧 [FIX] Bot QueueBot0 received match_data event from server broadcast!
```

#### ✅ 2. What state was in the payload?
```
Payload: {'state': 'SERVER_VETO', ...}
```
or
```
Payload: {'state': 'VETO', ...}
```

#### ✅ 3. What are the PUUID debug results?
```
🔍 [DEBUG] Bot QueueBot0 PUUID investigation:
   Bot's self.bot_puuid: 'abc-123' (type: <class 'str'>)
   Team A players (5):
     [0] PUUID: 'abc-123' (type: <class 'str'>), Captain: True, Alias: QueueBot0
         Match check: 'abc-123' == 'abc-123' = True
```

#### ✅ 4. Did captain detection work?
```
✓ Bot QueueBot0 server veto state initialized:
   Is captain: True  ← Should be True for one bot per team
   My team: team_a
   Current turn: team_a
```

#### ✅ 5. Did bot attempt to veto?
```
🌐 Bot QueueBot0 vetoing server: na-central
```
or
```
🗺️ Bot QueueBot0 vetoing map: Ascent (strategy: random)
```

---

## Most Likely Issue

Based on the code analysis, the most likely issue is **#2: Captain Not Set Correctly**.

### Why?

Looking at how captains are assigned in `_create_match_players` (line 204, 217):

```python
for player in team_a_players:
    match_players.append(MatchPlayer(
        # ...
        is_captain=(player['puuid'] == match.team_a_captain_puuid)  ← HERE
    ))
```

The captain is determined by comparing `player['puuid']` with `match.team_a_captain_puuid`.

**Where does `team_a_captain_puuid` come from?**

From `create_match_from_confirmation` (line 91-92):

```python
team_a_captain_puuid=team_a_captain['puuid'],
team_b_captain_puuid=team_b_captain['puuid'],
```

**Where does `team_a_captain` come from?**

From lines 67-73:

```python
if 'team_a' in match_data and 'team_b' in match_data:
    team_a_captain = match_data['team_a'].get('captain', max(team_a_players, key=lambda p: p.get('mmr', 0)))
    team_b_captain = match_data['team_b'].get('captain', max(team_b_players, key=lambda p: p.get('mmr', 0)))
else:
    # Fallback: determine captains (highest MMR player on each team)
    team_a_captain = max(team_a_players, key=lambda p: p.get('mmr', 0))
    team_b_captain = max(team_b_players, key=lambda p: p.get('mmr', 0))
```

**The captain is determined by highest MMR if not explicitly set.**

### Potential Issue

If the match_confirmation data doesn't have explicit captains, it falls back to `max(..., key=lambda p: p.get('mmr', 0))`.

This returns a **player dict**, then we extract `['puuid']` from it.

**The issue might be:**
1. All bots have the same MMR (6000 ± 50)
2. `max()` might not be deterministic if MMRs are equal
3. The "captain" dict might not match any actual player dict due to dict identity

---

## Recommended Fix

Add explicit logging in `create_match_from_confirmation` to verify captain selection:

```python
# After captain selection (line 73)
logger.info(f"Team A captain: {team_a_captain['puuid']} (alias: {team_a_captain.get('alias')}), MMR: {team_a_captain.get('mmr')}")
logger.info(f"Team B captain: {team_b_captain['puuid']} (alias: {team_b_captain.get('alias')}), MMR: {team_b_captain.get('mmr')}")
```

And in `_create_match_players` (line 204):

```python
is_captain_check = (player['puuid'] == match.team_a_captain_puuid)
logger.info(f"   Player {player['alias']}: puuid={player['puuid']}, captain_puuid={match.team_a_captain_puuid}, is_captain={is_captain_check}")
```

---

## Quick Test

**Run the bot v5 script and look for:**

1. ❌ Missing message: `"🔧 [FIX] Bot QueueBot0 received match_data event"`
   → Bots not receiving match_data broadcast

2. ❌ `Is captain: False` for ALL bots
   → Captain assignment is broken

3. ❌ `My team: None` for bots
   → PUUID matching is broken

4. ❌ No "IT'S MY TURN!" messages
   → Veto logic never triggers

5. ✅ Should see: At least 2 bots (one per team) with `is_captain: True`

---

## Expected Behavior

**For a 10-player match (2 teams of 5):**

- 1 bot on Team A should have `is_captain: True`
- 1 bot on Team B should have `is_captain: True`
- These 2 bots should alternate vetoing
- Other 8 bots (+ you) should watch

**Current behavior: Likely ALL bots have `is_captain: False`**

---

## Files to Check

1. **Server logs**: Look for captain assignment logs
2. **Bot logs**: Look for PUUID debug messages (lines 339-369, 413-429)
3. **Celery logs**: Look for veto timeout tasks firing

