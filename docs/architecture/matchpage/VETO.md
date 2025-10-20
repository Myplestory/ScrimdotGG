# Match Page & Veto System Implementation

 

## Overview

This document details the implementation of the match page system with map veto functionality. The system handles the flow from match acceptance through map selection.

---

## Components Implemented

### Backend

#### 1. Database Models (`server/matchmaking/models_match.py`)

**Match Model**
- Tracks complete match lifecycle
- States: CONFIRMED → VETO → SIDE_SELECTION → CREATING → READY → IN_PROGRESS → COMPLETED
- Stores team compositions, veto state, and game details
- Indexed on state, veto_deadline, and created_at

**MatchPlayer Model**
- Tracks individual player state within match
- Connection tracking (joined_pregame, is_ready)
- Join retry tracking for late joiners
- Unique constraint on (match, player_puuid)

**VetoAction Model**
- Audit trail for all veto actions
- Records: map name, team, player, timestamp
- Tracks timeout vs manual actions
- Ordered by sequence number

#### 2. Match Manager (`server/matchmaking/match_manager.py`)

**MatchManager Class**
- `create_match_from_confirmation()` - Creates Match instance from accepted match
- `start_veto()` - Initializes veto phase (higher MMR team bans first)
- `process_veto()` - Handles veto actions with validation
- `handle_veto_timeout()` - Auto-veto on timeout
- `get_match_data()` - Retrieves complete match state for frontend

**Features:**
- Snake draft veto (Team A → Team B → repeat)
- Captain-only veto authority
- 30-second timeout per veto
- Auto-veto random map on timeout
- Automatic transition to side selection when 1 map remains

#### 3. Match Confirmation Extension (`server/matchmaking/match_confirmation.py`)

**New Function: `transition_to_match()`**
- Called when all players accept
- Creates Match instance
- Broadcasts `match_confirmed` event to all players
- Starts veto phase automatically
- Cleans up match confirmation data

**Integration:**
- Hooked into `accept_match()` function
- Triggers when `all_accepted == True`
- Seamless transition from acceptance to veto

#### 4. WebSocket Events (`server/matchmaking/consumers.py`)

**Outgoing Events (Server → Client):**
- `match_confirmed` - All players accepted, redirect to match page
- `veto_started` - Veto phase begun
- `map_vetoed` - A map was vetoed
- `veto_timeout` - Timeout occurred, auto-veto
- `veto_complete` - Veto finished, final map selected

**Incoming Events (Client → Server):**
- `get_match_data` - Request match state
- `veto_map` - Captain vetoes a map

**Features:**
- Players auto-join `match_{match_id}` group
- Real-time veto updates to all 10 players
- Validation: only captains can veto
- Turn enforcement

#### 5. Celery Task (`server/matchmaking/tasks.py`)

**Task: `check_veto_timeouts`**
- Runs every 5 seconds
- Finds matches with expired veto deadlines
- Auto-vetos random map
- Broadcasts timeout event
- Advances veto sequence or completes veto

**Added to Beat Schedule (`server/scrimgg/celery.py`):**
```python
'check-veto-timeouts': {
    'task': 'matchmaking.tasks.check_veto_timeouts',
    'schedule': 5.0,  # Run every 5 seconds
},
```

---

### Frontend

#### 1. Match Page Component (`client/frontend/src/pages/MatchPage.jsx`)

**Features:**
- Unique URL: `/match/{matchId}`
- Auto-fetches match data on load
- Joins `match_{matchId}` WebSocket group
- Real-time veto updates

**Sections:**
- **Match Header** - Match ID, quality, state
- **Teams Display** - Both teams with player details, MMR, captain indicators
- **Veto Phase** - Interactive map selection, countdown timer
- **Veto History** - Timeline of all veto actions
- **Final Map** - Displayed after veto complete

**UI Features:**
- Captain identification (⭐ icon)
- Current player highlight (blue/red border)
- Team color coding (Team A: blue, Team B: red)
- Clickable maps (captain only, on their turn)
- Real-time countdown timer
- Timeout indicators

