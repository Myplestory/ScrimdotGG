# Frontend Architecture - Complete Summary

## Overview

This document provides a complete overview of the Scrim.GG frontend architecture, including all pages, entities, events, and implementation requirements.

---

## 📊 Implementation Status Overview

| Feature Category | Status | Backend | Frontend | Priority | Notes |
|-----------------|--------|---------|----------|----------|-------|
| **Core Infrastructure** | ✅ 90% | ✅ Complete | ⚠️ Partial | 🔥 Critical | WebSocket, Player model, handlers exist |
| **PUG Matchmaking** | ⚠️ 70% | ✅ Strong | ❌ Missing | 🔥 Critical | Queue, matchmaker, veto exist; need acceptance UI |
| **Match System** | ✅ 80% | ✅ Complete | ❌ Missing | 🔥 Critical | Veto, execution exist; need MatchPage UI |
| **Scrim System** | ⚠️ 30% | ⚠️ Partial | ❌ Missing | 🔶 High | Basic lobby exists; need invites, ready check |
| **Team Management** | ⚠️ 10% | ⚠️ Minimal | ❌ Missing | 🔶 High | Basic Team model; need expansion for leagues |
| **League System** | ❌ 5% | ❌ Missing | ❌ Missing | 🔷 Medium | No league app, need all models & scheduling |
| **Tournament System** | ❌ 3% | ❌ Missing | ❌ Missing | 🔷 Low | No tournament app, need bracket generation |
| **Forum System** | ❌ 0% | ❌ Missing | ❌ Missing | 🔷 Low | Entire forum app missing |
| **Support System** | ❌ 0% | ❌ Missing | ❌ Missing | 🔷 Low | Entire support app missing |

### Status Legend
- ✅ **Complete**: Fully implemented and functional
- ⚠️ **Partial**: Basic structure exists, needs enhancement
- ❌ **Missing**: Not implemented

### Priority Legend
- 🔥 **Critical**: Core functionality, must have for launch
- 🔶 **High**: Important features, early post-launch
- 🔷 **Medium**: Enhances experience, mid-term goal
- 🔹 **Low**: Nice-to-have, long-term consideration

### Key Findings

**✅ What's Working Well**:
- Player model is comprehensive (elo, mmr, trueskill, stats, friends)
- Match system has full veto infrastructure (server, map, side selection)
- Queue manager with Redis sorted sets and eligibility validation
- Matchmaker v2 with MMR-based matching and rank-aware tolerance
- WebSocket handlers for lobby, match, veto, execution
- Match execution with constructor assignment and join tracking

**⚠️ What Needs Work**:
- Match confirmation/acceptance system (critical gap for PUG flow)
- Frontend integration (pages exist but not wired to backend)
- Lobby model scrim fields (team captains, ready check)
- Team model expansion (owner, captain, logo for leagues)
- Profile model (bio, social links for player pages)
- ELO calculation on match completion

**❌ What's Missing**:
- League Django app (entire subsystem)
- Tournament Django app (entire subsystem)
- Forum Django app (entire subsystem)
- Support Django app (entire subsystem)
- ScrimInvite model
- MatchConfirmation model
- Queue status real-time broadcasting

### Development Timeline Estimate

**Phase 1: Complete PUG Matchmaking** (2-3 weeks) - 🔥 CRITICAL
- Add MatchConfirmation model
- Wire frontend to existing backend handlers
- Implement ELO calculation
- Add match completion detection
- **Goal**: Fully functional PUG queue → match → veto → play → completion

**Phase 2: Scrim System** (4-6 weeks) - 🔶 HIGH
- Expand Lobby model with scrim fields
- Create ScrimInvite model and handlers
- Implement ready check system
- Build frontend scrim UI

**Phase 3: League System** (8-12 weeks) - 🔶 HIGH
- Create League Django app with all models
- Expand Team model for league play
- Build scheduling and standings systems
- Implement team management (invites, roster locks)

**Phase 4: Tournament System** (10-16 weeks) - 🔷 MEDIUM
- Create Tournaments Django app
- Implement bracket generation algorithms
- Build tournament lifecycle management

**Phase 5: Community Features** (6-10 weeks) - 🔷 LOW
- Forum system
- Support ticketing
- Enhanced profiles

**Total Estimated Time to Feature-Complete**: 30-47 weeks (~7-11 months)

---

## Architecture Stack

### Frontend
- **Framework**: React (with Electron for desktop client)
- **State Management**: Context API (WebSocketContext)
- **Routing**: React Router
- **UI Library**: Material-UI (MUI)
- **Real-time**: WebSocket connections

