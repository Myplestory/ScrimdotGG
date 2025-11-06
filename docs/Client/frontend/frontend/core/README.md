# Core Pages Architecture

## Overview
Core pages that are essential to the application's functionality, including landing page, match page, and profile management.

---

## Page: Landing Page (`landing.jsx`)

### Purpose
Main dashboard that acts as a router between Home, Lobby, and PUG Queue views

### UI Components
The landing page is a container that switches between three main views:
- **Home** - Player dashboard and stats
- **Lobby** - Lobby management interface
- **PUG** - PUG queue interface (Play page)

### Architecture

```javascript
LandingPage.jsx (Container)
├── Receives activeComponent from route state
├── Renders one of:
│   ├── HomeComponent
│   ├── Lobby
│   └── Play (PUG Queue)
```

This page is essentially a routing component and delegates all functionality to its child components.

---

## Page: Match Page (`MatchPage.jsx`)

### Purpose
Live match interface showing real-time match state, veto phase, side selection, and match statistics

### UI Components
- Match header (team names, scores)
- Current phase indicator (veto, side selection, in progress, completed)
- Veto interface (server veto, map veto)
- Side selection interface
- Live scoreboard
- Round history
- Player statistics
- VOD/stream embed
- Match chat

### Entity Relationships

#### Primary Entities

```
Match (match_system/models.py)
├── id: UUID (PK)
├── state: string ('CONFIRMED', 'SERVER_VETO', 'MAP_VETO', 'SIDE_SELECTION', 'CREATING', 'READY', 'IN_PROGRESS', 'COMPLETED')
├── team_a_lobbies: JSONField
├── team_b_lobbies: JSONField
├── team_a_players: JSONField
├── team_b_players: JSONField
├── team_a_captain_puuid: string
├── team_b_captain_puuid: string
├── server_pool: JSONField
├── vetoed_servers: JSONField
├── final_server: string
├── map_pool: JSONField
├── vetoed_maps: JSONField
├── final_map: string
├── veto_history: JSONField
├── selected_side: string ('attack' | 'defense')
├── side_selector: string ('team_a' | 'team_b')
├── team_a_score: int
├── team_b_score: int
├── current_round: int
├── pregame_id: string
├── coregame_id: string
└── game_started_at: datetime

VetoAction (match_system/models.py)
├── match: ForeignKey → Match
├── team: string
├── action_type: string ('BAN_SERVER', 'BAN_MAP', 'PICK_MAP', 'PICK_SIDE')
├── target: string (server/map name or side)
├── timestamp: datetime
└── deadline: datetime

MatchStatistics (scrimgg/models.py)
├── match: ForeignKey → Match
├── player: ForeignKey → Player
├── team: string
├── kills: int
├── deaths: int
├── assists: int
├── damage_dealt: int
├── adr: float
├── rws: float
└── round_stats: JSONField
```

### Frontend State Management

```javascript
{
  matchData: {
    match_id: UUID,
    state: string,
    team_a: {
      lobbies: [...],
      players: [Player],
      captain: Player,
      score: int,
      ready: boolean
    },
    team_b: {...},
    current_phase: string,
    user_team: 'team_a' | 'team_b' | null,
    is_captain: boolean
  },
  
  vetoState: {
    phase: 'server' | 'map',
    server_pool: [string],
    map_pool: [string],
    vetoed_servers: [string],
    vetoed_maps: [string],
    veto_history: [VetoAction],
    current_turn: 'team_a' | 'team_b',
    deadline: timestamp,
    can_veto: boolean
  },
  
  sideSelectionState: {
    selector_team: 'team_a' | 'team_b',
    selected_side: 'attack' | 'defense' | null,
    deadline: timestamp,
    can_select: boolean
  },
  
  liveMatchState: {
    current_round: int,
    team_a_score: int,
    team_b_score: int,
    team_a_data: {
      players: [PlayerRoundData],
      economy: int,
      ultimates_ready: int
    },
    team_b_data: {...},
    round_history: [Round],
    last_updated: timestamp
  },
  
  statisticsState: {
    team_a_stats: [PlayerStats],
    team_b_stats: [PlayerStats],
    mvp: Player | null
  }
}
```

