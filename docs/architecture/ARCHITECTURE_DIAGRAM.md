# Scrim.GG Architecture Diagrams

Comprehensive visual diagrams showing the complete system architecture, user flows, and component interactions.

---

## 🏗️ Complete User Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SCRIM.GG USER INTERACTION FLOW                     │
└─────────────────────────────────────────────────────────────────────────────────┘

1. USER AUTHENTICATION & SETUP
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Opens    │───▶│  Client App     │───▶│  Valorant API   │
│   Application   │    │  (Electron)     │    │  Authentication │
│                 │    │  - React UI     │    │  - Riot Login   │
│                 │    │  - Material-UI  │    │  - Token Mgmt   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Riot Login     │
                       │  (Server Auth)  │
                       │  - Django Auth  │
                       │  - User Profile │
                       │  - ELO/MMR Init │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  WebSocket      │
                       │  Connection     │
                       │  - Heartbeat    │
                       │  - Event Router │
                       │  - State Sync   │
                       └─────────────────┘

2. LOBBY CREATION & MANAGEMENT
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Create Lobby  │───▶│  Set Preferences│───▶│  Invite Friends │
│  - Leader Role  │    │  - Map Selection│    │  - Friend List  │
│  - Party Size   │    │  - Region Pref  │    │  - Invite Links │
│  - Privacy      │    │  - Skill Range  │    │  - Notifications│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Lobby Ready    │
                       │  (All Players)  │
                       │  - Player Slots │
                       │  - Ready Status │
                       │  - Chat System  │
                       └─────────────────┘

3. QUEUE SYSTEM
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Join Queue    │───▶│  Redis Queue    │───▶│  Matchmaking    │
│   (Leader)      │    │  (Sorted by     │    │  Algorithm      │
│  - Queue Entry  │    │   ELO/MMR)      │    │  (Every 10s)    │
│  - Wait Time    │    │  - Sorted Set   │    │  - ELO Matching │
│  - Position     │    │  - TTL Mgmt     │    │  - Team Balance │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Find 10        │
                       │  Compatible     │
                       │  Players        │
                       │  - MMR Ranges   │
                       │  - Map Prefs    │
                       │  - Time Tolerance│
                       └─────────────────┘

4. MATCH FOUND & CONFIRMATION
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Match Found    │───▶│  30s Countdown  │───▶│  Accept/Decline │
│  Notification   │    │  Timer          │    │  (All Players)  │
│  - Team Balance │    │  - UI Countdown │    │  - Accept Count │
│  - Map Info     │    │  - Auto-decline │    │  - Decline Logic│
│  - Player List  │    │  - Notifications│    │  - Requeue Logic│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  All Accept?    │
                       │  ┌─────────────┐│
                       │  │ YES: Match  ││
                       │  │ NO: Cancel  ││
                       │  └─────────────┘│
                       └─────────────────┘

5. MATCH EXECUTION (If All Accept)
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Match Starting │───▶│  Veto Phase     │───▶│  Side Selection │
│  Notification   │    │  (7 Maps → 1)   │    │  (Attack/Defend)│
│  - Match ID     │    │  - Captain Veto │    │  - Coin Toss    │
│  - Team Assign  │    │  - Timer (30s)  │    │  - Side Choice  │
│  - Veto Order   │    │  - Map Pool     │    │  - Team Colors  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Custom Game    │
                       │  Creation       │
                       │  - Game Code    │
                       │  - Server Info  │
                       │  - Join Links   │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Players Join   │
                       │  Custom Game    │
                       │  - Auto-join    │
                       │  - Verification │
                       │  - Ready Check  │
                       └─────────────────┘

