# Captain Detection Investigation

## 🔍 **Revised Analysis: Server-Side Issue**

You're absolutely correct - the matchmaker SHOULD be assigning captains when creating the match. The bot script's team detection logic is likely fine; the issue is on the **Django server side**.

## 📊 **Evidence from Bot Logs**

From the test run logs:
```
INFO:__main__:🎮 Bot QueueBot1 veto state initialized:
INFO:__main__:   Is captain: False
INFO:__main__:   My team: None
INFO:__main__:   Current turn: team_a
INFO:__main__:   Available maps: ['Lotus', 'Breeze', 'Bind', 'Ascent', 'Pearl', 'Icebox', 'Haven']
```

**ALL 9 bots** report:
- ✅ `Is captain: False` 
- ❌ `My team: None`  ← **This is the smoking gun**

## 🎯 **Root Cause Hypothesis**

If `my_team` is `None`, it means the bot couldn't find its PUUID in either `team_a_players` or `team_b_players`. This suggests:

1. **The `match_data` payload is missing player data**, OR
2. **The player PUUIDs in the payload don't match the bot PUUIDs**, OR  
3. **The match was created but players weren't properly assigned to teams**

## 🔬 **Where to Investigate**

### **1. Check MatchManager.create_match_from_confirmation** 

**File:** `server/matchmaking/match_manager.py` (around lines 35-100)

**What to verify:**
- Are `team_a_players` and `team_b_players` being populated?
- Are captains being assigned (`is_captain` field)?
- Are PUUIDs being correctly copied from the match confirmation?

**Key code to examine:**
```python
@staticmethod
async def create_match_from_confirmation(match_confirmation_id: str) -> Optional[Match]:
    """
    Create a Match instance from a successful MatchConfirmation.
    Assigns players to teams, selects captains, initializes map pool.
    """
    # ... existing code ...
    
    # Team assignment logic
    # Are team_a_players and team_b_players being created correctly?
    
    # Captain selection logic
    # Is is_captain being set for one player per team?
```

### **2. Check Match Data Broadcasting**

**File:** `server/matchmaking/consumers.py` (around line 228)

**Method:** `handle_get_match_data`

**What to verify:**
```python
async def handle_get_match_data(self, event):
    """Send current match data to requester"""
    data = event.get('data', {})
    match_id = data.get('match_id')
    
    # ... fetch match ...
    
    # Build player data for teams
    team_a_players = [
        {
            'puuid': mp.player_puuid,  # ← Is this correct?
            'alias': mp.player_alias,
            'elo': mp.player_elo,
            'is_captain': mp.is_captain,  # ← Is this being set?
            # ... other fields ...
        }
        for mp in match_players if mp.team == 'team_a'
    ]
    
    team_b_players = [
        # ... same for team_b ...
    ]
    
    # Are these arrays being sent correctly?
```

### **3. Check MatchPlayer Creation**

**File:** `server/matchmaking/match_manager.py` (around lines 60-90)

**What to verify:**
- When creating `MatchPlayer` entries, is `team` field being set correctly?
- Is `is_captain` being set for exactly 2 players (1 per team)?
- Are all 10 player PUUIDs being correctly copied?

```python
# Creating MatchPlayer entries
for player_puuid in team_a_puuids:
    MatchPlayer.objects.create(
        match=match,
        player_puuid=player_puuid,
        team='team_a',  # ← Is this being set?
        is_captain=(player_puuid == team_a_captain_puuid),  # ← Is captain being assigned?
        # ... other fields ...
    )
```

## 🧪 **Debugging Steps**

### **Step 1: Add Server-Side Logging**

Add debug logging in `match_manager.py`:

```python
# In create_match_from_confirmation, after creating MatchPlayer entries:
logger.info(f"Match {match.id}: Created MatchPlayer entries")
logger.info(f"  Team A players: {[mp.player_puuid for mp in MatchPlayer.objects.filter(match=match, team='team_a')]}")
logger.info(f"  Team B players: {[mp.player_puuid for mp in MatchPlayer.objects.filter(match=match, team='team_b')]}")
logger.info(f"  Team A captain: {MatchPlayer.objects.filter(match=match, team='team_a', is_captain=True).first()}")
logger.info(f"  Team B captain: {MatchPlayer.objects.filter(match=match, team='team_b', is_captain=True).first()}")
```

### **Step 2: Verify Match Data Payload**

Add logging in `consumers.py` in `handle_get_match_data`:

```python
logger.info(f"[GET_MATCH_DATA] Sending match data for match {match_id}")
logger.info(f"  Team A players: {[p['puuid'][:8] + '...' for p in team_a_players]}")
logger.info(f"  Team B players: {[p['puuid'][:8] + '...' for p in team_b_players]}")
logger.info(f"  Team A captain: {[p['alias'] for p in team_a_players if p.get('is_captain')]}")
logger.info(f"  Team B captain: {[p['alias'] for p in team_b_players if p.get('is_captain')]}")
```

### **Step 3: Compare Bot PUUIDs**

In the bot script, add this logging (already exists but verify it's enabled):

```python
logger.debug(f"Bot {self.bot_alias} PUUID: {self.bot_puuid}")
logger.debug(f"Team A players: {[p.get('puuid') for p in team_a_players]}")
logger.debug(f"Team B players: {[p.get('puuid') for p in team_b_players]}")
```

Then compare:
- Bot's PUUID format
- Server's PUUID format in the payload
- Are they identical? Case-sensitive? String vs UUID object?

## 🎯 **Most Likely Issues**

### **Issue #1: MatchPlayer Team Assignment**
```python
# WRONG:
MatchPlayer.objects.create(
    match=match,
    player_puuid=puuid,
    # team field not set or set to None
)

# CORRECT:
MatchPlayer.objects.create(
    match=match,
    player_puuid=puuid,
    team='team_a',  # or 'team_b'
    is_captain=True,  # for captain players
)
```

### **Issue #2: Captain Selection Not Happening**
```python
# MISSING:
# No captain selection logic

# NEEDED:
team_a_captain = random.choice(team_a_puuids)
team_b_captain = random.choice(team_b_puuids)

for puuid in team_a_puuids:
    MatchPlayer.objects.create(
        match=match,
        player_puuid=puuid,
        team='team_a',
        is_captain=(puuid == team_a_captain),  # Only one gets True
    )
```

### **Issue #3: Match Data Query Missing is_captain**
```python
# WRONG:
team_a_players = [
    {
        'puuid': mp.player_puuid,
        'alias': mp.player_alias,
        # is_captain field missing!
    }
    for mp in match_players if mp.team == 'team_a'
]

# CORRECT:
team_a_players = [
    {
        'puuid': mp.player_puuid,
        'alias': mp.player_alias,
        'is_captain': mp.is_captain,  # Include this!
    }
    for mp in match_players if mp.team == 'team_a'
]
```

## 📝 **Recommendation**

1. **Run the bot test with debug logging enabled**
2. **Check Django logs** for:
   - MatchPlayer creation logs
   - Match data payload contents
3. **Compare the PUUIDs** between bot logs and server logs
4. **Verify the `handle_get_match_data` payload** includes `is_captain` field

Once we see the actual server logs, we can pinpoint exactly where the issue is.

## 🔧 **Quick Test**

To verify if this is a server issue, you can temporarily modify the bot script to log the RAW match_data payload:

```python
async def _handle_match_data(self, payload: dict):
    """Handle match data (veto phase initialization)"""
    logger.info(f"🎮 Bot {self.bot_alias} received match data")
    logger.info(f"📦 RAW PAYLOAD: {json.dumps(payload, indent=2)}")  # ADD THIS
    # ... rest of the code ...
```

This will show us EXACTLY what the server is sending, which will reveal if the issue is:
- Missing player data
- Missing is_captain field
- Incorrect PUUID format
- Or something else entirely

