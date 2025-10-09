# Scrim.GG Implementation Roadmap
## From Current State to FACEIT-like Experience

## 📋 Overview

This document provides a step-by-step plan to transform your current Scrim.GG platform into a fully-featured FACEIT-like competitive matchmaking service for Valorant.

---

## 🎯 Phase 1: WebSocket Communication Layer (Week 1-2)

### Priority: CRITICAL
**Goal:** Replace REST API with full WebSocket-based event system.

### Tasks:

#### 1.1 Frontend (React)
- [ ] Implement `WebSocketProvider` context (see `examples/1_websocket_client_hook.jsx`)
- [ ] Wrap App component with WebSocketProvider
- [ ] Create `useWebSocket()` hook for components
- [ ] Replace all `fetch()` calls to `/command` with WebSocket events
- [ ] Add reconnection logic with exponential backoff
- [ ] Add connection status indicator in UI

**Files to modify:**
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/App.js`
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/hooks/useWebSocket.js` (NEW)
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/pages/login.jsx`
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/components/lobby/lobby.jsx`
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/components/home/home.jsx`

#### 1.2 Local Backend (Quart)
- [ ] Replace `bootstrap.py` with improved version (see `examples/2_improved_quart_backend.py`)
- [ ] Implement event router system
- [ ] Remove `/command` REST endpoint
- [ ] Add proper event handlers for all operations
- [ ] Add WebSocket message validation
- [ ] Implement client state tracking

**Files to modify:**
- `Scrim.GG_Client/scrimgg/backend/bootstrap.py` → Use `bootstrap_improved.py`

#### 1.3 Testing
- [ ] Test authentication flow via WebSocket
- [ ] Test lobby creation via WebSocket
- [ ] Test chat messages via WebSocket
- [ ] Verify reconnection after disconnect
- [ ] Load test with multiple concurrent connections

---

## 🎮 Phase 2: Game State Monitor (Week 2-3)

### Priority: HIGH
**Goal:** Automatically detect Valorant game state changes and push to frontend.

### Tasks:

#### 2.1 Implement Game Monitor
- [ ] Create `game_monitor.py` (see `examples/3_game_monitor_service.py`)
- [ ] Integrate with `ValorantAPI` client
- [ ] Poll Valorant client every 2-5 seconds
- [ ] Detect state transitions:
  - MENUS → PREGAME (player joined custom game)
  - PREGAME → INGAME (match started)
  - INGAME → MENUS (match ended)
- [ ] Broadcast state changes to frontend via WebSocket

**Files to create:**
- `Scrim.GG_Client/scrimgg/backend/game_monitor.py` (NEW)

**Files to modify:**
- `Scrim.GG_Client/scrimgg/backend/bootstrap_improved.py` (start monitor after login)
- `Scrim.GG_Client/scrimgg/backend/clientapi.py` (add helper methods)

#### 2.2 Frontend Integration
- [ ] Display game state indicator in UI
- [ ] Show notification when match starts
- [ ] Show notification when match ends
- [ ] Auto-trigger result collection on match end

#### 2.3 Testing
- [ ] Verify state detection in actual Valorant client
- [ ] Test match start detection
- [ ] Test match end detection
- [ ] Verify state broadcasts reach frontend

---

## 🗺️ Phase 3: Veto System (Week 3-4)

### Priority: HIGH
**Goal:** Implement FACEIT-style map/server veto (ban/pick) system.

### Tasks:

#### 3.1 Backend Implementation
- [ ] Create `veto_system.py` (see `examples/4_veto_system.py`)
- [ ] Implement veto state management in Redis
- [ ] Add veto timeout handling (5 minutes)
- [ ] Support multiple veto formats (BO1, BO3, etc.)
- [ ] Implement auto-complete on timeout

**Files to create:**
- `ScrimGG/scrimgg/server/scrimgg/matchmaking/veto_system.py` (NEW)

#### 3.2 Django Consumer Integration
- [ ] Add veto event handlers to consumer
- [ ] Broadcast veto state changes to all match players
- [ ] Enforce turn-based veto logic
- [ ] Transition to acceptance phase after veto complete

**Files to modify:**
- `ScrimGG/scrimgg/server/scrimgg/matchmaking/consumers.py` (add veto handlers)

#### 3.3 Frontend UI
- [ ] Create veto screen component
- [ ] Show available/banned maps and servers
- [ ] Display whose turn it is
- [ ] Show countdown timer
- [ ] Allow ban/pick actions
- [ ] Show veto history

**Files to create:**
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/components/VetoScreen.jsx` (NEW)

#### 3.4 Testing
- [ ] Test BO1 veto flow
- [ ] Test turn enforcement
- [ ] Test timeout auto-completion
- [ ] Test with multiple concurrent matches

---

## 🎯 Phase 4: Match Coordinator (Week 4-5)

### Priority: CRITICAL
**Goal:** Orchestrate entire match lifecycle with timeouts and verification.

### Tasks:

