# Scrim.GG Architecture Improvements - FACEIT-like Experience

## 1. WebSocket-First Communication Architecture

### Current Issues:
- React frontend uses REST API (`/command` endpoint) for all operations
- WebSocket endpoint exists but is underutilized
- No real-time state synchronization
- Polling for lobby updates instead of push notifications

### Proposed Architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (Electron)                 │
│                     WebSocket Client                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ WS Connection (localhost:5888/ws)
                           │ Event-Driven Bidirectional
┌──────────────────────────▼──────────────────────────────────┐
│              LOCAL QUART BACKEND (Client Service)            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  WebSocket Manager                                   │   │
│  │  - Handle frontend events                            │   │
│  │  - Broadcast game state changes                      │   │
│  │  - Forward to Django server                          │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Valorant Client Monitor (Game State Service)       │   │
│  │  - Poll local Valorant API every 2-5 seconds        │   │
│  │  - Detect match start/end                            │   │
│  │  - Monitor player state                              │   │
│  │  - Auto-push changes via WebSocket                   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Valorant Controller                                 │   │
│  │  - Execute game actions (join party, start match)   │   │
│  │  - Create custom games                               │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ WS Connection (server:8000/ws/matchmaking/{puuid}/)
                           │ Server Commands & Events
┌──────────────────────────▼──────────────────────────────────┐
│            DJANGO SERVER (Matchmaking Service)               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Django Channels Consumer (PugSocketConsumer)       │   │
│  │  - Player groups (1:1 per player)                   │   │
│  │  - Lobby groups (1:many per lobby)                  │   │
│  │  - Match groups (1:many per match)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Matchmaking Engine (Celery Background Tasks)       │   │
│  │  - Queue management                                  │   │
│  │  - ELO-based pairing                                 │   │
│  │  - Map/server veto system                            │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Match Coordinator                                   │   │
│  │  - Track match state                                 │   │
│  │  - Monitor player connections                        │   │
│  │  - Collect match results                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 2. Event-Driven Communication Protocol

### Frontend → Local Backend Events:
```javascript
// Client-side events
{
  "event": "authenticate",
  "payload": {}
}
{
  "event": "create_lobby",
  "payload": {}
}
{
  "event": "queue_lobby",
  "payload": {
    "lobby_id": "uuid",
    "map_preferences": ["Ascent", "Haven"],
    "server_preferences": ["NA-East"]
  }
}
{
  "event": "accept_match",
  "payload": {
    "match_id": "uuid"
  }
}
{
  "event": "lobby_chat",
  "payload": {
    "message": "Ready?",
    "lobby_id": "uuid"
  }
}
```

### Local Backend → Frontend Events:
```javascript
// Server-side events
{
  "event": "authentication_success",
  "payload": {
    "puuid": "...",
    "player_data": {...}
  }
}
{
  "event": "game_state_change",
  "payload": {
    "state": "in_pregame|in_match|in_menus",
    "match_id": "...",
    "party_id": "..."
  }
}
{
  "event": "match_found",
  "payload": {
    "match_id": "uuid",
    "players": [...],
    "map": "Ascent",
    "server": "NA-East",
    "accept_timeout": 30
  }
}
{
  "event": "lobby_updated",
  "payload": {
    "lobby_id": "uuid",
    "players": [...],
    "in_queue": true
  }
}
```

## 3. Improved Client Backend Structure

### Add Game State Monitor Service:
```python
# game_monitor.py
class ValorantGameMonitor:
    """
    Continuously monitors local Valorant client state
    and broadcasts changes via WebSocket
    """
    
    async def start_monitoring(self):
        """Poll Valorant client every 2 seconds"""
        while self.running:
            try:
                # Check if player is in match
                current_state = self.client.fetch_presence()
                
                # Detect state changes
                if current_state != self.last_state:
                    await self.broadcast_state_change(current_state)
                    
                # Check if match ended
                if self.in_match and self.detect_match_end():
                    await self.handle_match_end()
                    
            except Exception as e:
                print(f"Monitor error: {e}")
                
            await asyncio.sleep(2)
```

