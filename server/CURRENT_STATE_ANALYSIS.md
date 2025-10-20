# Current State Analysis - What Exists vs What Should Exist

## 📊 Current Architecture Problems

### **Problem 1: Veto Logic in Wrong App**

**Current location:** `matchmaking/match_manager.py` (1005 lines)
- Contains ALL server/map veto logic
- Contains side selection logic
- Contains custom game creation logic
- **This is PREGAME logic, NOT matchmaking logic!**

**Should be in:** `match_system/managers/match_manager.py`

---

### **Problem 2: Duplicate Models**

**Models exist in TWO places:**
1. ✅ `match_system/models.py` - Contains `Match`, `MatchPlayer`, `VetoAction` (CORRECT)
2. ❌ `matchmaking/models_match.py` - Contains same models (LEGACY, WRONG)

**Problem:** Code still imports from the WRONG location:
- `matchmaking/consumers.py` - imports `matchmaking.models_match`
- `matchmaking/match_manager.py` - imports `matchmaking.models_match`
- `matchmaking/tasks.py` - imports `matchmaking.models_match`
- `matchmaking/models.py` - imports `matchmaking.models_match`

---

### **Problem 3: Broken Stub Pattern**

**Current `match_system/managers/match_manager.py`:**
```python
# Lines 12-23: Tries to wrap matchmaking.match_manager
try:
    from match_manager import MatchManager as _MatchManager  # ❌ Fails
except ImportError:
    class MatchManager:  # ❌ Returns NotImplementedError
        raise NotImplementedError("MatchManager not yet migrated")
```

**This is wrong because:**
- Import path manipulation doesn't work
- Falls back to stub that raises errors
- Creates unnecessary coupling
- Veto logic SHOULD be in match_system, not wrapped

---

## ✅ What Should Exist

### **`matchmaking` App - Match Finding ONLY**

```
matchmaking/
├── queue_manager.py          ✅ Queue operations (CORRECT)
├── matchmaker.py             ✅ Match algorithm (CORRECT)
├── matchmaker_v2.py          ✅ MMR algorithm (CORRECT)
├── match_confirmation.py     ✅ Acceptance phase (CORRECT)
├── lobby_manager.py          ⚠️  Should move to lobby/ app
├── models.py                 ✅ Lobby models (CORRECT)
├── models_match.py           ❌ DELETE (duplicate)
├── match_manager.py          ❌ MOVE veto logic out
├── consumers.py              ❌ DELETE (moved to realtime/)
└── tasks.py                  ✅ Matchmaking tasks (CORRECT)
```

**Responsibilities:**
- Add lobbies to queue
- Find compatible matches using algorithms
- Create match confirmations
- Handle acceptance/decline
- Timeout unaccepted matches
- Requeue with priority

---

### **`match_system` App - Pregame Setup**

```
match_system/
├── models.py                              ✅ Match models (EXISTS)
├── managers/
│   ├── confirmation_manager.py            ✅ Wrapper for acceptance (OK)
│   ├── match_manager.py                   ❌ NEEDS veto logic moved here
│   └── veto_manager.py                    ❌ Empty placeholder
└── tasks.py                               ⚠️  Should have veto timeout tasks
```

**What SHOULD be in `match_system/managers/match_manager.py`:**
```python
from match_system.models import Match, MatchPlayer, VetoAction
from channels.layers import get_channel_layer

class MatchManager:
    """Pregame veto and setup - OWNS this logic, not wrapping"""
    
    @staticmethod
    async def create_match_from_confirmation(match_confirmation_id):
        """Create Match from confirmed acceptance"""
        # Get data from matchmaking.MatchConfirmationManager
        # Create Match instance in match_system.models
        # Start veto phase
        pass
    
    @staticmethod
    async def start_server_veto(match):
        """Initialize server veto"""
        # Update match state
        # Broadcast to players
        pass
    
    @staticmethod
    async def veto_server(match_id, player_puuid, server_name):
        """Process server veto + broadcast"""
        # Validate player/turn
        # Update Match model
        # Broadcast via channel_layer
        pass
    
    @staticmethod
    async def veto_map(match_id, player_puuid, map_name):
        """Process map veto + broadcast"""
        pass
    
    @staticmethod
    async def select_side(match_id, player_puuid, side):
        """Process side selection + broadcast"""
        pass
    
    @staticmethod
    async def get_match_data(match_id):
        """Get current match state"""
        pass
```