6. LIVE MATCH MONITORING
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Game Start     │───▶│  Live Updates   │───▶│  Score Tracking │
│  Detection      │    │  (WebSocket)    │    │  (Real-time)    │
│  - Valorant API │    │  - Score Updates│    │  - Round Scores │
│  - Game State   │    │  - Player Stats │    │  - Match Status │
│  - Auto-detect  │    │  - Event Stream │    │  - Win Detection│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Match End      │
                       │  Detection      │
                       │  - Final Score  │
                       │  - MVP Stats    │
                       │  - Result Calc  │
                       └─────────────────┘

7. POST-MATCH PROCESSING
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Result         │───▶│  ELO/MMR        │───▶│  Statistics     │
│  Collection     │    │  Updates        │    │  Update         │
│  - Match Data   │    │  - TrueSkill    │    │  - Player Stats │
│  - Performance  │    │  - ELO Calc     │    │  - Match History│
│  - Validation   │    │  - Rank Update  │    │  - Leaderboards │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Return to      │
                       │  Lobby/Queue    │
                       │  - Auto-return  │
                       │  - New Lobby    │
                       │  - Queue Again  │
                       └─────────────────┘
```

---

## 🖥️ Client Architecture (Electron + React + Quart)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT ARCHITECTURE                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Electron      │    │   React App     │    │   Quart         │
│   Main Process  │    │   (Renderer)    │    │   Backend       │
│                 │    │                 │    │                 │
│  - App Lifecycle│    │  - UI Components│    │  - ASGI Server  │
│  - Window Mgmt  │    │  - State Mgmt   │    │  - WebSocket    │
│  - IPC Bridge   │    │  - Material-UI  │    │  - Valorant API │
│  - Auto-updater │    │  - Routing      │    │  - Game Monitor │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IPC Channel   │    │   WebSocket     │    │   Connection    │
│   Communication │    │   Context       │    │   Manager       │
│  - Event Bridge │    │  - Provider     │    │  - Dual Proxy   │
│  - Data Sync    │    │  - Event Hooks  │    │  - Heartbeat    │
│  - State Share  │    │  - Reconnection │    │  - State Mgmt   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                       ┌─────────────────┐
                       │   Django        │
                       │   Server        │
                       │  - WebSocket    │
                       │  - Matchmaking  │
                       │  - Game Logic   │
                       └─────────────────┘

DETAILED COMPONENT BREAKDOWN:

Electron Main Process:
├── App Lifecycle Management
│   ├── Application startup/shutdown
│   ├── Window creation and management
│   ├── Auto-updater integration
│   └── System tray functionality
├── IPC Bridge
│   ├── Communication with renderer process
│   ├── File system access
│   ├── System notifications
│   └── Security context management
└── Native Integration
    ├── Valorant client detection
    ├── System resource monitoring
    └── Hardware acceleration

React Renderer Process:
├── UI Components
│   ├── Material-UI component library
│   ├── Custom Scrim.GG components
│   ├── Responsive design system
│   └── Theme management
├── State Management
│   ├── React Context for global state
│   ├── Local component state
│   ├── WebSocket state synchronization
│   └── Persistent storage (localStorage)
├── Routing & Navigation
│   ├── React Router for SPA navigation
│   ├── Protected routes (authentication)
│   ├── Deep linking support
│   └── History management
└── Real-time Updates
    ├── WebSocket event handling
    ├── Live match updates
    ├── Queue position updates
    └── Chat system integration

Quart Backend:
├── ASGI Server
│   ├── Async request handling
│   ├── WebSocket connection management
│   ├── HTTP/WebSocket protocol support
│   └── Performance optimization
├── Valorant Integration
│   ├── Local API client (valclient)
│   ├── Game state monitoring
│   ├── Match detection and tracking
│   └── Player data extraction
├── Connection Management
│   ├── Dual proxy architecture
│   ├── Heartbeat system
│   ├── Reconnection logic
│   └── State synchronization
└── Game Monitoring
    ├── Real-time game state detection
    ├── Match start/end detection
    ├── Score tracking and updates
    └── Performance metrics collection
```

---

