# Phase 1: Lobby System Enhancement - Implementation Complete

## 📋 Overview

Phase 1 of the PUG matchmaking service has been successfully implemented. This phase establishes the foundation of a lobby-first architecture where every player (even solo queuers) is part of a lobby, providing consistency and scalability for future matchmaking features.

---

## ✅ Completed Tasks

### 1. Enhanced Lobby Model (`server/scrimgg/models.py`)

**Added Fields:**
- `queue_type` (CharField): Type of queue ('pug', 'scrim', 'custom')
- `map_preferences` (JSONField): List of preferred maps
- `server_preferences` (JSONField): List of preferred servers
- `elo_range` (JSONField): Min/max ELO in lobby for matchmaking
- `max_size` (IntegerField): Maximum lobby size (default: 5)
- `created_at` (DateTimeField): Lobby creation timestamp
- `queued_at` (DateTimeField): When lobby joined queue
- `__str__` method for better Django admin display

**Purpose:**
These fields enable the matchmaking system to make intelligent decisions about player grouping, map selection, and team balancing.

---

### 2. LobbyManager Service (`server/matchmaking/lobby_manager.py`)

**A comprehensive service class that handles all lobby operations:**

#### Methods Implemented:

1. **`create_lobby(player_puuid)`**
   - Creates new lobby with player as leader
   - Checks for existing active lobby (prevents duplicates)
   - Initializes lobby stats (size, ELO)
   - Returns serialized lobby data

2. **`add_player_to_lobby(lobby_id, player_puuid, inviter_puuid)`**
   - Adds player to existing lobby via invite
   - Validates lobby capacity (max 5 players)
   - Prevents adding players while in queue
   - Checks for duplicate memberships
   - Updates lobby stats after addition

3. **`remove_player_from_lobby(lobby_id, player_puuid, kicked_by)`**
   - Removes player from lobby (kick or leave)
   - Transfers leadership if leader leaves
   - Disbands lobby if no players remain
   - Updates lobby stats after removal

4. **`disband_lobby(lobby_id)`**
   - Marks lobby as inactive
   - Removes from queue if queued
   - Cleanup operation for empty lobbies

5. **`update_lobby_preferences(lobby_id, map_preferences, server_preferences, requester_puuid)`**
   - Updates matchmaking preferences
   - Only lobby leader can update
   - Validates requester permissions

6. **`validate_queue_eligibility(lobby_id)`**
   - Checks if lobby can join queue
   - Validates minimum map selections (5)
   - Ensures lobby is active and not already in queue
   - Returns detailed eligibility status

7. **`get_lobby_by_player(player_puuid)`**
   - Retrieves active lobby for a player
   - Returns None if player not in active lobby

#### Helper Methods:

- **`_update_lobby_stats(lobby)`**: Calculates average ELO, ELO range, and size
- **`_serialize_lobby(lobby)`**: Converts lobby model to API-friendly dictionary

---

### 3. Enhanced Django Consumer (`server/matchmaking/consumers.py`)

**Added Event Handlers:**

#### Incoming Events (Client → Server):

| Event | Handler | Description |
|-------|---------|-------------|
| `create_lobby` | `create_lobby()` | Create new lobby using LobbyManager |
| `invite_to_lobby` | `invite_to_lobby()` | Invite player to lobby |
| `kick_from_lobby` | `kick_from_lobby()` | Kick player from lobby (leader only) |
| `leave_lobby` | `leave_lobby()` | Player leaves lobby voluntarily |
| `update_lobby_preferences` | `update_lobby_preferences()` | Update map/server preferences |

#### Outgoing Events (Server → Client):

| Event | Description | Broadcast To |
|-------|-------------|--------------|
| `lobby_created` | Lobby successfully created | Requesting client |
| `lobby_updated` | Lobby data changed | All lobby members |
| `player_joined_lobby` | Player added to lobby | All lobby members |
| `player_left_lobby` | Player removed from lobby | All lobby members |
| `kicked_from_lobby` | Player was kicked | Kicked player only |
| `lobby_disbanded` | Lobby closed (no members) | All former members |
| `lobby_preferences_updated` | Preferences changed | All lobby members |

---

## 🏗️ Architecture Decisions

### 1. **Lobby-First Design**
Every player must be in a lobby to queue. This provides:
- **Consistency**: Same code path for solo and party queues
- **Scalability**: Easy to add party features later
- **Simplicity**: Single matchmaking algorithm handles all cases

