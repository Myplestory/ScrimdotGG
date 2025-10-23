# Frontend Architecture Documentation

This directory contains comprehensive architecture documentation for all pages in the Scrim.GG frontend application.

## 📚 Documentation Structure

### 🌟 Essential Reading
- **[QUICK_START.md](./QUICK_START.md)** - ⭐ **START HERE!** Quick guide to get oriented
- **[COMPLETE_ARCHITECTURE_SUMMARY.md](./COMPLETE_ARCHITECTURE_SUMMARY.md)** - Complete system overview (all pages, events, entities)
- **[ENTITY_RELATIONSHIPS.md](./ENTITY_RELATIONSHIPS.md)** - Entity relationships and database queries

### 📖 Detailed Page Documentation
Individual page documentation organized by folder (see below)

## Architecture Flow

```
Frontend (React/Electron) 
    ↓ WebSocket (ws://localhost:5888)
    ↓
Quart Backend (Python - clientapi.py)
    ↓ HTTP/WebSocket
    ↓
Django Server (Python - realtime/consumers.py)
    ↓ Business Logic Routing
    ↓
Django Apps (lobby, match_system, matchmaking, league, tournaments, etc.)
```

## Event-Driven Architecture

The application uses an event-driven architecture with WebSocket connections:

1. **Frontend → Quart**: Client emits events via WebSocket
2. **Quart → Django**: Quart forwards events to Django server
3. **Django Routing**: `realtime/consumers.py` routes events to specialized handlers
4. **Business Logic**: Handlers delegate to domain-specific managers
5. **Pub/Sub**: Redis channels broadcast updates to all connected clients
6. **Django → Frontend**: Real-time updates pushed to clients

## Directory Structure

### `/pages` - Main Application Pages
- **`/matchmake`** - Matchmaking and queue system
  - `play.jsx` - PUG queue interface
  - `scrim.jsx` - Scrim/custom match interface
  
- **`/league`** - League management
  - `createteam.jsx` - Team creation and roster management
  - `registerpay.jsx` - League registration and payment
  - `standings.jsx` - League standings and rankings
  - `schedule.jsx` - Match schedule and fixtures
  - `rules.jsx` - League rules and regulations
  
- **`/forums`** - Community forums
  - `index.jsx` - Forum browser
  - `postnew.jsx` - Create new post
  
- **`/tournaments`** - Tournament system
  - `browse.jsx` - Browse available tournaments
  - `my.jsx` - User's tournament registrations
  - `create.jsx` - Create new tournament
  - `history.jsx` - Past tournaments
  
- **`/support`** - User support
  - `faq.jsx` - Frequently asked questions
  - `tickets.jsx` - Support ticket system
  
- **`/client`** - Client application
  - `download.jsx` - Download client application

### Special Pages
- `landing.jsx` - Main dashboard (home, lobby switcher)
- `MatchPage.jsx` - Live match interface
- `layout.jsx` - Shared layout wrapper

## Core Entities

### Primary Models (Django)
- **Player** - User profile, stats, MMR, rank
- **Lobby** - Group of players, queue preferences
- **Match** - Active/completed matches
- **MatchPlayer** - Player participation in matches
- **Team** - League teams and rosters
- **VetoAction** - Map/server veto history

### State Management (Frontend)
- **WebSocketContext** - Global WebSocket connection and state
- **PlayerData** - Current user information
- **LobbyData** - Current lobby state
- **MatchData** - Active match information
- **QueueStatus** - Queue state and eligibility

## 📖 Documentation By Feature

### 🎮 Matchmaking Pages
- **[Overview](./matchmake/README.md)** - Matchmaking system overview
- **[Play Page](./matchmake/PLAY_PAGE.md)** - PUG queue and matchmaking (PRIORITY: P0)
  - Lobby creation and management
  - Queue entry and status
  - Match finding and acceptance
  - Real-time updates
- **[Scrim Page](./matchmake/SCRIM_PAGE.md)** - Custom scrim setup (PRIORITY: P1)
  - Scrim lobby creation
  - Team invitation system
  - Ready check system
  - Match configuration

### 🏆 League Pages
- **[League System](./league/README.md)** - Complete league architecture (PRIORITY: P1)
  - **Create Team** - Team creation and roster management
  - **Register/Pay** - League registration and payment
  - **Standings** - League standings and rankings
  - **Schedule** - Match schedule and fixtures
  - **Rules** - League rules and regulations

### 🎯 Tournament Pages
- **[Tournament System](./tournaments/README.md)** - Tournament architecture (PRIORITY: P2)
  - **Browse** - Discover tournaments
  - **My Tournaments** - User's tournament registrations
  - **Create** - Tournament creation and configuration
  - **History** - Past tournament results

### 💬 Forum Pages
- **[Forum System](./forums/README.md)** - Community forums (PRIORITY: P2)
  - **Forum Index** - Browse categories and threads
  - **Post New** - Create new discussions
  - Like, reply, and moderation systems

### 🛟 Support Pages
- **[Support System](./support/README.md)** - Help and support (PRIORITY: P2)
  - **FAQ** - Self-service knowledge base
  - **Support Tickets** - Ticket creation and management

### 🎯 Core Pages
- **[Core System](./core/README.md)** - Essential pages (PRIORITY: P0)
  - **Landing Page** - Main dashboard
  - **Match Page** - Live match interface with veto and statistics
  - **Profile/Home** - Player profile and stats

## Key Patterns

### 1. Event Emission Pattern
```javascript
// Frontend sends event
api.emit('event_name', { payload_data });

// Backend receives and routes
async def receive(self, text_data):
    data = json.loads(text_data)
    handler = self._get_handler_for_action(data['event'])
    await handler.handle_event(data['event'], data)
```

### 2. State Subscription Pattern
```javascript
// Frontend subscribes to state updates
useEffect(() => {
    const handler = (data) => setState(data);
    on('state_update', handler);
    return () => off('state_update', handler);
}, []);
```

### 3. Group Broadcasting Pattern
```python
# Backend broadcasts to group
await self.channel_layer.group_send(
    f"lobby_{lobby_id}",
    {'type': 'lobby_update', 'lobby': lobby_data}
)
```

## Common Event Types

- **Lobby Events**: `create_lobby`, `join_lobby`, `leave_lobby`, `lobby_update`
- **Queue Events**: `add_to_queue`, `remove_from_queue`, `queue_status`
- **Match Events**: `match_found`, `accept_match`, `match_ready`, `match_update`
- **Veto Events**: `veto_map`, `veto_server`, `select_side`
- **Chat Events**: `lobby_message`, `match_message`

## Next Steps

Review individual page architectures for detailed entity relationships, events, and data flow requirements.
