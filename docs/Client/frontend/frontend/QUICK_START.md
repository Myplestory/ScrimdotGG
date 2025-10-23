# Quick Start Guide - Frontend Architecture

## 🚀 Start Here

If you're new to the Scrim.GG architecture, read the documents in this order:

1. **[COMPLETE_ARCHITECTURE_SUMMARY.md](./COMPLETE_ARCHITECTURE_SUMMARY.md)** (15 min read)
   - Complete system overview
   - All entities and events
   - Implementation roadmap
   - Page status and priorities

2. **[ENTITY_RELATIONSHIPS.md](./ENTITY_RELATIONSHIPS.md)** (5 min read)
   - Entity relationship diagram
   - Database query examples
   - Performance optimization tips

3. **Pick a specific page based on your work:**
   - Working on matchmaking? → [matchmake/PLAY_PAGE.md](./matchmake/PLAY_PAGE.md)
   - Working on leagues? → [league/README.md](./league/README.md)
   - Working on tournaments? → [tournaments/README.md](./tournaments/README.md)
   - Working on match page? → [core/README.md](./core/README.md)

---

## 📊 System at a Glance

### Technology Stack
```
Frontend: React + Electron + Material-UI
   ↓ WebSocket
Backend: Quart (Python async) on port 5888
   ↓ HTTP/WebSocket
Server: Django + Django Channels + Redis
   ↓ PostgreSQL
Database: Player, Lobby, Match, Team, League, Tournament, etc.
```

### Event Flow Example
```javascript
// 1. Frontend emits event
api.emit('create_lobby', { queue_type: 'pug' })

// 2. Backend routes to handler
RealtimeConsumer → LobbyHandler → LobbyManager.create_lobby()

// 3. Database operation
lobby = Lobby.objects.create(...)

// 4. Broadcast to group
channel_layer.group_send('player_{puuid}', {...})

// 5. Frontend receives update
on('lobby_created', (data) => setLobbyData(data))
```

---

## 🎯 Priority Roadmap

### P0 - Critical (Must Have)
- ✅ Basic models exist
- ⚠️ **Create LobbyManager** (matchmaking/lobby management)
- ⚠️ **Implement queue system** (matchmaking algorithm)
- ⚠️ **Complete veto system** (server/map veto)
- ⚠️ **Match execution tracking** (live scores)

### P1 - High Priority
- ⚠️ **Scrim system** (custom matches with invites)
- ⚠️ **League system** (teams, registrations, standings)
- ⚠️ **Profile system** (player bios, social links)

### P2 - Medium Priority
- ⚠️ **Tournament system** (brackets, check-ins)
- ⚠️ **Forum system** (community discussions)
- ⚠️ **Support system** (tickets, FAQ)

### P3 - Nice to Have
- ⚠️ **Achievements** (badges, milestones)
- ⚠️ **Advanced stats** (agent-specific, map-specific)
- ⚠️ **Social features** (friend suggestions, clans)

---

## 📁 File Structure

### Frontend
```
client/frontend/src/
├── pages/
│   ├── landing.jsx                 # Main dashboard
│   ├── MatchPage.jsx              # Live match interface
│   ├── matchmake/
│   │   ├── play.jsx               # PUG queue (P0)
│   │   └── scrim.jsx              # Scrim setup (P1)
│   ├── league/
│   │   ├── createteam.jsx         # Create team (P1)
│   │   ├── registerpay.jsx        # Register for league (P1)
│   │   ├── standings.jsx          # League standings (P1)
│   │   ├── schedule.jsx           # Match schedule (P1)
│   │   └── rules.jsx              # League rules (P2)
│   ├── tournaments/
│   │   ├── browse.jsx             # Browse tournaments (P2)
│   │   ├── my.jsx                 # My tournaments (P2)
│   │   ├── create.jsx             # Create tournament (P2)
│   │   └── history.jsx            # Tournament history (P3)
│   ├── forums/
│   │   ├── index.jsx              # Forum index (P2)
│   │   └── postnew.jsx            # Create post (P2)
│   └── support/
│       ├── faq.jsx                # FAQ (P2)
│       └── tickets.jsx            # Support tickets (P2)
├── contexts/
│   └── WebSocketContext.jsx       # Global WebSocket state
└── components/
    └── (various shared components)
```