### Events & Data Flow

#### 1. Join Match Page

**Frontend → Backend**
```javascript
Event: 'get_match_data'
Payload: {
  match_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'match_data'
Payload: {
  match: {
    id: UUID,
    state: string,
    team_a: {...},
    team_b: {...},
    user_team: string | null,
    is_captain: boolean,
    veto_state: {...} | null,
    side_selection: {...} | null,
    live_data: {...} | null
  }
}
```

#### 2. Server Veto

**Frontend → Backend**
```javascript
Event: 'veto_server'
Payload: {
  match_id: UUID,
  server_name: string
}
```

**Backend Processing**
1. Validate it's user's team's turn
2. Validate user is captain
3. Add server to vetoed list
4. Create VetoAction record
5. Switch turn to other team
6. If only one server remains, set as final_server
7. If final_server set, transition to MAP_VETO state
8. Broadcast update

**Backend → Frontend (to all match participants)**
```javascript
Event: 'server_vetoed'
Payload: {
  match_id: UUID,
  vetoed_server: string,
  vetoed_by_team: string,
  remaining_servers: [string],
  next_turn: string,
  deadline: timestamp,
  final_server: string | null,
  transition_to_map_veto: boolean
}
```

#### 3. Map Veto

**Frontend → Backend**
```javascript
Event: 'veto_map'
Payload: {
  match_id: UUID,
  map_name: string
}
```

**Backend Processing**
Similar to server veto:
1. Validate turn and captain
2. Add to vetoed maps
3. Record action
4. Switch turn
5. If only one map remains, set as final_map
6. If final_map set, determine side selector and transition to SIDE_SELECTION
7. Broadcast

**Backend → Frontend**
```javascript
Event: 'map_vetoed'
Payload: {
  match_id: UUID,
  vetoed_map: string,
  vetoed_by_team: string,
  remaining_maps: [string],
  next_turn: string,
  deadline: timestamp,
  final_map: string | null,
  transition_to_side_selection: boolean,
  side_selector_team: string | null
}
```

#### 4. Side Selection

**Frontend → Backend**
```javascript
Event: 'select_side'
Payload: {
  match_id: UUID,
  side: 'attack' | 'defense'
}
```

**Backend Processing**
1. Validate user is captain of selector team
2. Set selected_side
3. Transition to CREATING state
4. Assign constructor (one of the captains)
5. Send instructions to constructor
6. Broadcast

**Backend → Frontend**
```javascript
Event: 'side_selected'
Payload: {
  match_id: UUID,
  selected_side: string,
  selector_team: string,
  match_ready: boolean,
  constructor_puuid: string,
  message: string
}
```

#### 5. Custom Game Created

**Frontend → Backend** (from constructor)
```javascript
Event: 'custom_game_created'
Payload: {
  match_id: UUID,
  pregame_id: string,
  game_pod: string
}
```

**Backend Processing**
1. Update match with pregame_id
2. Transition to READY state
3. Start join timeout timer
4. Send join instructions to all players
5. Broadcast

**Backend → Frontend (to all)**
```javascript
Event: 'match_ready_to_join'
Payload: {
  match_id: UUID,
  pregame_id: string,
  map: string,
  server: string,
  side_assignment: {
    team_a: 'attack' | 'defense',
    team_b: 'attack' | 'defense'
  },
  join_timeout: timestamp,
  message: 'Join the custom game now!'
}
```

#### 6. Player Joined Game

**Frontend → Backend**
```javascript
Event: 'player_joined_game'
Payload: {
  match_id: UUID
}
```

**Backend Processing**
1. Add player to joined_players list
2. Check if all players joined
3. If all joined, transition to IN_PROGRESS
4. Broadcast join status

**Backend → Frontend (real-time)**
```javascript
Event: 'player_join_update'
Payload: {
  match_id: UUID,
  joined_count: int,
  total_count: int,
  joined_players: [PUUID],
  all_joined: boolean
}
```

#### 7. Match Started

**Backend → Frontend** (when game starts)
```javascript
Event: 'match_started'
Payload: {
  match_id: UUID,
  coregame_id: string,
  started_at: timestamp
}
```

#### 8. Live Score Updates