### Backend (Quart)
- **Framework**: Quart (async Python)
- **Purpose**: Local client backend bridge
- **Port**: 5888
- **Role**: Forwards WebSocket events between Electron frontend and Django server

### Server (Django)
- **Framework**: Django + Django Channels
- **Architecture**: Event-driven microservices
- **Entry Point**: `realtime/consumers.py` (RealtimeConsumer)
- **Routing**: Events routed to specialized handlers
- **Business Logic**: Domain-specific managers per app
- **Pub/Sub**: Redis channels for real-time broadcasting

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  Components → WebSocketContext → ws://localhost:5888            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    QUART BACKEND (clientapi.py)                  │
│  WebSocket Handler → HTTP/WS Bridge → Django Server             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 DJANGO SERVER (realtime/consumers.py)            │
│  RealtimeConsumer → Route to Handler → Delegate to Manager      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               BUSINESS LOGIC (Django Apps/Managers)              │
│  LobbyManager, MatchManager, LeagueManager, etc.                 │
│  Database Operations + Redis Pub/Sub                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BROADCAST (Redis Channels)                    │
│  channel_layer.group_send() → All Connected Clients              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Complete Entity Model

### Core Entities

#### Player
```python
# Location: scrimgg/models.py
- puuid (PK)
- username, alias
- elo (display rank)
- mmr (hidden matchmaking rating)
- trueskill_mu, trueskill_sigma
- rank, region
- games_played, wins, losses
- Various stats (frags, deaths, assists, adr, rws, etc.)
- friends (M2M)
- team associations
```

#### Lobby
```python
# Location: scrimgg/models.py
- id (UUID)
- players (M2M → Player)
- lobby_leader (FK → Player)
- is_active, in_queue
- queue_type ('pug', 'scrim', 'custom')
- map_preferences, server_preferences
- average_elo, elo_range
- size, max_size
- Scrim additions:
  - team_a_captain, team_b_captain
  - team_a_ready, team_b_ready
  - scrim_format (JSON)
  - ready_check_active
```

#### Match
```python
# Location: match_system/models.py (primary)
# Also: scrimgg/models.py (legacy, being refactored)
- id (UUID)
- state (CONFIRMED, SERVER_VETO, MAP_VETO, SIDE_SELECTION, etc.)
- team_a_players, team_b_players (JSON)
- team_a_captain_puuid, team_b_captain_puuid
- server_pool, vetoed_servers, final_server
- map_pool, vetoed_maps, final_map
- veto_history (JSON)
- selected_side, side_selector
- team_a_score, team_b_score
- pregame_id, coregame_id
- Match statistics
```

### League Entities (NEW - Need Implementation)

#### League
```python
# Location: league/models.py (to create)
- id (UUID)
- name, season, division
- region, max_teams
- status (registration, active, playoffs, completed)
- registration dates, season dates
- entry_fee, prize_pool
- format (round_robin, swiss, double_elim)
- rules, map_pool
```

#### Team
```python
# Location: scrimgg/models.py (expand existing)
- id (UUID)
- name, tag, logo
- owner (FK → Player)
- captain (FK → Player)
- players (M2M → Player through TeamMember)
- active_roster (5 starters)
- substitute_roster (up to 2)
- division, verified
- wins, losses, stats
```

#### TeamMember (NEW)
```python
# Location: league/models.py
- team (FK → Team)
- player (FK → Player)
- role (IGL, Entry, AWP, Lurk, Support, Substitute)
- status (active, inactive, suspended)
- joined_at, left_at
- stats_with_team
```

#### LeagueRegistration (NEW)
```python
# Location: league/models.py
- league (FK → League)
- team (FK → Team)
- status (pending, confirmed, waitlist, rejected)
- payment_status
- roster_snapshot (locked at registration)
- registered_at, confirmed_at
```

#### LeagueMatch (NEW)
```python
# Location: league/models.py
- league (FK → League)
- week, match_number
- team_a, team_b (FK → Team)
- scheduled_time
- status (scheduled, live, completed, forfeit)
- scores, winner
- maps_played, vod_url
```

#### LeagueStanding (NEW)
```python
# Location: league/models.py
- league (FK → League)
- team (FK → Team)
- rank, wins, losses, ties
- rounds_won, rounds_lost
- round_differential, points
- streak, last_updated
```

### Tournament Entities (NEW - Need Implementation)