### 2. **Service Layer Pattern**
`LobbyManager` provides a clean separation between business logic and WebSocket communication:
- **Reusability**: Can be called from REST API, WebSockets, or Celery tasks
- **Testability**: Easy to unit test without WebSocket complexity
- **Maintainability**: Single source of truth for lobby operations

### 3. **Async/Await Throughout**
All operations use `async`/`await` with `sync_to_async` for Django ORM:
- **Performance**: Non-blocking I/O for WebSocket operations
- **Scalability**: Can handle many concurrent connections
- **Compatibility**: Works with Django Channels async architecture

### 4. **Comprehensive Validation**
Every operation validates:
- Player permissions (leader vs member)
- Lobby state (active, in queue, full)
- Player state (already in lobby, not found)
- Returns detailed error messages for debugging

---

## 🔄 Event Flow Examples

### Example 1: Solo Player Creates Lobby and Queues

```
1. Client → Server: { event: 'create_lobby', payload: { puuid: 'player123' } }
2. Server creates lobby (size=1, leader=player123)
3. Server → Client: { event: 'lobby_created', data: { id: 'lobby-uuid', ... } }
4. Client → Server: { event: 'update_lobby_preferences', payload: { lobby_id: 'lobby-uuid', map_preferences: [...] } }
5. Server → All Lobby Members: { event: 'lobby_preferences_updated', ... }
```

### Example 2: Player Invites Friend to Lobby

```
1. Client → Server: { event: 'invite_to_lobby', payload: { lobby_id: 'lobby-uuid', player_puuid: 'friend456', inviter_puuid: 'player123' } }
2. Server validates:
   - Lobby not full
   - Not in queue
   - Friend not in another lobby
3. Server adds friend to lobby
4. Server → All Lobby Members: { event: 'player_joined_lobby', data: { player_puuid: 'friend456', lobby: {...} } }
```

### Example 3: Leader Leaves Lobby

```
1. Client → Server: { event: 'leave_lobby', payload: { lobby_id: 'lobby-uuid', player_puuid: 'player123' } }
2. Server removes player
3. Server transfers leadership to next player
4. Server → All Remaining Members: { event: 'player_left_lobby', data: { reason: 'left', lobby: {...} } }
5. Server → Leaving Player: { event: 'left_lobby', data: { ... } }
```

---

## 📊 Database Schema Updates

### Updated `Lobby` Model Fields:

```python
class Lobby(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    players = ManyToManyField(Player, related_name='lobbies')
    lobby_leader = ForeignKey(Player, on_delete=SET_NULL, null=True, related_name='led_lobbies')
    
    # State
    is_active = BooleanField(default=True)
    in_queue = BooleanField(default=False)
    queue_type = CharField(max_length=20, default='pug')  # NEW
    
    # Preferences
    map_preferences = JSONField(default=list)  # NEW
    server_preferences = JSONField(default=list)  # NEW
    
    # Stats
    average_elo = FloatField(default=0.0)
    elo_range = JSONField(default=dict)  # NEW
    size = IntegerField(default=0)
    max_size = IntegerField(default=5)  # NEW
    
    # Timestamps
    created_at = DateTimeField(auto_now_add=True)  # NEW
    queued_at = DateTimeField(null=True, blank=True)  # NEW
```

---

## 🚀 Next Steps (Phase 2: Queue System)

Now that Phase 1 is complete, the next phase will implement:

1. **Queue Manager Service** (`server/matchmaking/queue_manager.py`)
   - Redis-based queue storage
   - Priority scoring for matchmaking
   - Queue statistics and wait times

2. **Matchmaker Algorithm** (`server/matchmaking/matchmaker.py`)
   - Find 10 players from queued lobbies
   - Balance teams by ELO
   - Consider map/server preferences
   - Match quality scoring

3. **Match Confirmation System** (`server/matchmaking/match_confirmation.py`)
   - 30-second acceptance window
   - Track player responses
   - Handle dodges and timeouts
   - Requeue accepting players

4. **Celery Background Tasks** (`server/matchmaking/tasks.py`)
   - Periodic matchmaking (every 5 seconds)
   - Timeout handling
   - Queue cleanup

---

## 🧪 Testing Instructions

### Prerequisites:
```bash
# Make sure Redis is running
redis-server

# Activate virtual environment
cd server
pipenv shell

# Run migrations
python manage.py makemigrations scrimgg
python manage.py migrate

# Start Django server
python manage.py runserver
```