**Backend → Frontend** (periodic updates during match)
```javascript
Event: 'match_score_update'
Payload: {
  match_id: UUID,
  current_round: int,
  team_a_score: int,
  team_b_score: int,
  team_a_data: {
    players: [
      {
        puuid: string,
        alias: string,
        agent: string,
        kills: int,
        deaths: int,
        assists: int,
        acs: int,
        alive: boolean
      }
    ]
  },
  team_b_data: {...},
  round_won_by: 'team_a' | 'team_b' | null,
  round_win_type: string // 'elimination', 'defuse', 'detonation', 'time'
}
```

#### 9. Match Completed

**Backend → Frontend**
```javascript
Event: 'match_completed'
Payload: {
  match_id: UUID,
  winner: 'team_a' | 'team_b',
  final_score: {
    team_a: int,
    team_b: int
  },
  mvp: {
    puuid: string,
    alias: string,
    stats: {...}
  },
  match_statistics: {
    team_a: [PlayerStats],
    team_b: [PlayerStats]
  },
  elo_changes: {
    [puuid]: {
      old_elo: int,
      new_elo: int,
      change: int
    }
  },
  completed_at: timestamp
}
```

### Component Hierarchy

```
MatchPage.jsx
├── MatchHeader
│   ├── TeamInfo (Team A)
│   │   ├── TeamName
│   │   ├── TeamScore
│   │   └── TeamPlayers
│   ├── PhaseIndicator
│   └── TeamInfo (Team B)
├── PhaseContent (conditional rendering based on state)
│   ├── VetoPhase (if SERVER_VETO or MAP_VETO)
│   │   ├── VetoHeader
│   │   │   ├── PhaseTitle ('Server Veto' | 'Map Veto')
│   │   │   ├── TurnIndicator
│   │   │   └── CountdownTimer
│   │   ├── AvailableOptions
│   │   │   └── VetoOptionCard
│   │   │       ├── OptionImage
│   │   │       ├── OptionName
│   │   │       └── VetoButton
│   │   └── VetoHistory
│   │       └── VetoActionRow
│   ├── SideSelectionPhase (if SIDE_SELECTION)
│   │   ├── SelectionHeader
│   │   ├── MapDisplay
│   │   ├── SideOptions
│   │   │   ├── AttackOption
│   │   │   └── DefenseOption
│   │   └── CountdownTimer
│   ├── WaitingPhase (if CREATING or READY)
│   │   ├── StatusMessage
│   │   ├── JoinInstructions
│   │   ├── JoinedPlayersList
│   │   └── JoinButton (if READY)
│   ├── LiveMatchPhase (if IN_PROGRESS)
│   │   ├── ScoreBoard
│   │   │   ├── RoundIndicator
│   │   │   ├── TeamAPlayers
│   │   │   │   └── PlayerRow
│   │   │   │       ├── AgentIcon
│   │   │   │       ├── PlayerName
│   │   │   │       ├── KDA
│   │   │   │       ├── ACS
│   │   │   │       └── AliveIndicator
│   │   │   └── TeamBPlayers
│   │   ├── RoundHistory
│   │   │   └── RoundResult
│   │   └── StreamEmbed (if available)
│   └── CompletedPhase (if COMPLETED)
│       ├── VictoryBanner
│       ├── FinalScoreDisplay
│       ├── MVPCard
│       ├── StatisticsTable
│       │   ├── TeamAStats
│       │   └── TeamBStats
│       ├── EloChanges
│       │   └── PlayerEloChange
│       └── MatchActions
│           ├── ViewVODButton
│           ├── DownloadDemoButton
│           └── ReturnToLobbyButton
└── MatchChat (sidebar)
    ├── MessageList
    └── MessageInput
```

### Backend Django Architecture

#### Apps Involved
1. **`match_system`** - Match lifecycle management
2. **`match_execution`** - Live match data collection
3. **`realtime`** - WebSocket events

#### Handlers

```
realtime/handlers/veto_handler.py
├── handle_veto_server()
├── handle_veto_map()
├── handle_select_side()
├── check_veto_deadline()
└── transition_to_next_phase()

realtime/handlers/execution_handler.py
├── handle_custom_game_created()
├── handle_player_joined()
├── handle_player_join_failed()
├── handle_match_started()
├── handle_score_update()
└── handle_match_completed()
```

