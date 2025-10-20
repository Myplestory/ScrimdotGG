# Refactored Architecture - Visual Diagrams

## 🏗️ App Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      REALTIME LAYER                         │
│              (WebSocket Communication)                      │
│  ┌────────────────────────────────────────────────────┐   │
│  │  RealtimeConsumer (Single WebSocket Endpoint)      │   │
│  │  ws://server/ws/matchmaking/{puuid}/               │   │
│  └────────────┬───────────────────────────────────────┘   │
│               │ Routes events to handlers                  │
│     ┌─────────┼─────────┬──────────┬──────────┐           │
│     ↓         ↓         ↓          ↓          ↓           │
│  Lobby    Match     Veto      Execution   Base            │
│  Handler  Handler   Handler   Handler     Handler         │
└─────────────────────────────────────────────────────────────┘
               ↓ Calls business logic ↓
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                             │
│                 (Business Logic Apps)                       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   LOBBY      │  │ MATCHMAKING  │  │ MATCH_SYSTEM │    │
│  │              │  │              │  │              │    │
│  │ - manager.py │  │ - queue_mgr  │  │ - models.py  │    │
│  │ - models.py  │  │ - matchmaker │  │ - managers/  │    │
│  │              │  │ - trueskill  │  │ - tasks.py   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │            │
│         └──────────┬───────┴──────────────────┘            │
│                    ↓                                       │
│         ┌──────────────────────┐                          │
│         │  MATCH_EXECUTION     │                          │
│         │                      │                          │
│         │  - execution_mgr     │                          │
│         │  - monitor.py        │                          │
│         └──────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
               ↓ Uses shared utilities ↓
┌─────────────────────────────────────────────────────────────┐
│                    CORE LAYER                               │
│                 (Shared Utilities)                          │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ redis_manager.py │  │websocket_utils.py│               │
│  │                  │  │                  │               │
│  │ - Redis ops      │  │ - Broadcast      │               │
│  │ - Connection     │  │ - Group send     │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│           ┌──────────────────┐                             │
│           │  exceptions.py   │                             │
│           │                  │                             │
│           │ - Custom errors  │                             │
│           └──────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow - Full Matchmaking Cycle

```
┌─────────────┐
│   CLIENT    │
│ (pugapi.py) │
└──────┬──────┘
       │ 1. Connect WebSocket
       ↓
┌──────────────────────────────────────┐
│  RealtimeConsumer                    │
│  • Subscribe to player_{puuid}       │
└──────┬───────────────────────────────┘
       │ 2. Create lobby
       ↓
┌──────────────────┐      ┌──────────────────┐
│  LobbyHandler    │ ───→ │  LobbyManager    │
│  handle_create   │      │  create_lobby()  │
└──────┬───────────┘      └──────────────────┘
       │ 3. Join lobby group: lobby_{id}
       ↓
┌──────────────────────────────────────┐
│  RealtimeConsumer                    │
│  • Subscribed to lobby_{lobby_id}    │
└──────┬───────────────────────────────┘
       │ 4. Add to queue
       ↓
┌──────────────────┐      ┌──────────────────┐
│  LobbyHandler    │ ───→ │  QueueManager    │
│  handle_add      │      │  enqueue_lobby() │
└──────────────────┘      └─────────┬────────┘
                                    │
       ┌────────────────────────────┘
       │ 5. Periodic matchmaking (Celery Beat)
       ↓
┌──────────────────┐      ┌──────────────────────┐
│  Celery Task     │ ───→ │  MatchmakerV2        │
│  periodic_match  │      │  find_matches_sync() │
└──────────────────┘      └─────────┬────────────┘
                                    │ 6. Match found!
       ┌────────────────────────────┘
       ↓
┌────────────────────────────────────────┐
│  MatchConfirmationManager              │
│  initiate_confirmation_sync()          │
│  • Store in Redis                      │
│  • Broadcast to all lobbies            │
└────────────┬───────────────────────────┘
             │ 7. Broadcast: match_found
             ↓
┌────────────────────────────────────────┐
│  WebSocketBroadcaster                  │
│  broadcast_to_lobby(lobby_id, ...)     │
└────────────┬───────────────────────────┘
             │
       ┌─────┴──────┐
       ↓            ↓
┌─────────────┐  ┌─────────────┐
│  Client 1   │  │  Client 2   │
│  Receives:  │  │  Receives:  │
│  match_found│  │  match_found│
└──────┬──────┘  └──────┬──────┘
       │ 8. Accept       │ 8. Accept
       ↓                 ↓
┌──────────────────┐      ┌──────────────────────┐
│  MatchHandler    │ ───→ │  MatchConfirmation   │
│  handle_accept   │      │  accept_match()      │
└──────────────────┘      └─────────┬────────────┘
                                    │ 9. All accepted!
       ┌────────────────────────────┘
       ↓
┌────────────────────────────────────────┐
│  MatchManager                          │
│  create_match_from_confirmation()      │
│  • Create Match in DB                  │
│  • Initialize veto                     │
└────────────┬───────────────────────────┘
             │ 10. Join match group: match_{id}
             ↓
┌────────────────────────────────────────┐
│  RealtimeConsumer                      │
│  • Now in match_{match_id} group       │
└────────────┬───────────────────────────┘
             │ 11. Broadcast: veto_started
             ↓
┌────────────────────────────────────────┐
│  Clients receive veto started          │
│  Captains veto maps/servers            │
└────────────┬───────────────────────────┘
             │ 12. Veto actions
             ↓
┌──────────────────┐      ┌──────────────────┐
│  VetoHandler     │ ───→ │  MatchManager    │
│  handle_veto_map │      │  veto_map()      │
└──────────────────┘      └─────────┬────────┘
                                    │ 13. Broadcast updates
       ┌────────────────────────────┘
       ↓
┌────────────────────────────────────────┐
│  All players see veto updates          │
│  in real-time                          │
└────────────┬───────────────────────────┘
             │ 14. Veto complete → Side selection
             ↓
┌────────────────────────────────────────┐
│  Captain selects side                  │
└────────────┬───────────────────────────┘
             │ 15. All done!
             ↓
┌──────────────────┐      ┌──────────────────────┐
│  ExecutionHandler│ ───→ │  MatchExecutionMgr   │
│  handle_custom   │      │  assign_constructor()│
└──────────────────┘      └──────────────────────┘
             │ 16. Constructor creates game
             ↓
┌────────────────────────────────────────┐
│  Valorant custom game created          │
│  Players join, match starts!           │
└────────────────────────────────────────┘
```