## 4. Enhanced Django Server Features

### A. Match Verification System
```python
# Match state tracking with client verification
class MatchVerification:
    - Ensure all 10 players joined the custom game
    - Detect if someone dodges/leaves
    - Apply penalties for leavers
    - Auto-cancel match if someone doesn't join within 2 minutes
```

### B. Automated Veto System
```python
# Map/Server ban-pick system like FACEIT
class VetoSystem:
    - Team A bans a map
    - Team B bans a map
    - Team A picks a server
    - Continue until map/server selected
    - Real-time WebSocket updates during veto
```

### C. Live Match Monitoring
```python
# Track ongoing matches
class MatchMonitor:
    - Wait for all players to report "in_game" state
    - Monitor for disconnections
    - Allow pause/resume
    - Detect match completion
```

### D. Automated Result Collection
```python
# Fetch match results from Valorant API
class ResultCollector:
    - Poll match_id for results
    - Update player stats (kills, deaths, ADR, etc)
    - Calculate ELO changes
    - Store match demo/replay data
```

## 5. Key Features to Implement

### Priority 1: Core Matchmaking Flow
- [ ] Full WebSocket communication (remove REST /command endpoint)
- [ ] Game state monitoring service
- [ ] Match acceptance flow with timeout
- [ ] Automated custom game creation
- [ ] Player verification (all 10 joined)
- [ ] Match cancellation on dodge

### Priority 2: Competitive Features
- [ ] Map/server veto system
- [ ] ELO calculation and ranking system
- [ ] Match history with detailed stats
- [ ] Leaver detection and penalties
- [ ] Player reputation system (karma)
- [ ] Reconnect handling

### Priority 3: Social Features
- [ ] Lobby chat (already partially implemented)
- [ ] Friend system (models exist, needs UI)
- [ ] Player profiles with stats
- [ ] Match notifications
- [ ] Team creation and management

### Priority 4: Anti-Cheat & Integrity
- [ ] Client heartbeat verification
- [ ] Detect Valorant client tampering
- [ ] Match demo storage
- [ ] Report system for cheaters/griefers
- [ ] Admin panel for reviewing reports

### Priority 5: Advanced Features
- [ ] Tournament system
- [ ] League/ladder system
- [ ] Voice chat integration (optional)
- [ ] In-game overlay (optional)
- [ ] Match statistics dashboard
- [ ] Replay system

## 6. Database Schema Improvements

### Current Issues:
- Match model doesn't track individual player performance
- No match state tracking
- Missing veto history
- No penalty/ban tracking

### Recommended Additions:

```python
# Match player performance tracking
class MatchPlayer(models.Model):
    match = models.ForeignKey(Match)
    player = models.ForeignKey(Player)
    team = models.CharField(max_length=10)  # "team_a" or "team_b"
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    combat_score = models.IntegerField(default=0)
    damage_dealt = models.IntegerField(default=0)
    elo_change = models.IntegerField(default=0)
    mvp = models.BooleanField(default=False)
    
# Match state tracking
class MatchState(models.Model):
    match = models.OneToOneField(Match)
    state = models.CharField(max_length=50)  # "created", "accepting", "veto", "ready", "live", "completed", "cancelled"
    players_accepted = models.JSONField(default=list)
    players_joined = models.JSONField(default=list)
    veto_history = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)

# Penalty system
class PlayerPenalty(models.Model):
    player = models.ForeignKey(Player)
    penalty_type = models.CharField(max_length=50)  # "dodge", "leave", "afk", "grief", "toxicity"
    match = models.ForeignKey(Match, null=True)
    reason = models.TextField()
    duration_minutes = models.IntegerField()  # Cooldown time
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    active = models.BooleanField(default=True)
```