#### Manager Methods

```python
# match_system/manager.py

class MatchManager:
    async def get_match_data(self, match_id, viewer_puuid)
    async def process_server_veto(self, match_id, captain_puuid, server)
    async def process_map_veto(self, match_id, captain_puuid, map_name)
    async def process_side_selection(self, match_id, captain_puuid, side)
    async def check_veto_timeouts(self) # Background task
    async def assign_random_veto(self, match_id, phase) # On timeout
    
# match_execution/manager.py

class ExecutionManager:
    async def record_pregame_id(self, match_id, pregame_id, constructor_puuid)
    async def record_player_join(self, match_id, player_puuid)
    async def start_match(self, match_id, coregame_id)
    async def update_live_scores(self, match_id, score_data)
    async def complete_match(self, match_id, final_data)
    async def calculate_elo_changes(self, match_id)
    async def distribute_rewards(self, match_id)
```

### Database Queries

```python
# Get match with all data
match = await sync_to_async(
    Match.objects.select_related().get
)(id=match_id)

# Get player's team in match
player_data = next(
    (p for p in match.team_a_players if p['puuid'] == puuid),
    next((p for p in match.team_b_players if p['puuid'] == puuid), None)
)

# Get match statistics
stats = await sync_to_async(
    MatchStatistics.objects.filter(match=match)
    .select_related('player')
    .order_by('-kills')
    .all
)()
```

### Redis Data Structures

```python
# Live match state cache (Redis Hash)
Key: f"match:{match_id}:live"
Fields:
  - current_round: int
  - team_a_score: int
  - team_b_score: int
  - last_updated: timestamp
  - team_a_players: JSON
  - team_b_players: JSON

# Veto deadline tracking (Redis Sorted Set)
Key: "match_veto_deadlines"
Score: deadline_timestamp
Value: f"{match_id}:{phase}" # for background cleanup
```

### Performance Considerations

1. **WebSocket Groups**: Subscribe all match participants to `match_{match_id}` group
2. **State Caching**: Cache match state in Redis during live gameplay
3. **Batch Updates**: Aggregate score updates every 5 seconds instead of every kill
4. **Lazy Loading**: Load match statistics only when requested (not during live gameplay)

---

## Page: Profile/Home Component

### Purpose
Player dashboard showing stats, recent matches, friends, achievements

### UI Components
- Player card (avatar, rank, elo, stats)
- Recent matches list
- Stats overview (win rate, KDA, ADR, RWS)
- Friends list
- Achievements/badges
- Match history graph
- Agent stats

### Entity Relationships

```
Profile (Django) - NEW ENTITY (from league docs)
├── player: OneToOne → Player
├── bio: text
├── social_links: JSONField
├── team_history: JSONField
├── achievements: JSONField
├── preferred_agents: JSONField
├── preferred_roles: JSONField
└── looking_for_team: boolean
```

### Events & Data Flow

#### 1. Get Player Profile

**Frontend → Backend**
```javascript
Event: 'get_player_profile'
Payload: {
  puuid: string // can view others' profiles
}
```

**Backend → Frontend**
```javascript
Event: 'player_profile'
Payload: {
  player: {
    puuid: string,
    alias: string,
    rank: string,
    elo: int,
    avatar: string,
    region: string,
    games_played: int,
    wins: int,
    losses: int,
    win_rate: float,
    kda: float,
    adr: float,
    rws: float,
    hs_percentage: float,
    highest_rank: string,
    account_level: int
  },
  profile: {
    bio: string,
    social_links: {...},
    preferred_agents: [string],
    preferred_roles: [string],
    looking_for_team: boolean
  },
  recent_matches: [Match],
  achievements: [Achievement],
  stats_by_agent: [...],
  friends_count: int,
  is_friend: boolean,
  is_self: boolean
}
```

#### 2. Update Profile

**Frontend → Backend**
```javascript
Event: 'update_profile'
Payload: {
  bio: string,
  social_links: {...},
  preferred_agents: [string],
  preferred_roles: [string],
  looking_for_team: boolean
}
```