## 🗂️ Dependency Graph

```
                    ┌──────┐
                    │ core │ (No dependencies)
                    └───┬──┘
                        │
         ┌──────────────┼──────────────┐
         ↓              ↓              ↓
    ┌────────┐    ┌──────────┐    ┌────────┐
    │ lobby  │    │matchmaking│    │ users  │
    └────┬───┘    └─────┬────┘    └────────┘
         │              │
         └──────┬───────┘
                ↓
         ┌──────────────┐
         │ match_system │
         └──────┬───────┘
                ↓
         ┌──────────────────┐
         │ match_execution  │
         └──────┬───────────┘
                ↓
           ┌─────────┐
           │realtime │ (Depends on all)
           └─────────┘
```

**Dependency Rules:**
1. **Core** has NO dependencies (foundation)
2. **Domain apps** (lobby, matchmaking) depend only on core
3. **Match system** depends on domain apps
4. **Match execution** depends on match system
5. **Realtime** depends on ALL (top layer)

## 📡 WebSocket Event Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT SIDE                              │
│  PugSocketClient (client/backend/pugapi.py)                │
│                                                             │
│  ws = websockets.connect('ws://server/ws/matchmaking/{id}')│
└─────────────┬───────────────────────────────────────────────┘
              │
              │ WebSocket Connection
              ↓
┌─────────────────────────────────────────────────────────────┐
│                    SERVER SIDE                              │
│  RealtimeConsumer (single connection per player)           │
│                                                             │
│  Subscribed to groups:                                     │
│  • player_{puuid}     (personal channel)                   │
│  • lobby_{lobby_id}   (when in lobby)                      │
│  • match_{match_id}   (when in match)                      │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ Event received
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Event Routing (based on action name)                      │
│                                                             │
│  Lobby Events → LobbyHandler                               │
│  • create_lobby, add_lobby_to_queue, lobby_message         │
│                                                             │
│  Match Events → MatchHandler                               │
│  • accept_match, decline_match                             │
│                                                             │
│  Veto Events → VetoHandler                                 │
│  • veto_map, veto_server, select_side, get_match_data     │
│                                                             │
│  Execution Events → ExecutionHandler                       │
│  • custom_game_created, player_joined_game, match_started │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ Handler processes
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Handler calls business logic                              │
│                                                             │
│  LobbyHandler → LobbyManager, QueueManager                 │
│  MatchHandler → MatchConfirmationManager                   │
│  VetoHandler → MatchManager (veto methods)                 │
│  ExecutionHandler → MatchExecutionManager                  │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ Business logic executes
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Response Flow                                              │
│                                                             │
│  1. Direct Response (to sender)                            │
│     handler.send_event('lobby_created', data)              │
│                                                             │
│  2. Group Broadcast (to all in group)                      │
│     WebSocketBroadcaster.broadcast_to_lobby(id, event)     │
│                                                             │
│  3. Targeted Broadcast (to specific players)               │
│     WebSocketBroadcaster.broadcast_to_player(puuid, event) │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ Via Django Channels
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Redis Channel Layer                                        │
│                                                             │
│  Groups:                                                    │
│  • player_abc123 → [connection1]                           │
│  • lobby_xyz789  → [conn1, conn2, conn3, conn4, conn5]     │
│  • match_def456  → [conn1, conn2, ..., conn10]             │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ Delivered to WebSocket
              ↓