#### Tournament
```python
# Location: tournaments/models.py (to create)
- id (UUID)
- name, organizer, description
- format (single_elim, double_elim, swiss, round_robin)
- team_size, max_teams
- status (upcoming, registration, running, completed)
- registration dates, start_date
- check_in settings
- prize_pool, prize_distribution
- rules, map_pool, match_format
```

#### TournamentRegistration (NEW)
```python
# Location: tournaments/models.py
- tournament (FK → Tournament)
- team/player (FK)
- status (registered, checked_in, disqualified, withdrawn)
- seed, roster_snapshot
- checked_in_at
```

#### TournamentMatch (NEW)
```python
# Location: tournaments/models.py
- tournament (FK → Tournament)
- bracket (FK → TournamentBracket)
- round_number, match_number
- participant_a, participant_b
- winner, loser
- status, score
- next_match_winner, next_match_loser
```

### Forum Entities (NEW - Need Implementation)

#### ForumCategory, ForumThread, ForumReply
```python
# Location: forums/models.py (to create)
- Forum categories with threads and replies
- Like system
- Report system for moderation
```

### Support Entities (NEW - Need Implementation)

#### FAQ, SupportTicket, TicketMessage
```python
# Location: support/models.py (to create)
- FAQ knowledge base
- Ticket system with messaging
- Feedback system
```

### Profile Entity (NEW - Need Implementation)

#### Profile
```python
# Location: users/models.py or scrimgg/models.py
- player (OneToOne → Player)
- bio, social_links
- preferred_agents, preferred_roles
- team_history, achievements
- looking_for_team
```

---

## Event Categories

### Lobby Events
- `create_lobby` - Create new lobby
- `invite_to_lobby` - Invite player to lobby
- `join_lobby` - Join existing lobby
- `leave_lobby` - Leave lobby
- `kick_from_lobby` - Remove player
- `update_lobby_preferences` - Update map/server preferences
- `lobby_message` - Chat message

### Queue Events
- `add_lobby_to_queue` - Enter matchmaking
- `remove_lobby_from_queue` - Leave queue
- `get_queue_status` - Check queue state
- `check_queue_eligibility` - Validate can queue

### Match Confirmation Events
- `match_found` - Matchmaker found match
- `accept_match` - Accept match
- `decline_match` - Decline match
- `match_acceptance_update` - Real-time acceptance count
- `match_ready` - All accepted, transition to match

### Veto Events
- `veto_server` - Ban a server
- `veto_map` - Ban a map
- `select_side` - Choose attack/defense

### Match Execution Events
- `custom_game_created` - Constructor created game
- `player_joined_game` - Player joined custom game
- `match_started` - Game started
- `match_score_update` - Live score update
- `match_completed` - Match finished

### Scrim Events
- `create_scrim_lobby` - Create scrim lobby
- `send_scrim_invite` - Invite player/team to scrim
- `respond_to_scrim_invite` - Accept/decline invite
- `assign_scrim_captain` - Set team captain
- `scrim_ready_check` - Initiate ready check
- `player_ready` - Mark player as ready

### League Events
- `create_team` - Create competitive team
- `add_team_member` - Invite player to team
- `respond_to_team_invitation` - Accept/decline team invite
- `update_active_roster` - Set starters/subs
- `get_available_leagues` - Browse leagues
- `register_team_for_league` - Register for season
- `get_league_standings` - Fetch standings
- `get_league_schedule` - Fetch match schedule
- `request_match_reschedule` - Request time change

### Tournament Events
- `get_tournaments` - Browse tournaments
- `create_tournament` - Create new tournament
- `register_for_tournament` - Sign up
- `tournament_check_in` - Check in before start
- `withdraw_from_tournament` - Withdraw registration
- `generate_tournament_bracket` - Create bracket

### Forum Events
- `get_forum_categories` - Get forum structure
- `get_forum_threads` - Get threads in category
- `create_forum_thread` - Post new thread
- `post_forum_reply` - Reply to thread
- `toggle_forum_like` - Like/unlike content
- `report_forum_content` - Report abuse
- `search_forums` - Search posts

### Support Events
- `get_faqs` - Get help articles
- `search_faqs` - Search knowledge base
- `create_support_ticket` - Open support ticket
- `get_my_tickets` - List user's tickets
- `reply_to_ticket` - Reply to ticket
- `close_ticket` - Close resolved ticket
- `submit_ticket_feedback` - Rate support

### Profile Events
- `get_player_profile` - Load profile
- `update_profile` - Save profile changes
- `send_friend_request` - Add friend
- `accept_friend_request` - Accept friend
- `remove_friend` - Unfriend

