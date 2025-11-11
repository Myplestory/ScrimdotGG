# Matchmaking Pages Architecture

## Overview
Matchmaking pages handle the PUG (Pick-Up Game) queue system and scrim/custom match setup.

## Pages

### 1. Play Page (`play.jsx`)
**Purpose**: Main PUG matchmaking queue interface (FACEIT-like experience)

---

## Play Page - Full Architecture

### UI Components
- Queue selection (PUG, Ranked, Unranked)
- Map preferences selector
- Server/region preferences
- Real-time queue status display
- Player count and estimated wait time
- Match acceptance modal
- Lobby member list
- Chat interface

### Entity Relationships

#### Primary Entities
```
Player (Django)
├── puuid: string (PK)
├── username: string
├── alias: string
├── elo: int (display rank)
├── mmr: float (matchmaking rating - hidden)
├── trueskill_mu: float
├── trueskill_sigma: float
├── rank: string
├── region: string
├── games_played: int
├── is_in_placement: boolean
├── karma: int
└── Various stats fields

Lobby (Django)
├── id: UUID (PK)
├── players: ManyToMany → Player
├── lobby_leader: ForeignKey → Player
├── is_active: boolean
├── in_queue: boolean
├── queue_type: string ('pug', 'scrim', 'custom')
├── map_preferences: JSONField [list of map names]
├── server_preferences: JSONField [list of server regions]
├── average_elo: float
├── elo_range: JSONField {min, max}
├── size: int
├── max_size: int (default: 5)
├── created_at: datetime
└── queued_at: datetime

MatchConfirmation (Django - via matchmaking)
├── id: UUID (PK)
├── lobby_a: ForeignKey → Lobby
├── lobby_b: ForeignKey → Lobby
├── team_a_players: JSONField [player data]
├── team_b_players: JSONField [player data]
├── accepted_players: JSONField [list of PUUIDs]
├── declined_players: JSONField [list of PUUIDs]
├── status: string ('pending', 'accepted', 'declined', 'expired')
├── created_at: datetime
├── expires_at: datetime
└── timeout_seconds: int (default: 30)
```

### Frontend State Management

#### WebSocket Context State
```javascript
{
  // Connection state
  connected: boolean,
  authenticated: boolean,
  
  // Player state
  playerData: {
    puuid: string,
    alias: string,
    rank: string,
    elo: int,
    mmr: float,
    region: string,
    games_played: int,
    stats: {...}
  },
  
  // Lobby state
  lobbyData: {
    id: UUID,
    players: [Player],
    lobby_leader: Player,
    is_active: boolean,
    in_queue: boolean,
    queue_type: string,
    map_preferences: [string],
    server_preferences: [string],
    size: int,
    max_size: int
  },
  
  // Queue state
  queueStatus: {
    in_queue: boolean,
    queue_type: string,
    estimated_wait: int, // seconds
    players_in_queue: int,
    can_queue: boolean,
    blocked_reason: string | null
  },
  
  // Match state validation
  matchStateInfo: {
    inActiveMatch: boolean,
    matchId: UUID | null,
    matchState: string | null,
    canQueue: boolean,
    blockedReason: string | null
  }
}
```

### Events & Data Flow

#### 1. Lobby Creation/Management

**Frontend → Backend**
```javascript
Event: 'create_lobby'
Payload: {
  queue_type: 'pug' | 'scrim' | 'custom',
  max_size: int (default: 5)
}
```

**Backend Processing**
1. `realtime/consumers.py` → `LobbyHandler.handle_event()`
2. `lobby_handler.py` → Create lobby in database
3. Add player to lobby
4. Join player to lobby WebSocket group
5. Broadcast lobby creation

**Backend → Frontend**
```javascript
Event: 'lobby_created'
Payload: {
  lobby: {
    id: UUID,
    players: [Player],
    lobby_leader: Player,
    queue_type: string,
    size: int,
    max_size: int
  }
}
```

#### 2. Queue Entry

**Frontend → Backend**
```javascript
Event: 'add_lobby_to_queue'
Payload: {
  lobby_id: UUID,
  map_preferences: [string], // ['Ascent', 'Bind', 'Haven']
  server_preferences: [string] // ['Virginia', 'Illinois']
}
```

**Backend Processing**
1. Validate lobby eligibility:
   - Not already in queue
   - No active matches for any member
   - Lobby size within limits
   - All players have valid region
