# Refactored Architecture - Visual Diagrams

## 🏗️ App Layer Architecture
```
<diagram of realtime/domain/core layers>
```

## 🔄 Data Flow - Full Matchmaking Cycle
```
<end-to-end sequence from queue to live match>
```

## 🗂️ Dependency Graph
```
<module dependency graph showing core → domain → match_system → match_execution → realtime>
```

## 📡 WebSocket Event Flow
- Client groups (player/lobby/match), event routing to domain handlers, broadcast patterns
- For event lists and payload shapes, see Client/Server docs

## 🔒 Backward Compatibility
- External WS API and message shapes preserved

## 📦 Database Schema
- High-level entities only (players, lobbies, matches, veto actions)
- Full schema lives in `docs/Server/` (models/migrations/specs)

## 🎯 Summary
- Clear separation, backward compatibility, scalability, testability, maintainability

References:
- `architecture/ARCHITECTURE_COMPARISON.md` (before/after)
- `architecture/ASYNC_SYNC_ARCHITECTURE.md` (runtime split)
- `docs/Server/*`, `docs/Client/*` (code-level details)

