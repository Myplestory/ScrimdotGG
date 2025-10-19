# Django App Refactor Implementation Plan

## Overview
Split the monolithic `matchmaking` app into focused, domain-driven apps following Django best practices.

## New App Structure

```
server/
├── matchmaking/          # CORE: Queue + Matchmaker only
├── match_system/         # NEW: Match lifecycle (confirmation, veto, side selection)
├── match_execution/      # NEW: Live game management and monitoring
├── realtime/            # NEW: WebSocket consumer layer
├── core/                # NEW: Shared utilities
├── lobby/               # EXISTING: Enhanced with lobby_manager
└── [existing apps...]
```

## Implementation Phases

### Phase 1: Create New Apps ✓
- Create app directories and basic Django structure
- Add to INSTALLED_APPS (order matters for migrations)

### Phase 2: Move Models ✓
- Move Match, MatchPlayer, VetoAction to match_system
- Create database migrations
- Update foreign key references

### Phase 3: Relocate Managers ✓
- Move match_manager, match_confirmation to match_system
- Move match_execution, match_monitor to match_execution
- Move lobby_manager to lobby app
- Update all imports

### Phase 4: Split WebSocket Consumers ✓
- Extract handler classes in realtime app
- Keep single WebSocket endpoint (backward compatible)
- Update routing

### Phase 5: Distribute Celery Tasks ✓
- Split tasks.py by domain
- Update Celery configuration
- Update task routing

### Phase 6: Update Configuration ✓
- Update settings.py
- Update ASGI routing
- Update URL patterns

### Phase 7: Testing & Validation
- Run migrations
- Test all WebSocket events
- Test Celery tasks
- Integration tests

## Rollback Plan
Each phase is reversible. Keep git commits granular.

## Timeline
Estimated: 2-3 days for careful implementation and testing

