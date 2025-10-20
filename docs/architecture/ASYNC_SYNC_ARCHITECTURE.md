# Async/Sync Architecture - Comprehensive Verification

**Last Updated:** October 13, 2025  
**Status:** ✅ Complete and Production-Ready

---

## Overview
This document details the hybrid async/sync architecture implemented for ScrimGG's matchmaking system, following Django Channels and Celery best practices.

---

## Architecture Philosophy

### Core Principle
**"Use async where it matters (I/O-bound user connections), sync everywhere else (background processing)"**

```
┌──────────────────────────────────────────┐
│  CELERY TASKS (Synchronous)              │
│  • Direct Redis operations               │
│  • Direct Django ORM                     │
│  • No async_to_sync except for WS bridge│
│  • Handles concurrency via workers      │
└──────────────────────────────────────────┘
              ↓
    async_to_sync (channel_layer only)
              ↓
┌──────────────────────────────────────────┐
│  WEBSOCKET CONSUMERS (Asynchronous)      │
│  • Async WebSocket handling              │
│  • sync_to_async for ORM                 │
│  • Native async for Redis/Channels       │
│  • Handles 1000s of connections          │
└──────────────────────────────────────────┘
```

---

## Why This Architecture?

### Celery Best Practices
- Don't pass model instances; pass IDs and re-fetch in task
- Tasks are synchronous; Celery provides async execution
- Re-fetch from database to prevent race conditions
- Use direct ORM calls for reliability and performance

### Django Channels Best Practices
- WebSocket consumers are async; handle many concurrent connections
- Use `sync_to_async` for ORM from async context
- Channel layer is async; use await or `async_to_sync`

---

## Method Inventory (References)
- QueueManager: see `docs/Server/matchmaking.md` for async/sync variants and responsibilities.
- MatchmakerV2: see `docs/Server/match_system.md` for algorithms and sync/async parity.
- MatchConfirmationManager: see `docs/Server/match_system.md` for acceptance flow.
- MatchManager: see `docs/Server/matchpage.md` for veto/start and timeout handling.
- MatchExecutionManager / MatchMonitor: see `docs/Server/match_execution.md`.

---

## Celery Task Implementations (Reference)
- periodic_matchmaking: queue stats, run matchmaker, initiate confirmations (all sync). See `docs/Server/match_system.md`.
- cleanup_expired_matches: validate, requeue, notify (sync with WS bridge). See `docs/Server/match_system.md`.
- check_veto_timeouts: ORM check + handle_veto_timeout_sync + WS broadcast. See `docs/Server/matchpage.md`.
- cleanup_expired_queues: Redis cleanup. See `docs/Server/matchmaking.md`.

---

## Algorithms (High-Level)
- Recursive backtracking for lobby combinations (supports solo → mixed parties)
- Adaptive weighting (MMR/ELO convergence states) for team rating
- Time tolerance expansion based on queue wait

For formulas and code-level details, see `docs/Server/match_system.md`.

---

## Performance Characteristics
- 1,000 concurrent users: ~3% worker utilization (single worker)
- 10,000 concurrent users: ~10% worker utilization (1-2 workers)
- 100,000 concurrent users: partition by region/tier (3-5 workers)

See `docs/Server/performance.md` for measurements and test scripts.

---

## Error Handling & Edge Cases
- Solo queue, mixed party sizes, high MMR spread
- Match expiration, veto timeout, stuck matches

See `docs/Server/testing.md` for scenarios and scripts.

---

## Migration Path
- For Celery tasks: create `_sync` methods, use ORM/Redis directly, WS only via `async_to_sync` bridge
- For WebSocket consumers: async methods, `sync_to_async` for ORM, native await for Channels/Redis

Implementation details: `docs/Server/match_system.md` and `docs/Server/matchpage.md`.

---

## Verification Checklist
- Celery tasks use only `_sync` methods; WS bridge only for group_send
- Async methods preserved for WebSocket consumers
- Tests pass using server scripts in `server/testing/`

---

## Production Deployment
- Celery workers/beat recommended flags; scaling guidelines by concurrency
- See `docs/Server/deployment.md` for commands and options

---

## Troubleshooting
- Common async/sync pitfalls and fixes: see `docs/Server/troubleshooting.md`

---

## Summary
✅ Complete sync/async separation achieved  
✅ Celery tasks follow best practices  
✅ Full feature parity between sync and async  
✅ Scales to 100K+ users with horizontal scaling  
✅ Zero async/sync context errors

