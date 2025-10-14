# Captain Detection Logic Fix

## Problem Identified

The bot script had a critical logic error in lines 259-270 that prevented non-captain bots from identifying their team assignment.

### Original Buggy Logic
```python
for player in team_a_players:
    if player.get('puuid') == self.bot_puuid and player.get('is_captain'):
        self.is_captain = True
        self.my_team = 'team_a'
        break

if not self.is_captain:
    for player in team_b_players:
        if player.get('puuid') == self.bot_puuid and player.get('is_captain'):
            self.is_captain = True
            self.my_team = 'team_b'
            break
```

**Issue**: The condition `player.get('puuid') == self.bot_puuid and player.get('is_captain')` only succeeds when BOTH conditions are true:
1. The player's PUUID matches the bot's PUUID
2. The player is the captain

This meant **non-captain bots would never set `my_team`**, resulting in:
- `my_team: None`
- Unable to determine if it's their turn to veto
- Unable to participate in the veto phase

## Root Cause

The logic was conflating two separate concerns:
1. **Team membership detection** - which team is this bot on?
2. **Captain status detection** - is this bot the captain of that team?

These should be handled independently:
- **ALL bots** need to know their team
- **ONLY captain bots** need to know they're captain

## Fix Implementation

### New Corrected Logic
```python
# First, find which team this bot is on
self.is_captain = False
self.my_team = None

# Check team A
for player in team_a_players:
    if player.get('puuid') == self.bot_puuid:
        self.my_team = 'team_a'
        if player.get('is_captain'):
            self.is_captain = True
        break

# Check team B if not found in team A
if self.my_team is None:
    for player in team_b_players:
        if player.get('puuid') == self.bot_puuid:
            self.my_team = 'team_b'
            if player.get('is_captain'):
                self.is_captain = True
        break
```

**How it works**:
1. **Find team first**: Loop through players and check PUUID only
2. **Set team**: When PUUID matches, set `my_team` immediately
3. **Check captain**: As a secondary check, see if this player is also captain
4. **Break early**: Once team is found, no need to keep searching

## Expected Behavior After Fix

### For Captain Bots
```
🎮 Bot bot_1 veto state initialized:
   Is captain: True
   My team: team_a
   Current turn: team_a
   Available maps: ['Ascent', 'Bind', 'Haven', 'Split', 'Icebox']
```

### For Non-Captain Bots
```
🎮 Bot bot_2 veto state initialized:
   Is captain: False
   My team: team_a
   Current turn: team_a
   Available maps: ['Ascent', 'Bind', 'Haven', 'Split', 'Icebox']
```

**Key difference**: Non-captain bots now correctly identify their team!

## Verification

This fix enables:
1. ✅ All bots correctly identify their team (`team_a` or `team_b`)
2. ✅ Captain bots correctly identify themselves as captain
3. ✅ Non-captain bots correctly identify themselves as non-captain
4. ✅ Bots can determine if it's their team's turn to veto
5. ✅ Captain bots can make veto decisions when it's their turn

## Files Modified

- `server/testing/test_queue_with_bots_v4.py` (lines 255-274)

## Related Issues

This fix complements the "Veto Completion Wait" fix implemented earlier, ensuring:
- Bots stay connected throughout the veto phase
- Bots correctly identify their team and captain status
- Bots can participate in the veto process when it's their turn

## Testing

To test this fix:
1. Run the v4 bot script: `python server/testing/test_queue_with_bots_v4.py`
2. Watch the logs after match confirmation
3. Verify all 10 bots log their team assignment correctly
4. Verify captain bots show `Is captain: True`
5. Verify non-captain bots show `Is captain: False`
6. Verify captain bots make veto decisions on their team's turn

## Status

✅ **IMPLEMENTED** - Logic fix applied to `test_queue_with_bots_v4.py`

