# Veto System Refactor Plan - Proper Separation of Concerns

## 🎯 Problem Identified

Currently, veto logic is in the **WRONG APP**:
- ❌ `matchmaking/match_manager.py` contains ALL veto/pregame logic
- ❌ `matchmaking/models_match.py` contains Match/VetoAction models  
- ❌ Creating **wrappers** instead of **moving logic**

## ✅ Correct Architecture

### **App #1: `matchmaking` - Queue & Match Finding ONLY**
**Responsibility:** Find compatible matches using algorithms

**What belongs here:**
- ✅ Queue management (`QueueManager`)
- ✅ Match finding algorithms (`Matchmaker`, `MatchmakerV2`)
- ✅ Match confirmation/acceptance phase (`MatchConfirmationManager`)
- ✅ Requeuing with priority bias
- ✅ Acceptance counting/timeout

**What does NOT belong:**
- ❌ Match models (Move to `match_system`)
- ❌ Veto logic (Move to `match_system`)
- ❌ Custom game creation (Move to `match_system`)

---

### **App #2: `match_system` - Pregame Veto & Setup**
**Responsibility:** Handle everything AFTER acceptance, BEFORE game starts

**What belongs here:**
- ✅ Match models (`Match`, `MatchPlayer`, `VetoAction`) - **ALREADY MOVED!**
- ✅ Create Match from confirmation
- ✅ Server veto logic
- ✅ Map veto logic  
- ✅ Side selection
- ✅ Custom game creation coordination
- ✅ Veto timeout handling
- ✅ Broadcasting match/veto updates

**Current Status:**
- ✅ Models exist in `match_system/models.py`
- ❌ Business logic still in `matchmaking/match_manager.py`
- ❌ Imports still referencing `matchmaking.models_match`

---

### **App #3: `match_execution` - During Game**
**Responsibility:** Handle live game state

**What belongs here:**
- ✅ Game state tracking
- ✅ Score updates
- ✅ Round tracking
- ✅ Stats logging
- ✅ Results display
- ✅ Post-game processing

---

## 📦 What Needs to Move

### **From `matchmaking/match_manager.py` → `match_system/managers/`**

Move these methods to `match_system/managers/match_manager.py`:

```python
# ALL of these are PREGAME logic:
- create_match_from_confirmation()
- start_server_veto()
- process_server_veto()
- process_map_veto()
- get_match_data()
- handle_server_veto_timeout()
- handle_map_veto_timeout_sync()
- handle_side_selection_timeout_sync()
- process_side_selection()
- process_side_selection_sync()
```

### **Update Imports Throughout Codebase**

Change ALL imports from:
```python
from matchmaking.models_match import Match, MatchPlayer, VetoAction
```

To:
```python
from match_system.models import Match, MatchPlayer, VetoAction
```

**Files to update:**
- `matchmaking/consumers.py` (lines 1334, 1410, 1491)
- `matchmaking/match_manager.py` (line 19)
- `matchmaking/tasks.py` (line 16)
- `matchmaking/models.py` (line 4)
- `matchmaking/match_confirmation.py` (if any imports)

---

## 🏗️ Orchestration Layer

`match_system` should have **OWN business logic**, NOT wrappers!

### **New `match_system/managers/match_manager.py`**
```python
"""
Match Manager - Pregame veto and setup orchestration.

Handles everything AFTER players accept a match, BEFORE game starts:
- Server/map veto
- Side selection  
- Custom game creation coordination
"""

from match_system.models import Match, MatchPlayer, VetoAction
from channels.layers import get_channel_layer
# Import from matchmaking ONLY for match confirmation data:
from matchmaking.match_confirmation import MatchConfirmationManager

class MatchManager:
    # MOVE all veto logic here (not wrap, MOVE)
    # Add broadcasting as part of methods
```

---

## 📝 Implementation Steps

### **Step 1: Move Business Logic**
1. Copy ALL veto methods from `matchmaking/match_manager.py`
2. Paste into `match_system/managers/match_manager.py`
3. Update model imports to `match_system.models`
4. Add broadcasting logic directly in methods (orchestration)

### **Step 2: Update All Imports**
1. Find all `from matchmaking.models_match import`
2. Replace with `from match_system.models import`
3. Find all `from matchmaking.match_manager import MatchManager`
4. Replace with `from match_system.managers import MatchManager`

### **Step 3: Update Handlers**
1. `realtime/handlers/veto_handler.py` imports `match_system.managers.MatchManager`
2. Methods call MatchManager directly (no wrappers needed)

### **Step 4: Clean Up**
1. Delete or deprecate `matchmaking/models_match.py`
2. Delete or deprecate old `matchmaking/match_manager.py` veto methods
3. Keep ONLY match-finding logic in `matchmaking`

### **Step 5: Update Tasks**
1. `match_system/tasks.py` should handle veto timeouts
2. `matchmaking/tasks.py` only handles matchmaking tasks

---

## 🎯 Result: Clean Separation

```
CLIENT REQUEST (veto_server)
    ↓
realtime/handlers/veto_handler.py
    ↓  
match_system/managers/match_manager.py
    - Validates veto action
    - Updates Match model (match_system.models.Match)
    - Broadcasts to match group
    - Returns result
    ↓
CLIENT RECEIVES UPDATE
```

**No wrappers. No cross-app dependencies. Clean separation.**

---

## ⚠️ Key Principle

**Apps should be SELF-CONTAINED:**
- Each app has its own models
- Each app has its own business logic
- Each app has its own managers
- Apps communicate via:
  - Function calls (when needed)
  - Channel layer broadcasts
  - Shared data structures (match IDs, player PUUIDs)

**Not via wrapping other apps' managers!**