## 🎮 PUG Flow Architecture (Client + Server + Celery)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PUG FLOW ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   Django        │    │   Celery        │
│   (Quart)       │    │   Server        │    │   Tasks         │
│                 │    │                 │    │                 │
│  - WebSocket    │    │  - WebSocket    │    │  - Matchmaking  │
│  - Game Monitor │    │  - Consumers    │    │  - Cleanup      │
│  - State Mgmt   │    │  - Match Logic  │    │  - Timeouts     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Queue   │    │   PostgreSQL    │    │   Redis Cache   │
│  - Lobby Queue  │    │  - User Data    │    │  - Match State  │
│  - Sorted Sets  │    │  - Match Data   │    │  - Session Mgmt │
│  - TTL Mgmt     │    │  - Statistics   │    │  - Temp Data    │
└─────────────────┘    └─────────────────┘    └─────────────────┘

DETAILED PUG FLOW BREAKDOWN:

1. QUEUE ENTRY PHASE
Client Side:
├── Lobby Creation
│   ├── Map preference selection (min 5 maps)
│   ├── Skill range configuration
│   ├── Party size validation (1-5 players)
│   └── Privacy settings
├── Queue Join Request
│   ├── WebSocket event: 'queue_join'
│   ├── Lobby data validation
│   ├── Player ELO/MMR verification
│   └── Queue position calculation
└── Queue Status Updates
    ├── Real-time position updates
    ├── Estimated wait time display
    ├── Queue statistics
    └── Player count monitoring

Server Side:
├── Queue Manager (Redis)
│   ├── Sorted set by ELO/MMR
│   ├── TTL management (30min timeout)
│   ├── Queue position tracking
│   └── Duplicate prevention
├── WebSocket Consumer
│   ├── Event validation and routing
│   ├── Player authentication
│   ├── Queue state management
│   └── Broadcast updates
└── Database Updates
    ├── Player queue status
    ├── Lobby state persistence
    ├── Queue statistics
    └── Match history tracking

2. MATCHMAKING PHASE
Celery Tasks (Background):
├── Matchmaking Algorithm (Every 10s)
│   ├── ELO/MMR range calculation
│   ├── Time tolerance expansion
│   ├── Team balancing algorithm
│   └── Map preference matching
├── Queue Processing
│   ├── Lobby compatibility check
│   ├── 10-player combination logic
│   ├── Snake draft team assignment
│   └── Match quality validation
└── Match Creation
    ├── Match confirmation setup
    ├── 30-second timer initialization
    ├── Player notification dispatch
    └── Match state persistence

Server Components:
├── Matchmaker Engine
│   ├── TrueSkill integration
│   ├── Adaptive weighting system
│   ├── Rank-aware tolerance
│   └── Priority bias calculation
├── Match Confirmation Manager
│   ├── 30-second acceptance window
│   ├── Per-lobby acceptance tracking
│   ├── Auto-cancel on timeout
│   └── Requeue logic
└── WebSocket Broadcasting
    ├── Match found notifications
    ├── Acceptance status updates
    ├── Timer countdown events
    └── Match state changes

3. MATCH EXECUTION PHASE
Client Side:
├── Match Acceptance
│   ├── 30-second countdown UI
│   ├── Accept/Decline buttons
│   ├── Acceptance status display
│   └── Auto-decline on timeout
├── Veto Phase
│   ├── Interactive map selection
│   ├── Captain veto system
│   ├── Timer synchronization
│   └── Veto progress visualization
├── Side Selection
│   ├── Coin toss simulation
│   ├── Attack/Defend choice
│   ├── Team color assignment
│   └── Final match setup
└── Game Integration
    ├── Custom game creation
    ├── Auto-join functionality
    ├── Game state monitoring
    └── Live score tracking

Server Side:
├── Match System
│   ├── Veto action processing
│   ├── Side selection logic
│   ├── Custom game coordination
│   └── Match state management
├── Game Monitoring
│   ├── Valorant API integration
│   ├── Match start detection
│   ├── Score tracking
│   └── Match end detection
└── Real-time Updates
    ├── Live score broadcasting
    ├── Player statistics
    ├── Match progress updates
    └── Event stream management