2. Update lobby preferences in database
3. Add to Redis matchmaking queue
4. Start matchmaking algorithm
5. Broadcast queue status update

**Backend → Frontend**
```javascript
Event: 'queue_status_update'
Payload: {
  in_queue: boolean,
  lobby_id: UUID,
  queue_type: string,
  estimated_wait: int,
  players_in_queue: int,
  position_in_queue: int
}
```

#### 3. Match Found

**Backend → Frontend**
```javascript
Event: 'match_found'
Payload: {
  match_confirmation_id: UUID,
  team_a: {
    lobbies: [Lobby],
    players: [Player],
    average_elo: float
  },
  team_b: {
    lobbies: [Lobby],
    players: [Player],
    average_elo: float
  },
  timeout_seconds: int, // 30 seconds to accept
  expires_at: timestamp
}
```

**Frontend Action**
- Show match acceptance modal
- Display team compositions
- Start countdown timer
- Show accept/decline buttons

#### 4. Match Acceptance

**Frontend → Backend**
```javascript
Event: 'accept_match'
Payload: {
  match_confirmation_id: UUID
}
```

**Backend Processing**
1. Record player acceptance
2. Broadcast acceptance count to all players
3. If all players accepted:
   - Create Match entity
   - Remove lobbies from queue
   - Transition to veto phase
4. If any player declines or timeout:
   - Cancel match confirmation
   - Return lobbies to queue
   - Apply queue penalty to decliner

**Backend → Frontend (Real-time)**
```javascript
Event: 'match_acceptance_update'
Payload: {
  match_confirmation_id: UUID,
  accepted_count: int,
  total_players: int,
  accepted_players: [PUUID]
}
```

**Backend → Frontend (On Success)**
```javascript
Event: 'match_ready'
Payload: {
  match_id: UUID,
  state: 'CONFIRMED',
  redirect_to: '/match/{match_id}'
}
```

#### 5. Queue Exit

**Frontend → Backend**
```javascript
Event: 'remove_lobby_from_queue'
Payload: {
  lobby_id: UUID
}
```

**Backend Processing**
1. Remove from Redis matchmaking queue
2. Update lobby state
3. Broadcast queue exit

**Backend → Frontend**
```javascript
Event: 'queue_exited'
Payload: {
  lobby_id: UUID,
  message: 'Left queue successfully'
}
```

### Backend Django Architecture

#### Apps Involved
1. **`realtime`** - WebSocket consumer entry point
2. **`lobby`** - Lobby management business logic
3. **`matchmaking`** - Queue management and matchmaking algorithm
4. **`match_system`** - Match creation and lifecycle

#### Handlers Chain
```
RealtimeConsumer (consumers.py)
    ↓
LobbyHandler (handlers/lobby_handler.py)
    ↓
LobbyManager (lobby/manager.py) ← Need to create
    ↓
Lobby Model (scrimgg/models.py)
```

### Required Backend Implementation

#### New Django App: `lobby`
```python
# lobby/manager.py
class LobbyManager:
    async def create_lobby(self, leader_puuid, queue_type='pug', max_size=5)
    async def add_player_to_lobby(self, lobby_id, player_puuid)
    async def remove_player_from_lobby(self, lobby_id, player_puuid)
    async def update_lobby_preferences(self, lobby_id, map_prefs, server_prefs)
    async def calculate_lobby_averages(self, lobby_id)
    async def validate_lobby_for_queue(self, lobby_id)
    async def destroy_lobby(self, lobby_id)
    async def transfer_leadership(self, lobby_id, new_leader_puuid)
```

#### Queue Management
```python
# matchmaking/queue_manager.py
class QueueManager:
    async def add_lobby_to_queue(self, lobby_id, preferences)
    async def remove_lobby_from_queue(self, lobby_id)
    async def get_queue_status(self, lobby_id)
    async def check_eligibility(self, lobby_id)
    async def find_match(self, lobby_id) # Matchmaking algorithm
```

### Database Queries Needed

```python
# Get lobby with all players
lobby = await sync_to_async(
    Lobby.objects.select_related('lobby_leader')
    .prefetch_related('players')
    .get
)(id=lobby_id)

# Check if any lobby member is in active match
active_matches = await sync_to_async(
    Match.objects.filter(
        Q(team_a_players__contains=[{'puuid': puuid}]) |
        Q(team_b_players__contains=[{'puuid': puuid}]),
        status__in=['confirmed', 'in_progress']
    ).exists
)()

# Get queue statistics
queue_stats = await redis_manager.get_queue_stats('pug')
```