### Backend (Django)
```
server/
├── realtime/                      # WebSocket entry point
│   ├── consumers.py               # Main consumer (routes events)
│   └── handlers/
│       ├── lobby_handler.py       # Lobby events
│       ├── match_handler.py       # Match confirmation
│       ├── veto_handler.py        # Veto/side selection
│       └── execution_handler.py   # Live match tracking
├── scrimgg/                       # Core models
│   └── models.py                  # Player, Lobby, Match, Team
├── matchmaking/                   # Queue management
│   └── (algorithm, queue manager)
├── match_system/                  # Match lifecycle
│   └── models.py                  # Match, VetoAction, MatchPlayer
├── lobby/                         # ⚠️ TO CREATE
│   └── manager.py                 # Lobby business logic
├── league/                        # ⚠️ TO CREATE
│   ├── models.py                  # League entities
│   └── manager.py                 # League business logic
├── tournaments/                   # ⚠️ TO CREATE
│   ├── models.py                  # Tournament entities
│   └── manager.py                 # Tournament logic
├── forums/                        # ⚠️ TO CREATE
│   └── (forum models and logic)
└── support/                       # ⚠️ TO CREATE
    └── (support models and logic)
```

---

## 🔑 Key Entities

### Core
- **Player** - User account (puuid, alias, elo, mmr, rank, stats)
- **Lobby** - Group of players (players, leader, queue_type, preferences)
- **Match** - Confirmed match (state, teams, veto data, scores)

### League (NEW)
- **Team** - Competitive team (name, roster, stats)
- **League** - League season (division, format, rules)
- **LeagueMatch** - Scheduled match (teams, time, status)
- **LeagueStanding** - Team ranking (wins, losses, points)

### Tournament (NEW)
- **Tournament** - Tournament (format, bracket_type, prizes)
- **TournamentRegistration** - Team/player signup
- **TournamentMatch** - Bracket match

### Social (NEW)
- **Profile** - Player profile (bio, socials, preferences)
- **ForumThread** - Discussion thread
- **SupportTicket** - Help ticket

---

## 🎮 Common Event Patterns

### Create Entity
```javascript
// Frontend
api.emit('create_lobby', { queue_type: 'pug' })

// Backend
async def handle_create_lobby(data):
    lobby = await manager.create_lobby(data)
    await broadcast('lobby_created', lobby_data)
```

### Update Entity
```javascript
// Frontend
api.emit('update_lobby_preferences', { 
    lobby_id: 'xxx',
    maps: ['Ascent', 'Bind']
})

// Backend
async def handle_update_preferences(data):
    lobby = await manager.update_preferences(data)
    await broadcast_to_lobby('lobby_update', lobby_data)
```

### Real-time Broadcast
```python
# Backend broadcasts to all in group
await self.channel_layer.group_send(
    f"lobby_{lobby_id}",
    {
        'type': 'lobby_update',
        'payload': lobby_data
    }
)
```

---

## 🐛 Debugging Tips

### Check WebSocket Connection
```javascript
// In browser console
console.log(socket.readyState)
// 0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED
```

### Monitor Events
```javascript
// Frontend - log all incoming events
on('*', (event, data) => console.log('Event:', event, data))
```

### Backend Logging
```python
# In handler methods
logger.info(f"Event: {action}, Data: {data}, User: {self.puuid}")
```

### Check Redis
```bash
# Connect to Redis
redis-cli

# View all keys
KEYS *

# Check queue
ZRANGE queue:pug 0 -1 WITHSCORES

# Check lobby data
HGETALL lobby:xxx:preferences
```

---

## ⚡ Performance Tips

### Frontend
1. **Debounce frequent events** (e.g., typing, mouse movement)
2. **Use React.memo** for expensive components
3. **Lazy load** heavy components
4. **Virtualize** long lists

### Backend
1. **Use select_related()** for foreign keys
2. **Use prefetch_related()** for many-to-many
3. **Cache hot data** in Redis
4. **Batch database operations**
5. **Use async/await** properly

### Database
1. **Add indexes** on frequently queried fields
2. **Avoid N+1 queries**
3. **Use pagination** for large result sets
4. **Optimize JSON queries**

---

## 📚 Additional Resources