---

## Implementation Status

### ✅ FULLY IMPLEMENTED

1. **Match Models** (`server/match_system/models.py`)
   - ✅ Match model with full state machine:
     - States: CONFIRMED → SERVER_VETO → MAP_VETO → SIDE_SELECTION → CREATING → READY → IN_PROGRESS → COMPLETED
     - Team tracking (team_a_players, team_b_players, team_a_captain_puuid, team_b_captain_puuid)
     - Veto tracking (server_pool, map_pool, veto_history, selected_server, selected_map, selected_side)
     - Score tracking (team_a_score, team_b_score, team_a_rounds_won, team_b_rounds_won)
     - Timing (created_at, started_at, completed_at)
   - ✅ MatchPlayer model - Connection tracking for each player
   - ✅ VetoAction model - Audit trail for all veto actions

2. **Veto System** (`server/realtime/handlers/veto_handler.py`, `server/match_system/managers.py`)
   - ✅ VetoHandler - WebSocket handler for veto events
   - ✅ MatchManager - Business logic for veto operations:
     - get_match_data() - Fetch current match state
     - veto_server() - Handle server veto with turn validation
     - veto_map() - Handle map veto with turn validation
     - select_side() - Handle side selection with turn validation
   - ✅ Veto turn validation (ensures correct captain's turn)
   - ✅ Veto history tracking (VetoAction records)
   - ✅ Automatic state progression (SERVER_VETO → MAP_VETO → SIDE_SELECTION → CREATING)

3. **Match Execution** (`server/match_execution/execution_manager.py`, `server/realtime/handlers/execution_handler.py`)
   - ✅ MatchExecutionManager:
     - assign_constructor() - Assign player to create custom game
     - handle_custom_game_created() - Track pregame_id when game is created
     - handle_player_joined() - Track player joins
     - check_all_players_joined() - Validate all 10 players joined
     - start_match() - Transition to IN_PROGRESS state
   - ✅ ExecutionHandler - WebSocket handler for execution events
   - ✅ Custom game creation tracking
   - ✅ Player join monitoring

4. **Player Model** (`server/scrimgg/models.py`)
   - ✅ Comprehensive player tracking:
     - Identity (puuid, username, alias, region)
     - Ratings (elo, mmr, trueskill_mu, trueskill_sigma, rank)
     - Stats (games_played, wins, losses, kills, deaths, assists, headshots, etc.)
     - Social (friends ManyToMany)
     - Placement (is_in_placement, placement_matches_played)
     - Behavior (karma, last_login)

### ⚠️ PARTIALLY IMPLEMENTED / NEEDS ENHANCEMENT

1. **Match Statistics** (`server/scrimgg/models.py`)
   - ✅ MatchStatistics model exists with basic fields
   - ⚠️ Need live score update system (currently manual)
   - ⚠️ Need round-by-round tracking
   - ⚠️ Need integration with Valorant API for real-time stats

2. **ELO Calculation**
   - ⚠️ Player model has elo/mmr fields
   - ⚠️ Need ELO calculation algorithm on match completion
   - ⚠️ Need MMR adjustment based on match performance
   - ⚠️ Need TrueSkill updates

3. **Match Chat**
   - ⚠️ No dedicated match chat system
   - ⚠️ Could reuse lobby chat infrastructure (if it exists)

4. **Side Selection**
   - ✅ MatchManager.select_side() exists
   - ⚠️ Need frontend UI for side selection
   - ⚠️ Need validation that side selection happens after map veto

### ❌ NOT IMPLEMENTED

1. **Profile Model** (`server/scrimgg/models.py` or `server/users/models.py`)
   - ❌ No dedicated Profile model for extended player info:
     - bio: text
     - country: string
     - social_links: JSONField (Twitter, Twitch, Discord)
     - favorite_agent: string
     - main_role: string
     - achievements: JSONField
     - profile_banner: ImageField
     - profile_picture: ImageField (currently uses Riot avatar)
   - ❌ Player model has stats but no bio/social features

2. **Live Score Updates** (`server/match_system/score_tracker.py` - DOES NOT EXIST)
   - ❌ No real-time score tracking from Valorant API
   - ❌ No round-by-round score updates
   - ❌ No live scoreboard broadcasting
   - ❌ No spike plant/defuse tracking
   - ❌ No economy tracking

3. **Match Completion System**
   - ❌ No automatic match completion detection
   - ❌ No match result validation
   - ❌ No post-match statistics aggregation
   - ❌ No match review/VOD linking

4. **ELO System** (`server/match_system/elo_calculator.py` - DOES NOT EXIST)
   - ❌ No ELO calculation algorithm
   - ❌ No K-factor configuration
   - ❌ No placement match handling
   - ❌ No rank promotion/demotion logic

5. **Profile Manager** (`server/users/profile_manager.py` - DOES NOT EXIST)
   - ❌ No profile management business logic:
     - update_profile()
     - update_social_links()
     - upload_profile_picture()
     - update_favorite_agent()

6. **Frontend Integration**
   - ❌ MatchPage.jsx not integrated with backend events
   - ❌ No veto UI implementation
   - ❌ No side selection UI
   - ❌ No live scoreboard
   - ❌ No player statistics display
   - ❌ Home page not integrated with profile data
   - ❌ Profile page not implemented

---

## Implementation Priority

### 🔥 HIGH PRIORITY (Core Match Functionality)
1. **Complete Frontend MatchPage** - Integrate with existing veto/execution handlers
2. **Build Veto UI** - Server veto, map veto, side selection interfaces
3. **Add Match Completion** - Detect when match ends and record results
4. **Implement ELO Calculator** - Calculate rating changes on match completion
5. **Add Live Score Broadcasting** - WebSocket events for score updates
6. **Build Basic Profile Page** - Display player stats and match history

### 🔶 MEDIUM PRIORITY (Enhanced Match Experience)
7. **Create Profile Model** - Extend Player with bio, social links, achievements
8. **Implement Profile Manager** - CRUD for profile data
9. **Add Round-by-Round Tracking** - Detailed round history for matches
10. **Build Match Statistics Display** - Scoreboard, KDA, economy on MatchPage
11. **Add Match Replay/VOD** - Link to VOD or match replay
12. **Implement Match Chat** - In-match communication

### 🔷 LOW PRIORITY (Polish & Features)
13. **Advanced Match Stats** - Heatmaps, agent picks, economy graphs
14. **Live Spectator Mode** - Watch ongoing matches
15. **Match Highlights** - Auto-generate highlight clips
16. **Achievement System** - Unlock achievements for milestones
17. **Profile Customization** - Banners, badges, profile themes
18. **Match Predictions** - Show win probability before veto
19. **Player Comparison** - Compare stats between players
20. **Rank History Graph** - Visualize ELO changes over time

---

## Summary

**Overall Status**: ~60% Complete

The **core match system is well-implemented**: Match models with full veto infrastructure, veto handlers with turn validation, match execution with join tracking, and comprehensive player stats tracking. The backend foundation for MatchPage is **production-ready**.

**What's Working**:
- Match model with state machine and veto tracking ✅
- Veto system (server/map/side) with turn validation ✅
- VetoAction audit trail ✅
- Match execution with constructor assignment ✅
- Player join tracking ✅
- MatchPlayer and MatchStatistics models ✅
- Comprehensive Player model with stats ✅

**Critical Gaps**:
- No frontend integration (MatchPage not wired to backend)
- No Profile model for bio/social links
- No ELO calculation on match completion
- No live score updates from Valorant API
- No match completion detection

**Dependencies**:
- Frontend MatchPage needs to connect to existing WebSocket handlers
- ELO calculator depends on match completion system
- Live scores depend on Valorant API integration
- Profile system is independent and can be built anytime

**Next Immediate Steps**:
1. Wire MatchPage.jsx to existing veto/execution handlers
2. Build veto UI (server picker, map picker, side picker)
3. Implement match completion detection
4. Build ELO calculator and apply on match end
5. Create Profile model and basic profile page

**Recommendation**: Match system is **ready for integration**. The backend is solid - focus on frontend work to connect UI to existing handlers. ELO calculation and match completion are critical for closing the loop on the match lifecycle. Profile system is lower priority but nice-to-have for user engagement.