4. POST-MATCH PHASE
Celery Tasks:
├── Result Processing
│   ├── Match data validation
│   ├── Score verification
│   ├── Performance metrics
│   └── Statistics calculation
├── ELO/MMR Updates
│   ├── TrueSkill rating updates
│   ├── Display ELO calculation
│   ├── Rank progression
│   └── Leaderboard updates
└── Cleanup Tasks
    ├── Temporary data removal
    ├── Cache invalidation
    ├── Session cleanup
    └── Resource optimization

Database Updates:
├── Player Statistics
│   ├── Match history
│   ├── Performance metrics
│   ├── ELO/MMR changes
│   └── Achievement tracking
├── Match Records
│   ├── Complete match data
│   ├── Player performances
│   ├── Veto history
│   └── Result validation
└── System Metrics
    ├── Queue performance
    ├── Match quality scores
    ├── System health data
    └── Usage statistics
```

---

## 🗂️ Server App Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SERVER APP ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core          │    │   Domain        │    │   Match System  │
│   (Shared)      │    │   (Business)    │    │   (Lifecycle)   │
│                 │    │                 │    │                 │
│  - Redis Mgmt   │    │  - Matchmaking  │    │  - Match Models │
│  - WebSocket    │    │  - Lobby Mgmt   │    │  - Confirmation │
│  - Exceptions   │    │  - Queue Logic  │    │  - Veto System  │
│  - Utilities    │    │  - User Mgmt    │    │  - Execution    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Realtime      │    │   Match         │    │   Users         │
│   (WebSocket)   │    │   Execution     │    │   (Auth)        │
│                 │    │                 │    │                 │
│  - Consumers    │    │  - Game Monitor │    │  - Riot Login   │
│  - Event Handlers│   │  - Score Track  │    │  - Profiles     │
│  - Broadcasting │    │  - Live Updates │    │  - Statistics   │
│  - State Sync   │    │  - Result Proc  │    │  - ELO/MMR      │
└─────────────────┘    └─────────────────┘    └─────────────────┘

DEPENDENCY FLOW:
Core → Domain → Match System → Match Execution → Realtime
  ↓       ↓         ↓              ↓              ↓
Users ← Lobby ← Matchmaking ← Veto System ← WebSocket Events
```

---

## 📡 WebSocket Event Flow

### Client → Server Events
```
lobby_create → lobby_join → queue_join → match_accept → 
match_decline → veto_action → game_join → match_complete
```

### Server → Client Events
```
lobby_created → queue_joined → match_found → match_confirmed → 
match_starting → veto_phase → side_selection → game_ready → 
match_in_progress → match_completed → elo_updated
```

---

## 🔒 Backward Compatibility
- External WebSocket API and message shapes preserved
- All existing client integrations continue to work
- Gradual migration path for new features

---

## 📦 Database Schema (High-Level)
- **Players**: User profiles, ELO/MMR, statistics
- **Lobbies**: Party management, preferences, queue status
- **Matches**: Match data, veto history, results
- **Veto Actions**: Map selection history, timing data

Full schema details in `docs/Server/` (models/migrations/specs)

---

## 🎯 System Summary
- **Clear Separation**: Modular architecture with defined boundaries
- **Backward Compatibility**: Existing integrations preserved
- **Scalability**: Redis-based queue system, Celery background tasks
- **Testability**: Isolated components, comprehensive test coverage
- **Maintainability**: Clean code structure, extensive documentation

---

**References:**
- `architecture/ARCHITECTURE_COMPARISON.md` (before/after)
- `architecture/ASYNC_SYNC_ARCHITECTURE.md` (runtime split)
- `docs/Server/*`, `docs/Client/*` (code-level details)
- `architecture/matchmaking/` (matchmaking system details)