#### 4.1 Backend Implementation
- [ ] Create `match_coordinator.py` (see `examples/5_match_coordinator.py`)
- [ ] Implement all match states (CREATED, VETO, ACCEPTING, READY, etc.)
- [ ] Add timeout handlers:
  - Veto phase: 5 minutes
  - Acceptance phase: 30 seconds
  - Join phase: 2 minutes
- [ ] Implement player verification (all 10 must join)
- [ ] Add penalty system for dodgers/no-shows

**Files to create:**
- `ScrimGG/scrimgg/server/scrimgg/matchmaking/match_coordinator.py` (NEW)

#### 4.2 Database Models
- [ ] Create `MatchState` model
- [ ] Create `MatchPlayer` model (for individual performance)
- [ ] Create `PlayerPenalty` model
- [ ] Add migrations

**Files to modify:**
- `ScrimGG/scrimgg/server/scrimgg/scrimgg/models.py` (add new models)

#### 4.3 Consumer Integration
- [ ] Integrate coordinator with consumer events
- [ ] Handle match acceptance
- [ ] Handle pregame creation
- [ ] Handle player join verification
- [ ] Handle match results

**Files to modify:**
- `ScrimGG/scrimgg/server/scrimgg/matchmaking/consumers.py` (use `examples/6_enhanced_django_consumer.py`)

#### 4.4 Frontend Match Flow
- [ ] Create match acceptance modal (30 sec timer)
- [ ] Show "Creating custom game..." for constructor
- [ ] Show "Joining custom game..." for others
- [ ] Show player join progress (X/10 joined)
- [ ] Display "Match Live" when all joined

**Files to create:**
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/components/MatchAcceptanceModal.jsx` (NEW)
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/components/MatchLiveIndicator.jsx` (NEW)

#### 4.5 Testing
- [ ] Test full match flow (veto → accept → join → live)
- [ ] Test dodge cancellation
- [ ] Test no-show cancellation
- [ ] Test penalties applied correctly
- [ ] Test timeout handlers

---

## 📊 Phase 5: Match Results & ELO (Week 5-6)

### Priority: HIGH
**Goal:** Automatically collect match results and update player stats/ELO.

### Tasks:

#### 5.1 Result Collection
- [ ] Fetch match details from Valorant API after match ends
- [ ] Extract player stats (kills, deaths, assists, combat score, etc.)
- [ ] Send results to Django server
- [ ] Store in `MatchPlayer` model

**Files to modify:**
- `Scrim.GG_Client/scrimgg/backend/game_monitor.py` (add result fetching)
- `Scrim.GG_Client/scrimgg/backend/clientapi.py` (add API methods)

#### 5.2 ELO Calculation
- [ ] Implement ELO rating algorithm
- [ ] Calculate team average ELO
- [ ] Determine ELO changes based on:
  - Win/Loss
  - Team ELO difference
  - Individual performance (optional multiplier)
- [ ] Update player ELO in database

**Files to create:**
- `ScrimGG/scrimgg/server/scrimgg/matchmaking/elo_calculator.py` (NEW)

#### 5.3 Stats Aggregation
- [ ] Update player lifetime stats
- [ ] Update player PUG-specific stats
- [ ] Calculate ADR, RWS, K/D, etc.
- [ ] Track win/loss record

**Files to modify:**
- `ScrimGG/scrimgg/server/scrimgg/matchmaking/match_coordinator.py` (process results)

#### 5.4 Post-Match UI
- [ ] Create match summary screen
- [ ] Show final score
- [ ] Display player stats table
- [ ] Show ELO changes (+/- for each player)
- [ ] Highlight MVP

**Files to create:**
- `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/components/MatchSummary.jsx` (NEW)

#### 5.5 Testing
- [ ] Test result collection from real match
- [ ] Verify ELO calculations
- [ ] Verify stats updates
- [ ] Test with various match outcomes

---

## 👥 Phase 6: Social Features (Week 6-7)

### Priority: MEDIUM
**Goal:** Improve social experience with friends, profiles, and teams.

### Tasks:

#### 6.1 Friend System
- [ ] Add friend request UI
- [ ] Implement accept/decline flow
- [ ] Show online friends
- [ ] Allow inviting friends to lobby

#### 6.2 Player Profiles
- [ ] Create player profile page
- [ ] Show stats, ELO history, match history
- [ ] Display achievements/badges
- [ ] Show recent matches

#### 6.3 Team System
- [ ] Create team creation UI
- [ ] Implement roster management
- [ ] Allow team-based queue (future)

---

## 🔐 Phase 7: Anti-Cheat & Integrity (Week 7-8)

### Priority: MEDIUM
**Goal:** Add integrity checks and reporting system.

### Tasks:

#### 7.1 Client Verification
- [ ] Implement heartbeat system
- [ ] Verify client is running Valorant
- [ ] Detect client tampering

#### 7.2 Reporting System
- [ ] Add in-game report button
- [ ] Store reports in database
- [ ] Create admin review panel

#### 7.3 Demo/Replay Storage
- [ ] Store match IDs for replay retrieval
- [ ] Allow downloading demos

---

## 🚀 Phase 8: Polish & Optimization (Week 8-9)

