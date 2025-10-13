# Critical Team Balance Bug Fix

## 🚨 **Critical Issue Identified**

The matchmaking system is creating **unbalanced teams (4v6 instead of 5v5)** due to incorrect snake draft logic in `MatchmakerV2`.

## 🐛 **Root Cause**

**File**: `server/matchmaking/matchmaker_v2.py`  
**Lines**: 435 (async) and 1033 (sync)

**Broken Code:**
```python
# Current INCORRECT logic
for i, player in enumerate(sorted_players):
    if i % 4 < 2:  # ❌ This creates 6v4 teams!
        team_a.append(player)
    else:
        team_b.append(player)
```

**Problem Analysis:**
For 10 players (indices 0-9), this creates:
- **Team A**: Players 0, 1, 4, 5, 8, 9 = **6 players** ❌
- **Team B**: Players 2, 3, 6, 7 = **4 players** ❌

## ✅ **Solution**

**Correct Snake Draft Logic:**
```python
# Fixed CORRECT logic for 5v5 balance
for i, player in enumerate(sorted_players):
    # Snake draft pattern: A-B-B-A-A-B-B-A-A-B
    if i == 0 or (i >= 3 and i <= 4) or (i >= 7 and i <= 8):
        team_a.append(player)
    else:
        team_b.append(player)
```

**Or more elegantly:**
```python
# Alternative implementation
snake_pattern = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1]  # A=0, B=1
for i, player in enumerate(sorted_players):
    if snake_pattern[i] == 0:
        team_a.append(player)
    else:
        team_b.append(player)
```

**Result:**
- **Team A**: Players 0, 3, 4, 7, 8 = **5 players** ✅
- **Team B**: Players 1, 2, 5, 6, 9 = **5 players** ✅

## 🎯 **Snake Draft Explanation**

A proper snake draft for competitive balance should follow this pattern:
1. **Highest MMR** → Team A
2. **2nd & 3rd highest** → Team B  
3. **4th & 5th highest** → Team A
4. **6th & 7th highest** → Team B
5. **8th & 9th highest** → Team A
6. **Lowest MMR** → Team B

This ensures both teams get a mix of high and low skill players.

## 🔧 **Files to Fix**

### 1. Async Version
**File**: `server/matchmaking/matchmaker_v2.py`  
**Line**: ~435

```python
@staticmethod
async def _balance_teams_mmr(players: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Balance players into two teams using MMR.
    Uses proper snake draft for 5v5 fairness.
    """
    # Sort by MMR (descending)
    sorted_players = sorted(players, key=lambda p: p.get('mmr', p.get('elo', 0)), reverse=True)
    
    team_a = []
    team_b = []
    
    # Proper 5v5 snake draft: A-B-B-A-A-B-B-A-A-B
    snake_pattern = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1]  # A=0, B=1
    
    for i, player in enumerate(sorted_players):
        if i < len(snake_pattern):
            if snake_pattern[i] == 0:
                team_a.append(player)
            else:
                team_b.append(player)
        else:
            # Fallback for more than 10 players (shouldn't happen in 5v5)
            if len(team_a) <= len(team_b):
                team_a.append(player)
            else:
                team_b.append(player)
    
    return team_a, team_b
```

### 2. Sync Version  
**File**: `server/matchmaking/matchmaker_v2.py`  
**Line**: ~1033

```python
@staticmethod
def _balance_teams_mmr_sync(players: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Balance players into two teams using MMR - SYNC version.
    Uses proper snake draft for 5v5 fairness.
    """
    # Sort by MMR (descending)
    sorted_players = sorted(players, key=lambda p: p.get('mmr', p.get('elo', 0)), reverse=True)
    
    team_a = []
    team_b = []
    
    # Proper 5v5 snake draft: A-B-B-A-A-B-B-A-A-B
    snake_pattern = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1]  # A=0, B=1
    
    for i, player in enumerate(sorted_players):
        if i < len(snake_pattern):
            if snake_pattern[i] == 0:
                team_a.append(player)
            else:
                team_b.append(player)
        else:
            # Fallback for more than 10 players (shouldn't happen in 5v5)
            if len(team_a) <= len(team_b):
                team_a.append(player)
            else:
                team_b.append(player)
    
    return team_a, team_b
```

## 🧪 **Testing the Fix**

### Test Case: 10 Players by MMR
```python
players = [
    {'alias': 'Player1', 'mmr': 2000},  # Highest
    {'alias': 'Player2', 'mmr': 1900},
    {'alias': 'Player3', 'mmr': 1800},
    {'alias': 'Player4', 'mmr': 1700},
    {'alias': 'Player5', 'mmr': 1600},
    {'alias': 'Player6', 'mmr': 1500},
    {'alias': 'Player7', 'mmr': 1400},
    {'alias': 'Player8', 'mmr': 1300},
    {'alias': 'Player9', 'mmr': 1200},
    {'alias': 'Player10', 'mmr': 1100}  # Lowest
]

# Expected Result:
# Team A: Player1 (2000), Player4 (1700), Player5 (1600), Player8 (1300), Player9 (1200)
# Team B: Player2 (1900), Player3 (1800), Player6 (1500), Player7 (1400), Player10 (1100)
# 
# Team A Average: (2000+1700+1600+1300+1200)/5 = 1560
# Team B Average: (1900+1800+1500+1400+1100)/5 = 1540
# Difference: 20 MMR (very balanced!)
```

## 🚨 **Immediate Action Required**

This is a **critical bug** that affects match fairness and should be fixed immediately:

1. **Priority**: CRITICAL - affects all matches
2. **Impact**: Unbalanced 4v6 teams instead of fair 5v5
3. **User Experience**: Poor match quality, unfair games
4. **Competitive Integrity**: Compromised due to team imbalance

## 📋 **Implementation Steps**

1. **Fix both async and sync versions** of `_balance_teams_mmr()`
2. **Test with various player counts** (exactly 10 players)
3. **Verify team balance** in logs and database
4. **Monitor match quality** after deployment
5. **Add unit tests** to prevent regression

## 🔍 **Additional Validation**

After fixing, add validation to ensure teams are always balanced:

```python
def validate_team_balance(team_a: List[Dict], team_b: List[Dict]) -> bool:
    """Validate that teams are properly balanced (5v5)"""
    if len(team_a) != 5 or len(team_b) != 5:
        logger.error(f"Team imbalance detected: Team A={len(team_a)}, Team B={len(team_b)}")
        return False
    return True
```

This bug explains why matches are showing 4v6 instead of the expected 5v5 balance!