### Redis Data Structures

```python
# Queue entries (Redis Sorted Set)
Key: "queue:pug"
Score: timestamp (for FIFO + wait time calculation)
Value: lobby_id

# Lobby preferences (Redis Hash)
Key: f"lobby:{lobby_id}:preferences"
Fields:
  - map_preferences: JSON array
  - server_preferences: JSON array
  - average_elo: float
  - min_elo: float
  - max_elo: float

# Active match tracking (Redis Set)
Key: f"player:{puuid}:active_match"
Value: match_id
```

### Frontend Component Hierarchy

```
Play.jsx
├── QueueTypeSelector
├── MapPreferenceSelector
│   └── MapChip (clickable)
├── ServerPreferenceSelector
│   └── ServerChip (clickable)
├── LobbyMemberList
│   └── PlayerSlot (shows rank, elo, leader badge)
├── QueueStatusDisplay
│   ├── PlayersInQueue
│   ├── EstimatedWaitTime
│   └── QueueButton (Join/Leave)
├── MatchAcceptanceModal
│   ├── TeamComposition
│   │   ├── TeamAPlayers
│   │   └── TeamBPlayers
│   ├── CountdownTimer
│   ├── AcceptedPlayersList
│   └── AcceptDeclineButtons
└── ChatInterface
    ├── MessageList
    └── MessageInput
```

### Error Handling

#### Queue Eligibility Errors
```javascript
{
  error: 'queue_blocked',
  reason: 'IN_ACTIVE_MATCH' | 'ALREADY_IN_QUEUE' | 'LOBBY_TOO_SMALL' | 'LOBBY_TOO_LARGE',
  message: string,
  blocked_until: timestamp | null
}
```

#### Match Acceptance Timeout
```javascript
{
  event: 'match_cancelled',
  reason: 'TIMEOUT' | 'PLAYER_DECLINED',
  declined_by: PUUID | null,
  penalty_applied: boolean,
  return_to_queue: boolean
}
```

### Performance Considerations

1. **Queue Position Caching**: Cache queue positions in Redis to avoid repeated calculations
2. **Lobby State Caching**: Cache active lobby states to reduce database queries
3. **WebSocket Group Broadcasting**: Use Redis pub/sub for efficient multi-server broadcasting
4. **Matchmaking Algorithm**: Run asynchronously in background worker to avoid blocking WebSocket
5. **Player Status Check**: Use Redis for fast active match validation

### Testing Requirements

1. **Unit Tests**
   - Lobby creation and management
   - Queue eligibility validation
   - Match acceptance/decline logic
   
2. **Integration Tests**
   - Full queue → match found → acceptance flow
   - Multi-lobby matchmaking
   - Timeout handling
   
3. **Load Tests**
   - 100+ lobbies in queue simultaneously
   - Match acceptance with all players
   - WebSocket message throughput

---

## Implementation Status

### ✅ FULLY IMPLEMENTED

1. **Core Entity Models** (`server/scrimgg/models.py`)
   - ✅ Player model with comprehensive stats (elo, mmr, trueskill, karma, games_played, region)
   - ✅ Lobby model with queue state, preferences, leader tracking
   - ✅ Match model in match_system with full veto infrastructure

2. **WebSocket Infrastructure** (`server/realtime/`)
   - ✅ RealtimeConsumer with authentication and routing
   - ✅ LobbyHandler (`handlers/lobby_handler.py`) - handles create_lobby, invite, kick events
   - ✅ MatchHandler (`handlers/match_handler.py`) - handles match lifecycle events
   - ✅ VetoHandler (`handlers/veto_handler.py`) - handles server/map veto
   - ✅ ExecutionHandler (`handlers/execution_handler.py`) - handles custom game creation

3. **Lobby Management** (`server/matchmaking/` and `server/lobby/`)
   - ✅ LobbyManager in `matchmaking/lobby_manager.py` with create_lobby method
   - ✅ lobby Django app exists with manager.py (imports from matchmaking)

4. **Queue System** (`server/matchmaking/`)
   - ✅ QueueManager (`queue_manager.py`) - Full Redis-based queue with sorted sets
   - ✅ Enqueue/dequeue lobbies by average ELO
   - ✅ Queue eligibility validation with MatchStateValidator
   - ✅ Lobby data storage in Redis with TTL
   - ✅ Queue time tracking per lobby