### Priority: LOW
**Goal:** Optimize performance and improve UX.

### Tasks:

#### 8.1 Performance
- [ ] Optimize database queries
- [ ] Add database indexes
- [ ] Implement caching for frequently accessed data
- [ ] Load test with 100+ concurrent matches

#### 8.2 UX Improvements
- [ ] Add loading states everywhere
- [ ] Improve error messages
- [ ] Add sound notifications
- [ ] Polish animations and transitions

#### 8.3 Documentation
- [ ] Write user guide
- [ ] Document API/events
- [ ] Create troubleshooting guide

---

## 📝 Implementation Checklist by Component

### Frontend (React + Electron)
- [ ] WebSocket hook and provider
- [ ] Connection status indicator
- [ ] Lobby component (with WebSocket)
- [ ] Queue status display
- [ ] Veto screen
- [ ] Match acceptance modal
- [ ] Match live indicator
- [ ] Post-match summary
- [ ] Player profile page
- [ ] Friend management UI
- [ ] Settings page

### Local Client Backend (Quart)
- [ ] WebSocket event router
- [ ] Game state monitor service
- [ ] Valorant API wrapper improvements
- [ ] Result collection
- [ ] Auto-join custom game logic

### Server Backend (Django)
- [ ] Enhanced consumer with full match flow
- [ ] Veto system
- [ ] Match coordinator
- [ ] ELO calculator
- [ ] Matchmaking engine improvements
- [ ] Admin panel for moderation

### Database
- [ ] MatchState model
- [ ] MatchPlayer model
- [ ] PlayerPenalty model
- [ ] Match history indexes
- [ ] ELO history tracking

---

## 🛠️ Development Environment Setup

### Prerequisites
```bash
# Python 3.10+
# Node.js 16+
# Redis server
# PostgreSQL (optional, for production)
```

### Installation Steps

1. **Server Setup**
```bash
cd ScrimGG/scrimgg/server/scrimgg
pipenv install
pipenv shell
python manage.py migrate
python manage.py runserver
```

2. **Redis**
```bash
# Start Redis server
redis-server
```

3. **Celery Worker** (for background tasks)
```bash
cd ScrimGG/scrimgg/server/scrimgg
celery -A scrimgg worker -l info
```

4. **Client Backend**
```bash
cd Scrim.GG_Client/scrimgg/backend
pipenv install
pipenv shell
python bootstrap.py  # or bootstrap_improved.py
```

5. **Client Frontend**
```bash
cd Scrim.GG_Client/scrimgg/frontend/scrimgg
npm install
npm run start  # Runs React dev server + Electron
```

---

## 🧪 Testing Strategy

### Unit Tests
- [ ] Veto system logic
- [ ] ELO calculation
- [ ] Match state transitions
- [ ] Penalty system

### Integration Tests
- [ ] Full match flow (end-to-end)
- [ ] WebSocket communication
- [ ] Database operations

### Load Tests
- [ ] 100 concurrent users
- [ ] 50 concurrent matches
- [ ] WebSocket message throughput

---

## 📊 Success Metrics

- Match completion rate > 90%
- Average queue time < 2 minutes
- Dodge rate < 5%
- Client crash rate < 1%
- User retention > 30% (week 1 to week 4)

---

## 🚨 Critical Path Items

**These must be completed in order for the system to function:**

1. ✅ WebSocket communication (Phase 1)
2. ✅ Game state monitor (Phase 2)
3. ✅ Match coordinator (Phase 4)
4. ✅ Match results collection (Phase 5)
5. ✅ ELO calculation (Phase 5)

**Veto system (Phase 3) can be implemented in parallel with Phase 4.**

---

## 📚 Reference Implementation Files

All example code is provided in the `examples/` directory:

1. `1_websocket_client_hook.jsx` - React WebSocket integration
2. `2_improved_quart_backend.py` - Event-driven local backend
3. `3_game_monitor_service.py` - Valorant state monitoring
4. `4_veto_system.py` - Map/server veto logic
5. `5_match_coordinator.py` - Full match lifecycle management
6. `6_enhanced_django_consumer.py` - Complete Django consumer

---

## 🆘 Need Help?

Common issues and solutions:

### WebSocket connection fails
- Check Quart server is running on port 5888
- Verify CORS settings
- Check firewall rules

### Valorant client not detected
- Ensure Valorant is running
- Check lockfile exists
- Verify `valclient` library is working

### Match doesn't start
- Check all 10 players are connected
- Verify pregame_id is correct
- Check constructor created custom game

---

## 🎉 Next Steps After Completion

Once the core FACEIT-like experience is implemented:

1. **Leagues & Tournaments** - Organized competition
2. **Leaderboards** - Global, regional, and friend rankings
3. **Achievements & Rewards** - Gamification
4. **Mobile Companion App** - Queue from phone
5. **API for Third Parties** - Allow integrations
6. **Monetization** - Premium features, cosmetics, etc.

---

Good luck with your implementation! This is an ambitious but achievable project. Focus on the critical path items first, and iterate based on user feedback.