---

## Required Django Apps

### Existing Apps
1. ✅ **`scrimgg`** - Core models (Player, Lobby, Match, Team)
2. ✅ **`realtime`** - WebSocket consumer and handlers
3. ✅ **`matchmaking`** - Queue management
4. ✅ **`match_system`** - Match lifecycle
5. ✅ **Execution phase (match_system/phases/execution.py)** - Live match tracking
6. ✅ **`users`** - Authentication (currently empty, needs expansion)
7. ✅ **`maps`** - Map data
8. ✅ **`riotlogin`** - Riot authentication

### New Apps Needed
1. ⚠️ **`lobby`** - Lobby management business logic
2. ⚠️ **`league`** - League system (teams, registrations, standings, schedule)
3. ⚠️ **`tournaments`** - Tournament system
4. ⚠️ **`forums`** - Community forums
5. ⚠️ **`support`** - Help and support tickets

### App Expansion Needed
1. ⚠️ **`users`** - Add Profile model and social features
2. ⚠️ **`scrimgg`** - Expand Team and Lobby models for leagues/scrims

---

## Implementation Roadmap

### Phase 1: Core Matchmaking (Foundation)
1. ✅ Basic Lobby model (exists)
2. ⚠️ Create `lobby` Django app
3. ⚠️ Implement LobbyManager
4. ⚠️ Implement queue system in `matchmaking`
5. ⚠️ Build matchmaking algorithm
6. ⚠️ Complete veto system in `match_system`
7. ⚠️ Implement match execution tracking

### Phase 2: Scrim System
1. ⚠️ Add scrim fields to Lobby model
2. ⚠️ Create ScrimInvite model
3. ⚠️ Implement ScrimManager
4. ⚠️ Build ready check system
5. ⚠️ Add team assignment logic
6. ⚠️ Build scrim UI components

### Phase 3: League System
1. ⚠️ Create `league` Django app
2. ⚠️ Implement League, Team, TeamMember models
3. ⚠️ Build team creation and roster management
4. ⚠️ Implement team invitation system
5. ⚠️ Add league registration and payment
6. ⚠️ Build standings calculation system
7. ⚠️ Create match scheduling system
8. ⚠️ Add match result recording
9. ⚠️ Build all league UI pages

### Phase 4: Tournament System
1. ⚠️ Create `tournaments` Django app
2. ⚠️ Implement Tournament models
3. ⚠️ Build tournament creation
4. ⚠️ Implement registration and check-in
5. ⚠️ Create bracket generator
6. ⚠️ Build bracket progression logic
7. ⚠️ Add tournament admin tools
8. ⚠️ Build all tournament UI pages

### Phase 5: Community Features
1. ⚠️ Create `forums` Django app
2. ⚠️ Implement forum models
3. ⚠️ Build thread/reply system
4. ⚠️ Add search functionality
5. ⚠️ Implement moderation tools
6. ⚠️ Create `support` Django app
7. ⚠️ Build FAQ system
8. ⚠️ Implement ticket system
9. ⚠️ Build UI for forums and support

### Phase 6: Profile & Social
1. ⚠️ Create Profile model
2. ⚠️ Expand Player model with social features
3. ⚠️ Implement friend system
4. ⚠️ Build profile pages
5. ⚠️ Add achievements system

---

## Frontend Page Status

| Page | Path | Status | Priority |
|------|------|--------|----------|
| Landing | `/landingpage` | ✅ Exists | P0 |
| Play (PUG Queue) | `/landingpage` (pug view) | ⚠️ Partial | P0 |
| Lobby | `/landingpage` (lobby view) | ⚠️ Partial | P0 |
| Match Page | `/match/:matchId` | ⚠️ Partial | P0 |
| Scrim | `/scrim` | ❌ Not implemented | P1 |
| League Create Team | `/leaguecreateteam` | ⚠️ UI only | P1 |
| League Register | `/leagueregteam` | ⚠️ UI only | P1 |
| League Standings | `/leaguestandings` | ⚠️ UI only | P1 |
| League Schedule | `/leagueschedule` | ⚠️ UI only | P1 |
| League Rules | `/leaguerules` | ⚠️ UI only | P2 |
| Forum Index | `/forumindex` | ❌ Not implemented | P2 |
| Post New | `/postnew` | ❌ Not implemented | P2 |
| Browse Tournaments | `/tournaments/browse` | ❌ Not implemented | P2 |
| My Tournaments | `/tournaments/my` | ❌ Not implemented | P2 |
| Create Tournament | `/tournaments/create` | ❌ Not implemented | P2 |
| Tournament History | `/tournaments/history` | ❌ Not implemented | P3 |
| FAQ | `/faq` | ❌ Not implemented | P2 |
| Support Tickets | `/supporttickets` | ❌ Not implemented | P2 |
| Download | `/download` | ✅ Exists | P3 |