## 7. State Management on Frontend

### Use Context + WebSocket Hook:
```javascript
// WebSocketContext.jsx
const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [gameState, setGameState] = useState({});
  const [lobbyState, setLobbyState] = useState({});
  const [matchState, setMatchState] = useState({});
  
  useEffect(() => {
    // Connect to local backend WebSocket
    const ws = new WebSocket('ws://localhost:5888/ws');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleEvent(data.event, data.payload);
    };
    
    setSocket(ws);
    return () => ws.close();
  }, []);
  
  const sendEvent = (event, payload) => {
    socket.send(JSON.stringify({ event, payload }));
  };
  
  return (
    <WebSocketContext.Provider value={{ gameState, lobbyState, matchState, sendEvent }}>
      {children}
    </WebSocketContext.Provider>
  );
};
```

## 8. Match Flow Diagram (FACEIT-style)

```
1. Player opens client → Authenticates with Valorant
   ↓
2. Player creates/joins lobby (1-5 players)
   ↓
3. Lobby leader queues with preferences
   ↓
4. Matchmaking engine finds opponent lobby
   ↓
5. Both teams enter MAP/SERVER VETO phase
   - Team A bans map
   - Team B bans map
   - Team A picks server
   - Final map/server selected
   ↓
6. Match acceptance (30 second timer)
   - All 10 players must accept
   - Any decline → back to queue
   ↓
7. One player designated as "constructor"
   - Creates custom game in Valorant
   - Sends pregame_id to server
   ↓
8. Server sends pregame_id to other 9 players
   - All clients auto-join via party_join(pregame_id)
   ↓
9. Server monitors: Did all 10 join? (2 min timeout)
   - YES → Constructor starts game
   - NO → Cancel match, penalize no-shows
   ↓
10. Match is LIVE
    - Client monitors game state
    - Detects when match ends
    ↓
11. Match ends → Collect results
    - Fetch stats from Valorant API
    - Calculate ELO changes
    - Update player stats
    - Store match demo
    ↓
12. Show post-match summary
    - Player stats
    - ELO changes
    - MVP
```

## 9. Critical Code Changes Needed

### A. Replace REST with WebSocket in React
**File:** `Scrim.GG_Client/scrimgg/frontend/scrimgg/src/utils/WebSocketClient.js`

### B. Implement Event Router in Quart Backend
**File:** `Scrim.GG_Client/scrimgg/backend/bootstrap.py`
- Replace `/command` endpoint with WebSocket event handlers
- Add event routing system

### C. Add Game State Monitor
**File:** `Scrim.GG_Client/scrimgg/backend/game_monitor.py` (NEW)

### D. Enhance Django Consumer
**File:** `ScrimGG/scrimgg/server/scrimgg/matchmaking/consumers.py`
- Add match state management
- Add veto system handlers
- Add player verification logic

### E. Create Match Coordinator Service
**File:** `ScrimGG/scrimgg/server/scrimgg/matchmaking/match_coordinator.py` (NEW)

## 10. Security Considerations

- **Client Validation**: Server should verify all client-reported game states
- **Rate Limiting**: Prevent spam/abuse via rate limits on WebSocket messages
- **Heartbeat**: Implement heartbeat to detect client crashes/disconnects
- **Encryption**: Consider encrypting sensitive WebSocket messages
- **Anti-Tampering**: Validate that Valorant client is legitimate (check process signatures)

## 11. Performance Optimizations

- Use Redis for real-time state caching
- Implement connection pooling for database
- Use Celery for heavy background tasks (ELO calculation, stats processing)
- Add CDN for static assets
- Optimize database queries with select_related/prefetch_related

## 12. Monitoring & Observability

- Log all match events for debugging
- Track WebSocket connection health
- Monitor matchmaking queue times
- Alert on high dodge rates or errors
- Track player retention metrics

