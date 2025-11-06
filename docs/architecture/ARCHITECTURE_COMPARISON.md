# Architecture Comparison: Before vs After

Visual comparison of the previous monolith and the modular architecture.

---

## Previous Architecture (Monolithic)
- Single large WebSocket endpoint and ~40+ handlers in one file
- Global state, ad-hoc lifecycle, no validation layer
- Electron startup with timers, brittle process cleanup

Data flow and anti-patterns summarized; details moved to server/client docs.

---

## New Architecture (Modular)
- App factory, lifecycle hooks, health checks
- WebSocket routing → domain handlers (status/auth/lobby/queue/match/veto/chat)
- Typed envelopes and payload validation
- Clean Electron startup and shutdown

See:
- Diagram: `architecture/ARCHITECTURE_DIAGRAM.md`
- Async/Sync rationale: `architecture/ASYNC_SYNC_ARCHITECTURE.md`
- Server modules and responsibilities: `docs/Server/*`
- Client service and UI handlers: `docs/Client/*`

---

## Message Flow (Before vs After)
- Before: monolithic route, manual JSON parse, direct global state access
- After: validated envelope, event registry, isolated handlers, connection manager

For concrete examples, see `docs/Server/matchpage.md` and client docs.

---

## Electron Integration (Before vs After)
- Before: spawn with shell, fixed wait, brittle cleanup
- After: health polling, tracked PID, tree-kill cleanup

---

## Outcome Summary
- Smaller files, clearer boundaries, type-safe messaging
- Production lifecycle with health checks and graceful shutdown
- Easier testing and future feature additions

For migration steps and timelines, see `docs/implementation/`.