**Responsibilities:**
- Create Match from confirmation
- Server veto orchestration
- Map veto orchestration
- Side selection
- Broadcasting veto updates
- Custom game creation coordination
- Timeout handling for veto phases

---

### **`match_execution` App - Live Game**

```
match_execution/
├── models.py                 (if needed for game stats)
├── managers/
│   └── execution_manager.py  ✅ Game tracking
└── tasks.py                  (score updates, etc)
```

**Responsibilities:**
- Track game state (rounds, score)
- Log player stats
- Update match progress
- Handle game completion
- Calculate results

---

## 🔄 Migration Path

### **Step 1: Move Veto Logic**

**From:** `matchmaking/match_manager.py`  
**To:** `match_system/managers/match_manager.py`

**Methods to move:**
```python
✅ create_match_from_confirmation()
✅ _extract_team_lobbies()
✅ _extract_team_players()
✅ _create_match_players()
✅ start_server_veto()
✅ process_server_veto()
✅ process_map_veto()
✅ get_match_data()
✅ handle_server_veto_timeout()
✅ handle_map_veto_timeout_sync()
✅ handle_side_selection_timeout_sync()
✅ process_side_selection()
✅ process_side_selection_sync()
```

**Add broadcasting to each method** (orchestration layer)

---

### **Step 2: Update Model Imports**

**Find and replace throughout codebase:**

```python
# OLD (wrong):
from matchmaking.models_match import Match, MatchPlayer, VetoAction

# NEW (correct):
from match_system.models import Match, MatchPlayer, VetoAction
```

**Files to update:**
- `matchmaking/consumers.py` (if not deleted)
- `matchmaking/match_manager.py`
- `matchmaking/tasks.py`
- `matchmaking/models.py`
- `matchmaking/match_confirmation.py`

---

### **Step 3: Update Handler Imports**

**`realtime/handlers/veto_handler.py`:**
```python
# Already imports from match_system (correct)
from match_system.managers import MatchManager

# But MatchManager is broken stub
# After Step 1, this will work correctly
```

---

### **Step 4: Update Tasks**

**Move veto timeout tasks:**

**From:** `matchmaking/tasks.py`  
**To:** `match_system/tasks.py`

```python
# These belong in match_system:
- cleanup_expired_matches()
- check_veto_timeouts()
```

**Keep in matchmaking:**
```python
# These belong in matchmaking:
- periodic_matchmaking()
- cleanup_match_confirmations()
```

---

### **Step 5: Clean Up**

1. **Delete** `matchmaking/models_match.py`
2. **Remove** veto methods from `matchmaking/match_manager.py`
3. **Update** `matchmaking/match_confirmation.py` import paths
4. **Test** that veto flow works end-to-end

---

## 🎯 End Result: Proper Separation

```
┌─────────────────────────────────────────────────┐
│ MATCHMAKING APP                                 │
│ - Queue management                              │
│ - Find matches (algorithm)                      │
│ - Match acceptance/confirmation                 │
└──────────────────┬──────────────────────────────┘
                   │ transitions when all accept
                   ↓
┌─────────────────────────────────────────────────┐
│ MATCH_SYSTEM APP                                │
│ - Create Match from confirmation                │
│ - Server/map veto                               │
│ - Side selection                                │
│ - Custom game coordination                      │
└──────────────────┬──────────────────────────────┘
                   │ transitions when game starts
                   ↓
┌─────────────────────────────────────────────────┐
│ MATCH_EXECUTION APP                             │
│ - Track live game                               │
│ - Score updates                                 │
│ - Stats logging                                 │
└─────────────────────────────────────────────────┘
```

**Each app is self-contained with its own models, business logic, and orchestration.**

**No wrappers. No cross-app dependencies beyond necessary data passing.**