- [Django Channels Docs](https://channels.readthedocs.io/)
- [React WebSocket Guide](https://react.dev/)
- [Redis Pub/Sub](https://redis.io/topics/pubsub)
- [Material-UI](https://mui.com/)

---

## 📈 Current Implementation Status

### ✅ **What's Already Built** (~40% Complete)

**Core Infrastructure** (Production-Ready)
- ✅ Player model with comprehensive stats (elo, mmr, trueskill, karma, etc.)
- ✅ Lobby model with queue state and preferences
- ✅ Match model with full veto system (server, map, side selection)
- ✅ WebSocket infrastructure (RealtimeConsumer, handlers, broadcasting)
- ✅ Queue management with Redis sorted sets
- ✅ Matchmaker algorithm (MMR-based, rank-aware tolerance, adaptive weighting)
- ✅ Veto system with turn validation and audit trail
- ✅ Match execution with constructor assignment and join tracking

**What This Means**: PUG matchmaking **backend is 70% complete**. The core infrastructure for lobby creation, queue management, matchmaking, veto, and match execution exists and is functional.

### ⚠️ **What's Partially Built** (In Progress)

- ⚠️ Match confirmation/acceptance system (need MatchConfirmation model)
- ⚠️ Frontend integration (WebSocketContext exists but pages not fully wired)
- ⚠️ Queue status broadcasting (need real-time updates)
- ⚠️ ELO calculation on match completion
- ⚠️ Team model (basic structure exists, needs owner/captain/logo fields for leagues)

### ❌ **What's Missing** (Not Started)

**Scrim System** (~30% Complete)
- ❌ ScrimInvite model
- ❌ Ready check system
- ❌ Team captain assignment in lobbies
- ❌ Scrim-specific lobby fields

**League System** (~5% Complete)
- ❌ Entire League Django app
- ❌ All league models (League, LeagueRegistration, LeagueMatch, LeagueStanding)
- ❌ Team expansion (owner, captain, logo)
- ❌ Profile model (bio, social links)

**Tournament System** (~3% Complete)
- ❌ Entire Tournaments Django app
- ❌ All tournament models
- ❌ Bracket generation algorithms

**Community Features** (0% Complete)
- ❌ Forum system (entire Forums app)
- ❌ Support system (entire Support app)

### 🎯 **Development Roadmap**

**Phase 1: Complete PUG Matchmaking** (2-3 weeks)
1. Add MatchConfirmation model and acceptance flow
2. Wire frontend play.jsx to existing backend handlers
3. Add queue status broadcasting
4. Implement ELO calculation
5. Add match completion detection
6. Test full flow: lobby → queue → match → veto → play → completion

**Phase 2: Scrim System** (4-6 weeks)
1. Expand Lobby model with scrim fields
2. Create ScrimInvite model
3. Build ready check system
4. Add scrim handlers
5. Build frontend scrim UI

**Phase 3: League System** (8-12 weeks)
1. Create League Django app
2. Expand Team model
3. Create league models (League, Registration, Match, Standings)
4. Build team management
5. Implement scheduling and standings
6. Build frontend league pages

**Phase 4: Tournament System** (10-16 weeks)
1. Create Tournaments Django app
2. Implement bracket generation
3. Build tournament lifecycle
4. Add admin tools
5. Build frontend tournament pages

**Phase 5: Community Features** (6-10 weeks)
1. Forum system
2. Support/ticketing system
3. Enhanced profiles

**Recommendation**: Focus on **Phase 1** first to get a working PUG system, then evaluate which of Phase 2-5 to prioritize based on user needs.

---

## 🤝 Contributing

When working on a feature:

1. **Read the relevant architecture doc first**
2. **Check implementation status** in page-specific READMEs (they now have detailed status sections)
3. **Create entities** if they don't exist
4. **Implement manager methods** for business logic
5. **Add WebSocket events** to handlers
6. **Test the full flow** (frontend → backend → database → broadcast)
7. **Update documentation** if behavior changes

---

## ❓ Common Questions

**Q: Where do I add a new event?**
A: 
1. Add event name to handler's event list in `consumers.py`
2. Implement handler method in appropriate `handlers/*.py`
3. Add manager method in `*/manager.py`
4. Emit from frontend using `api.emit()`

**Q: How do I broadcast to all players in a match?**
A:
```python
await self.channel_layer.group_send(
    f"match_{match_id}",
    {'type': 'match_update', 'payload': data}
)
```

**Q: Where should business logic go?**
A: In manager classes (`*/manager.py`), NOT in handlers or views

**Q: How do I test WebSocket events?**
A: Use the browser console or write integration tests with `pytest-asyncio`

**Q: What's the difference between frontend, backend, and server?**
A:
- **Frontend** = React app (UI)
- **Backend** = Quart (local bridge between Electron and Django)
- **Server** = Django (main business logic and database)

---

Happy coding! 🚀