5. **Matchmaking Algorithm** (`server/matchmaking/`)
   - ✅ MatchmakerV2 (`matchmaker_v2.py`) - Advanced MMR-based matching
   - ✅ Hybrid tolerance system with rank-aware tiers (elite/high/mid/low/entry)
   - ✅ Adaptive weighting for team balancing
   - ✅ TrueSkill integration for skill-based matching
   - ✅ Time-in-queue tolerance expansion

6. **Match Execution** (`server/match_system/phases/execution.py`)
   - ✅ ExecutionPhaseManager with constructor assignment
   - ✅ Custom game creation tracking
   - ✅ Player join monitoring
   - ✅ Transition to live state management

### ⚠️ PARTIALLY IMPLEMENTED / NEEDS ENHANCEMENT

1. **Lobby Model Fields** (`server/scrimgg/models.py`)
   - ⚠️ Basic fields exist (players, leader, queue state, preferences)
   - ⚠️ Missing scrim-specific fields (team_a_captain, team_b_captain, ready_check_status, scrim_format)
   - ⚠️ Missing advanced features (voice channel ID, last_activity tracking)

2. **Match Confirmation System**
   - ⚠️ Match model exists but need dedicated MatchConfirmation model
   - ⚠️ Need acceptance/decline tracking
   - ⚠️ Need timeout handling with penalties
   - ⚠️ Need return-to-queue logic for failed confirmations

3. **Queue Status Broadcasting**
   - ⚠️ Need real-time queue position updates
   - ⚠️ Need estimated wait time calculation
   - ⚠️ Need players-in-queue count broadcasting

4. **Frontend Integration**
   - ⚠️ WebSocketContext exists but may need queue-specific state
   - ⚠️ UI components need full integration with backend events
   - ⚠️ Match acceptance modal needs implementation

### ❌ NOT IMPLEMENTED

1. **Lobby Chat System**
   - ❌ No ChatMessage model
   - ❌ No lobby-specific chat handlers
   - ❌ No message persistence or history

2. **Queue Penalties System**
   - ❌ No penalty tracking for declined matches
   - ❌ No temporary queue bans
   - ❌ No karma adjustment for queue dodging

3. **Advanced Queue Features**
   - ❌ Priority queue for high-karma players
   - ❌ Placement match special handling
   - ❌ Dynamic queue size balancing
   - ❌ Queue analytics and metrics

4. **Voice Integration**
   - ❌ No voice channel management
   - ❌ No voice state tracking
   - ❌ No team voice assignment

---

## Implementation Priority

### 🔥 HIGH PRIORITY (Core PUG Functionality)
1. Create MatchConfirmation model with acceptance tracking
2. Implement match acceptance/decline handlers
3. Add queue status broadcasting to frontend
4. Integrate frontend play.jsx with existing backend events
5. Add timeout handling for match acceptance

### 🔶 MEDIUM PRIORITY (Enhanced Experience)
1. Add lobby chat functionality
2. Implement queue penalty system
3. Add estimated wait time calculation
4. Add queue position tracking
5. Enhance Lobby model with last_activity tracking

### 🔷 LOW PRIORITY (Nice-to-Have)
1. Voice channel integration
2. Advanced queue analytics
3. Priority queue for high-karma players
4. Placement match special handling

---

## Summary

**Overall Status**: ~70% Complete

The core infrastructure is **solidly implemented**: Player/Lobby models, WebSocket handlers, queue management, and a sophisticated matchmaking algorithm with MMR/TrueSkill integration. The matchmaking engine is production-ready with rank-aware tolerance and adaptive team balancing.

**What's Working**:
- Player and lobby management
- Redis-based queue with ELO-based sorting
- Advanced matchmaking algorithm (MatchmakerV2)
- WebSocket event routing
- Match execution pipeline

**What's Missing**:
- Match confirmation/acceptance system (critical gap)
- Frontend integration with existing backend
- Queue status real-time updates
- Penalty system for queue dodging
- Lobby chat functionality

**Next Immediate Steps**:
1. Create MatchConfirmation model and handlers
2. Wire frontend play.jsx to existing WebSocket events
3. Add queue status broadcasting
4. Test full flow: lobby → queue → match found → acceptance → veto
