# Match State Validation

## Overview
System behavior to prevent players/parties from queuing while they are in an active match lifecycle.

## Current System Analysis

### Lifecycle States (High-Level)
- Blocks queue: confirmation, veto, side selection, ready, in progress, paused
- Allows queue: completed, cancelled, expired

### Queue Entry Points
1. PugQueue (Find Match)
2. Lobby (Party queue)
3. Server QueueManager (backend queue API)

## System Strategy (References)
- Server validation service and queue integration: see server docs in `docs/Server/` (queue and matchmaking modules).
- Database lookups and indexes for efficient eligibility checks: see `docs/Server/` data access docs.

### WebSocket Integration
- Real-time eligibility updates and queue-block notifications are emitted on match state changes.
- See server consumer docs under `docs/Server/` and client context handling under `docs/Client/frontend/`.

### Frontend Behavior
- UI disables queue actions when `inActiveMatch == true` and provides navigation back to the active match.
- See `docs/Client/frontend/` for WebSocket context and queue UI behavior.

### Data Access
- Use indexed queries and optional caching for fast eligibility checks. See server data-access docs in `docs/Server/`.

### UX Considerations
- Clear notifications for blocked queue attempts and quick navigation to the current match.

## Notes
Planning, prioritization, and timelines are tracked in `docs/implementation/`.

## Testing Strategy
- Server unit tests for validation, integration tests for queue flow, client tests for button states and notifications.

## Security Considerations
- Enforce server-side validation, handle race conditions, maintain state consistency, and ensure performant queries.