#### 2. Routing (`client/frontend/src/App.js`)

**Added Route:**
```javascript
<Route path="/match/:matchId" element={<MatchPage />} />
```

#### 3. Auto-Redirect (`client/frontend/src/pages/PugQueue.jsx`)

**Integration:**
- Listen for `match_confirmed` event
- Auto-navigate to `/match/{matchId}`
- Close acceptance modal
- Seamless transition

---

## Data Flow

### 1. Match Acceptance Complete

```
Player 10 accepts
    ↓
MatchConfirmationManager.accept_match()
    ↓
all_accepted == true
    ↓
MatchConfirmationManager.transition_to_match()
    ↓
MatchManager.create_match_from_confirmation()
    ↓
Match instance created (state: CONFIRMED)
MatchPlayer entries created (10 players)
    ↓
Broadcast match_confirmed to all 10 players
    ↓
Frontend auto-redirects to /match/{matchId}
```

### 2. Veto Phase Starts

```
MatchManager.start_veto(match)
    ↓
Determine starting team (higher MMR)
Update match state → VETO
Set veto_turn, veto_deadline (30s)
    ↓
Broadcast veto_started
    ↓
Frontend displays veto UI
Captain sees clickable maps
Countdown timer starts
```

### 3. Captain Vetoes Map

```
Frontend: Captain clicks map
    ↓
sendEvent('veto_map', { match_id, map })
    ↓
Consumer: handle_veto_map()
    ↓
Validate: correct team, correct turn, captain only
    ↓
MatchManager.process_veto()
    ↓
Add to vetoed_maps
Create VetoAction record
    ↓
Check remaining maps:
  - If 1 remains → veto_complete
  - Else → switch turns, reset deadline
    ↓
Broadcast map_vetoed or veto_complete
    ↓
Frontend updates UI
Next team's turn (or final map display)
```

### 4. Veto Timeout

```
30 seconds elapse
    ↓
Celery task check_veto_timeouts (every 5s)
    ↓
Find match with veto_deadline < now
    ↓
MatchManager.handle_veto_timeout()
    ↓
Auto-select random available map
Create VetoAction (was_timeout=True)
    ↓
Broadcast veto_timeout event
    ↓
Frontend displays timeout indicator
Veto continues or completes
```

---

## Database Schema

### Match Table
```sql
CREATE TABLE matchmaking_match (
    id UUID PRIMARY KEY,
    state VARCHAR(20),
    match_confirmation_id VARCHAR(100) UNIQUE,
    
    -- Teams
    team_a_lobbies JSON,
    team_b_lobbies JSON,
    team_a_players JSON,
    team_b_players JSON,
    team_a_captain_puuid VARCHAR(100),
    team_b_captain_puuid VARCHAR(100),
    
    -- Veto
    map_pool JSON,
    vetoed_maps JSON,
    veto_history JSON,
    final_map VARCHAR(50),
    veto_turn VARCHAR(10),
    veto_deadline TIMESTAMP,
    veto_started_at TIMESTAMP,
    
    -- Match details
    server_region VARCHAR(20),
    match_quality FLOAT,
    team_a_avg_mmr FLOAT,
    team_b_avg_mmr FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    INDEX (state, created_at),
    INDEX (veto_deadline)
);
```

### MatchPlayer Table
```sql
CREATE TABLE matchmaking_match_player (
    id SERIAL PRIMARY KEY,
    match_id UUID REFERENCES matchmaking_match(id),
    player_puuid VARCHAR(100),
    player_alias VARCHAR(100),
    player_elo INTEGER,
    player_mmr FLOAT,
    
    -- Team & role
    team VARCHAR(10),
    is_captain BOOLEAN,
    
    -- Connection
    is_ready BOOLEAN,
    joined_pregame BOOLEAN,
    joined_at TIMESTAMP,
    join_attempts INTEGER,
    last_join_attempt TIMESTAMP,
    
    -- Activity
    last_seen TIMESTAMP,
    connection_issues INTEGER,
    created_at TIMESTAMP,
    
    UNIQUE (match_id, player_puuid),
    INDEX (match_id, joined_pregame),
    INDEX (player_puuid, match_id)
);
```