### Manual Testing:

1. **Test Lobby Creation:**
   ```javascript
   // WebSocket connection to: ws://localhost:8000/ws/matchmaking/{puuid}/
   ws.send(JSON.stringify({
     event: 'create_lobby',
     payload: { puuid: 'test-player-123' }
   }));
   ```

2. **Test Invite:**
   ```javascript
   ws.send(JSON.stringify({
     event: 'invite_to_lobby',
     payload: {
       lobby_id: 'lobby-uuid-from-creation',
       player_puuid: 'friend-456',
       inviter_puuid: 'test-player-123'
     }
   }));
   ```

3. **Test Preferences Update:**
   ```javascript
   ws.send(JSON.stringify({
     event: 'update_lobby_preferences',
     payload: {
       lobby_id: 'lobby-uuid',
       requester_puuid: 'test-player-123',
       map_preferences: ['Ascent', 'Bind', 'Haven', 'Pearl', 'Split'],
       server_preferences: ['Virginia', 'Illinois']
     }
   }));
   ```

4. **Test Leave:**
   ```javascript
   ws.send(JSON.stringify({
     event: 'leave_lobby',
     payload: {
       lobby_id: 'lobby-uuid',
       player_puuid: 'test-player-123'
     }
   }));
   ```

---

## 📝 API Reference

### WebSocket Events

All events follow this format:
```json
{
  "event": "event_name",
  "payload": {
    // event-specific data
  }
}
```

### Incoming Events

#### `create_lobby`
**Payload:**
```json
{
  "puuid": "player_puuid"
}
```
**Response:**
```json
{
  "event": "lobby_created",
  "data": {
    "id": "lobby-uuid",
    "lobby_leader": { "puuid": "...", "alias": "...", "elo": 1500 },
    "players": [...],
    "size": 1,
    "max_size": 5,
    "average_elo": 1500,
    "map_preferences": [],
    "server_preferences": [],
    ...
  }
}
```

#### `invite_to_lobby`
**Payload:**
```json
{
  "lobby_id": "lobby-uuid",
  "player_puuid": "friend-puuid",
  "inviter_puuid": "inviter-puuid"
}
```

#### `kick_from_lobby`
**Payload:**
```json
{
  "lobby_id": "lobby-uuid",
  "player_puuid": "player-to-kick",
  "kicker_puuid": "leader-puuid"
}
```

#### `leave_lobby`
**Payload:**
```json
{
  "lobby_id": "lobby-uuid",
  "player_puuid": "leaving-player"
}
```

#### `update_lobby_preferences`
**Payload:**
```json
{
  "lobby_id": "lobby-uuid",
  "requester_puuid": "leader-puuid",
  "map_preferences": ["Ascent", "Bind", ...],
  "server_preferences": ["Virginia", "Illinois", ...]
}
```

---

## ⚠️ Important Notes

### Migration Required
Before testing, you **must** run database migrations:
```bash
cd server
python manage.py makemigrations scrimgg
python manage.py migrate
```

### Redis Dependency
The system uses Redis for caching and channel layers. Ensure Redis is running before starting the Django server.

### Logging
All operations are logged using Python's logging module. Check console output for debugging information.

### WebSocket Groups
Each lobby has a WebSocket group (`lobby_{lobby_id}`) for broadcasting updates. Players are automatically added/removed from groups when joining/leaving lobbies.

---

## 🎉 Summary

Phase 1 provides a solid foundation for the PUG matchmaking system:

- ✅ **Lobby Model Enhanced** with queue and matchmaking fields
- ✅ **LobbyManager Service** for all lobby operations
- ✅ **Django Consumer Updated** with new event handlers
- ✅ **WebSocket Events** for real-time lobby management
- ✅ **Validation & Error Handling** throughout
- ✅ **Documentation** complete

**Lines of Code Added:**
- Lobby Model: ~30 lines
- LobbyManager: ~450 lines
- Consumer Updates: ~250 lines
- **Total: ~730 lines of production code**

The system is now ready for Phase 2: Queue System Implementation!

---

## 📞 Questions or Issues?

If you encounter any issues during testing:
1. Check Django server logs for errors
2. Verify Redis is running
3. Ensure migrations are applied
4. Check WebSocket connection in browser DevTools
5. Review payload format matches API specification

---

**Implementation Date:** October 11, 2025  
**Author:** AI Assistant  
**Status:** ✅ Complete and Ready for Testing

