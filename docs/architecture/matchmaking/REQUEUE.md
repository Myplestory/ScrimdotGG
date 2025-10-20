# Requeue Functionality (Concise)

## Summary
On timeout, affected lobbies are requeued automatically; player-decline cancels the match without auto-requeue. The intended behavior is to requeue only lobbies that fully accepted and give them priority bias.

## Current Implementation
- Timeout path: Celery `cleanup_expired_matches` identifies expired confirmations, cancels the match, and requeues participating lobbies.
- Decline path: Cancels the match and returns affected lobbies to the caller (no auto-requeue by design).
- Data note: Persist the lobby leader PUUID (or requeue key) in match state to avoid blocking `sync_to_async` DB lookups during cleanup.

## Next Steps
- Track per-lobby acceptance and requeue only fully-accepting lobbies; apply priority bias to reduce requeue latency.
- Add structured logging around requeue operations for observability.