┌─────────────────────────────────────────────────────────────┐
│  CLIENT RECEIVES                                            │
│                                                             │
│  await handle_message(message)                             │
│  • Route by event type                                     │
│  • Update UI                                               │
│  • Trigger game actions                                    │
└─────────────────────────────────────────────────────────────┘
```

## 🔒 Backward Compatibility

```
┌─────────────────────────────────────────────────────────────┐
│  OLD CLIENT CODE (No changes needed!)                      │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  WebSocket Connection                                       │
│  ws://server/ws/matchmaking/{puuid}/   ✅ STILL WORKS      │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Event Format (unchanged)                                   │
│  {                                                          │
│    "event": "veto_map",                                     │
│    "payload": {"match_id": "...", "map": "Bind"}           │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  NEW SERVER CODE                                            │
│  RealtimeConsumer (was PugSocketConsumer)                  │
│  • Same URL pattern                                         │
│  • Same event names                                         │
│  • Same response format                                     │
│  • Internal routing to handlers (invisible to client)      │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  OLD CLIENT CODE                                            │
│  Receives same events, same format                         │
│  NO CHANGES NEEDED! ✅                                      │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│  scrimgg (main app)                                         │
├─────────────────────────────────────────────────────────────┤
│  scrimgg_player                                             │
│  • puuid (PK)                                               │
│  • alias, elo, mmr                                          │
│  • trueskill_mu, trueskill_sigma                           │
│                                                             │
│  scrimgg_lobby                                              │
│  • id (UUID, PK)                                            │
│  • lobby_leader_id (FK → Player)                            │
│  • players (M2M → Player)                                   │
│  • in_queue, queue_type                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  match_system (NEW)                                         │
├─────────────────────────────────────────────────────────────┤
│  match_system_match                                         │
│  • id (UUID, PK)                                            │
│  • state (CONFIRMED, VETO, IN_PROGRESS, etc.)              │
│  • team_a_players, team_b_players (JSON)                   │
│  • map_pool, vetoed_maps, final_map                        │
│  • veto_turn, veto_deadline                                │
│  • pregame_id, coregame_id                                 │
│                                                             │
│  match_system_match_player                                  │
│  • id (PK)                                                  │
│  • match_id (FK → Match)                                    │
│  • player_puuid                                             │
│  • team, is_captain                                         │
│  • joined_pregame, join_attempts                           │
│                                                             │
│  match_system_veto_action                                   │
│  • id (PK)                                                  │
│  • match_id (FK → Match)                                    │
│  • action_type (BAN, PICK, TIMEOUT)                        │
│  • map_name, team                                           │
│  • sequence_number                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Redis (Queue & State)                                      │
├─────────────────────────────────────────────────────────────┤
│  matchmaking:queue:pug                 (Sorted Set)         │
│  • lobby_id → score (average_elo)                          │
│                                                             │
│  matchmaking:lobby_data:{lobby_id}     (Hash)              │
│  • JSON blob with lobby data                                │
│                                                             │
│  matchmaking:confirmation:{match_id}   (Hash)              │
│  • Match confirmation data                                  │
│  • Accepted players list                                    │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Summary

This architecture provides:
- ✅ **Clear separation** of concerns
- ✅ **Single responsibility** per app
- ✅ **Backward compatibility** with existing clients
- ✅ **Scalability** for future growth
- ✅ **Testability** through isolation
- ✅ **Maintainability** with organized code

All while keeping the same external API and WebSocket interface!