### VetoAction Table
```sql
CREATE TABLE matchmaking_veto_action (
    id SERIAL PRIMARY KEY,
    match_id UUID REFERENCES matchmaking_match(id),
    
    action_type VARCHAR(10),  -- 'BAN', 'PICK', 'TIMEOUT'
    map_name VARCHAR(50),
    team VARCHAR(10),
    player_puuid VARCHAR(100),
    
    sequence_number INTEGER,
    was_timeout BOOLEAN,
    created_at TIMESTAMP,
    
    INDEX (match_id, sequence_number)
);
```

---

## WebSocket Event Reference

### match_confirmed
Sent after all players accept. Triggers redirect to match page.

**Payload:**
```json
{
  "event": "match_confirmed",
  "data": {
    "match_id": "uuid-here",
    "team": "team_a",
    "redirect_url": "/match/uuid-here"
  }
}
```

**Frontend Action:**
```javascript
navigate(`/match/${payload.match_id}`);
```

---

### veto_started
Veto phase has begun.

**Payload:**
```json
{
  "event": "veto_started",
  "data": {
    "match_id": "uuid-here",
    "current_turn": "team_a",
    "available_maps": ["Ascent", "Bind", "Haven", ...],
    "deadline": "2025-10-13T20:30:00Z"
  }
}
```

**Frontend Action:**
- Display veto UI
- Start countdown timer
- Highlight current team's turn

---

### map_vetoed
A team vetoed a map.

**Payload:**
```json
{
  "event": "map_vetoed",
  "data": {
    "match_id": "uuid-here",
    "map": "Ascent",
    "vetoed_by": "team_a",
    "next_turn": "team_b",
    "remaining_maps": ["Bind", "Haven", ...],
    "deadline": "2025-10-13T20:30:30Z"
  }
}
```

**Frontend Action:**
- Add map to vetoed list
- Update available maps
- Switch turn indicator
- Reset countdown timer

---

### veto_timeout
Veto deadline expired, auto-veto occurred.

**Payload:**
```json
{
  "event": "veto_timeout",
  "data": {
    "match_id": "uuid-here",
    "auto_vetoed_map": "Icebox",
    "veto_complete": false,
    "next_turn": "team_b",
    "remaining_maps": ["Bind", "Haven"],
    "deadline": "2025-10-13T20:31:00Z",
    "final_map": null
  }
}
```

**Frontend Action:**
- Display timeout notification
- Add auto-vetoed map to history
- Continue veto or transition to final map

---

### veto_complete
Veto phase complete, final map selected.

**Payload:**
```json
{
  "event": "veto_complete",
  "data": {
    "match_id": "uuid-here",
    "final_map": "Haven",
    "side_selector": "team_b"
  }
}
```

**Frontend Action:**
- Hide veto UI
- Display final map prominently
- Transition to side selection phase

---

## Client → Server Events

### get_match_data
Request match state.

**Sent:**
```json
{
  "event": "get_match_data",
  "payload": {
    "match_id": "uuid-here"
  }
}
```

**Response:** `match_data` event with complete match state

---

### veto_map
Captain vetoes a map.

**Sent:**
```json
{
  "event": "veto_map",
  "payload": {
    "match_id": "uuid-here",
    "map": "Ascent"
  }
}
```

**Validation:**
- Player must be captain
- Must be their team's turn
- Map must be available (not already vetoed)

**Response:** `map_vetoed` or `veto_complete` event

---

## Usage Flow

### Step 1: All Players Accept Match

1. Last player accepts via PugQueue
2. Backend detects `all_accepted == true`
3. `transition_to_match()` called automatically
4. Match instance created in database
5. `match_confirmed` event sent to all 10 players
6. Frontend auto-redirects to `/match/{matchId}`

### Step 2: Match Page Loads

1. Component mounts with `matchId` from URL
2. Sends `get_match_data` event
3. Receives match data response
4. Joins `match_{matchId}` WebSocket group
5. Displays teams and match info