**Legend:**
- ✅ Exists - Page is implemented with backend
- ⚠️ Partial - UI exists but needs backend
- ❌ Not implemented - Needs both UI and backend
- Priority: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)

---

## Key Architecture Patterns

### 1. Event Routing Pattern
```python
# Frontend emits
api.emit('event_name', payload)

# Backend routes
RealtimeConsumer.receive() 
  → _get_handler_for_action()
  → Handler.handle_event()
  → Manager.method()
  → Database + Broadcast
```

### 2. State Broadcasting Pattern
```python
# Backend broadcasts to group
await self.channel_layer.group_send(
    f"lobby_{lobby_id}",
    {'type': 'lobby_update', 'lobby': data}
)

# Frontend receives
on('lobby_update', (data) => setLobbyData(data))
```

### 3. WebSocket Group Management
```python
# Join group
await self.channel_layer.group_add(group_name, self.channel_name)

# Leave group
await self.channel_layer.group_discard(group_name, self.channel_name)

# Groups used:
- player_{puuid} - Personal notifications
- lobby_{lobby_id} - Lobby updates
- match_{match_id} - Match updates
- forum_thread_{thread_id} - Forum updates
- support_ticket_{ticket_id} - Ticket updates
```

---

## Performance Considerations

### Redis Caching Strategy
1. **Queue State** - Store queue entries in Redis Sorted Sets
2. **Lobby Preferences** - Cache in Redis Hash with TTL
3. **Match State** - Cache live match data for quick access
4. **Player Status** - Track active matches in Redis
5. **Hot Data** - Cache frequently accessed data (standings, etc.)

### Database Optimization
1. **Indexes** - Add indexes on frequently queried fields
2. **Select Related** - Use `select_related()` for foreign keys
3. **Prefetch Related** - Use `prefetch_related()` for many-to-many
4. **Batch Operations** - Bulk create/update when possible
5. **Read Replicas** - Consider read replicas for heavy queries

### WebSocket Optimization
1. **Selective Broadcasting** - Only send to relevant groups
2. **Message Throttling** - Rate limit frequent updates
3. **Lazy Loading** - Load data on demand, not on connect
4. **Connection Pooling** - Reuse database connections
5. **Heartbeat** - Implement ping/pong for connection health

---

## Security Considerations

1. **Authentication** - Validate PUUID on all events
2. **Authorization** - Check permissions (captain, admin, etc.)
3. **Rate Limiting** - Prevent spam and abuse
4. **Input Validation** - Sanitize all user inputs
5. **SQL Injection** - Use Django ORM (prevents by default)
6. **XSS** - Escape user-generated content
7. **CSRF** - WebSocket doesn't need CSRF but HTTP endpoints do

---

## Testing Strategy

### Unit Tests
- Test managers in isolation
- Test model methods
- Test utility functions

### Integration Tests
- Test full event flows
- Test WebSocket handlers
- Test database operations

### E2E Tests
- Test complete user journeys
- Test multi-player scenarios
- Test error handling

### Load Tests
- Test concurrent users
- Test matchmaking under load
- Test WebSocket scalability

---

## Documentation Structure

```
docs/architecture/frontend/
├── README.md (this file)
├── matchmake/
│   ├── README.md
│   ├── PLAY_PAGE.md
│   └── SCRIM_PAGE.md
├── league/
│   └── README.md (all league pages)
├── tournaments/
│   └── README.md (all tournament pages)
├── forums/
│   └── README.md (all forum pages)
├── support/
│   └── README.md (all support pages)
└── core/
    └── README.md (landing, match page, profile)
```

Each document contains:
- Page purpose and UI components
- Entity relationships
- Complete event flow with payloads
- Backend architecture
- Component hierarchy
- Database queries
- Redis data structures
- Implementation priority

---

## Next Steps

1. Review architecture with your team
2. Prioritize implementation phases
3. Start with Phase 1 (Core Matchmaking)
4. Create Jira/GitHub issues for each task
5. Begin implementing LobbyManager
6. Build matchmaking algorithm
7. Test end-to-end PUG flow
8. Iterate and expand to other phases

---

For detailed information on any specific page, refer to its individual documentation file.