### Step 3: Veto Phase Begins

1. Backend automatically starts veto after match creation
2. `veto_started` event broadcast
3. Frontend displays veto UI
4. Timer countdown starts (30s)
5. Current turn highlighted

### Step 4: Captains Veto Maps

1. Captain clicks map (if their turn)
2. `veto_map` event sent to server
3. Server validates and processes
4. `map_vetoed` event broadcast to all players
5. UI updates: map removed, turn switches, timer resets
6. Repeat until 1 map remains

### Step 5: Veto Complete

1. Only 1 map remains
2. `veto_complete` event broadcast
3. Frontend displays final map
4. Match state → SIDE_SELECTION
5. Ready for next phase

---

## Configuration

### Timing Constants

```python
# server/matchmaking/match_manager.py
VETO_TIMEOUT_SECONDS = 30  # 30 seconds per veto
SIDE_SELECTION_TIMEOUT_SECONDS = 15  # 15 seconds for side selection
```

### Celery Schedule

```python
# server/scrimgg/celery.py
'check-veto-timeouts': {
    'task': 'matchmaking.tasks.check_veto_timeouts',
    'schedule': 5.0,  # Check every 5 seconds
}
```

---

## Testing Checklist

### Backend Tests
- [ ] Match creation from confirmation
- [ ] Veto turn validation
- [ ] Captain-only veto enforcement
- [ ] Timeout auto-veto
- [ ] Veto completion detection
- [ ] WebSocket event broadcasting

### Frontend Tests
- [ ] Auto-redirect on match_confirmed
- [ ] Match data fetch and display
- [ ] Team assignments correct
- [ ] Captain identification
- [ ] Veto UI interactive (captain only)
- [ ] Countdown timer accuracy
- [ ] Real-time veto updates
- [ ] History display

### Integration Tests
- [ ] 10-player full flow
- [ ] Both captains veto successfully
- [ ] Timeout auto-veto works
- [ ] Page refresh maintains state
- [ ] WebSocket reconnection handling

---

## Next Steps

### Phase 2: Side Selection
- [ ] Add `handle_select_side` to consumers
- [ ] Implement side selection UI component
- [ ] Add timeout handling for side selection
- [ ] Broadcast side selection complete

### Phase 3: Custom Game Creation
- [ ] Select constructor (Team A captain)
- [ ] Send `create_custom_game` to constructor client
- [ ] Handle `custom_game_created` response
- [ ] Broadcast `join_custom_game` to other players
- [ ] Track pregame joins

### Phase 4: Match Start
- [ ] Monitor all 10 players joined
- [ ] Constructor starts custom game
- [ ] Transition to IN_PROGRESS state
- [ ] Begin match monitoring

---

## Migration Command

```bash
# Create migrations for new models
cd server
pipenv run python manage.py makemigrations matchmaking

# Apply migrations
pipenv run python manage.py migrate

# Restart services to load new code
# 1. Restart Celery Beat (for new veto timeout task)
# 2. Restart Celery Worker (for new task handler)
# 3. Restart Daphne (for new WebSocket events)
```

---

## Files Modified/Created

### Backend
- ✅ `server/matchmaking/models_match.py` (NEW)
- ✅ `server/matchmaking/match_manager.py` (NEW)
- ✅ `server/matchmaking/match_confirmation.py` (MODIFIED)
- ✅ `server/matchmaking/consumers.py` (MODIFIED)
- ✅ `server/matchmaking/tasks.py` (MODIFIED)
- ✅ `server/scrimgg/celery.py` (MODIFIED)

### Frontend
- ✅ `client/frontend/src/pages/MatchPage.jsx` (NEW)
- ✅ `client/frontend/src/pages/PugQueue.jsx` (MODIFIED)
- ✅ `client/frontend/src/App.js` (MODIFIED)

### Documentation
- ✅ `docs/MATCH_PAGE_IMPLEMENTATION_PLAN.md` (NEW)
- ✅ `docs/MATCH_PAGE_VETO_IMPLEMENTATION.md` (NEW - this file)

---

 


