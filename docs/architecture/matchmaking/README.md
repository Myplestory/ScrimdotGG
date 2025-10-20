# Matchmaking System Overview (Concise)

Concise overview of the matchmaking algorithm, rating systems, tolerance, and requeueing logic as implemented today.

---

## Core System

### Rating Systems
- **[MMR_ELO_SYSTEM.md](./MMR_ELO_SYSTEM.md)** - Hybrid MMR/ELO rating system design
  - Hidden MMR for accurate skill tracking (TrueSkill-based)
  - Display ELO for player-facing ranks
  - Adaptive weighting based on convergence

- **[TRUESKILL.md](./TRUESKILL.md)** - TrueSkill details
  - Uncertainty (sigma) management and conservative rating
  - `mu`-to-ELO/MMR mappings
  - Uncertainty decay for returning players

### Matchmaking Algorithm
- Scheduler
  - Matchmaker runs periodically (≈10s cadence)
  - Cleanup runs periodically (≈10s) to reclaim expired confirmations
- Tolerance & Bias
  - Rank-aware tolerance tiers with linear per-minute expansion and caps
  - Adaptive weighting blends hidden MMR and display ELO; priority bias planned (see [PRIORITY_BIAS.md](./PRIORITY_BIAS.md))
- Core algorithm fixes are captured in the bug folder; current behavior reflects those fixes

---

## Requeue System

Handles match timeouts and requeueing under strict rules.

- See `./bug/ALL_REQUEUE_FIXES_FINAL_SUMMARY.md` for high-level background; detailed analyses live alongside it.
- Implementation overview: **[REQUEUE.md](./REQUEUE.md)**

---

## Architecture

### Key Components

#### 1. **Matchmaker** (`matchmaking.py`)
- MMR-based matching
- Time tolerance calculation
- Multi-lobby combinations (2-10 lobbies → 10 players)
- Snake draft team balancing

#### 2. **QueueManager** (`queue_manager.py`)
- Redis sorted set for lobbies (scored by ELO)
- `queued_at` timestamp tracking
- TTL management

#### 3. **MatchConfirmationManager** (`match_confirmation.py`)
- 30-second acceptance window
- Per-lobby acceptance tracking
- Automatic requeueing on timeout
- Only requeues lobbies where ALL players accepted

#### 4. **Cleanup Tasks** (`tasks.py`)
- `cleanup_expired_matches` - periodic detection
- Handles timeouts and requeueing
- Preserves original queue timestamps

---

## Flow Diagram (High Level)
```
1) Lobbies enter queue (queued_at recorded)
2) Matchmaker runs → tolerance expands with time → candidate combinations
3) Match proposed → 30s acceptance window (per-lobby)
4a) All accept → match ready
4b) Some decline/timeout → cleanup → requeue per policy
```

---

## Key Concepts

### Adaptive Weighting
Balances hidden MMR and display ELO based on convergence state:
- Converged (small gap): Slightly more weight on display ELO
- Diverging (large gap): More weight on hidden MMR
- Moderate: Balanced weighting

### Time Tolerance
Expands matchmaking range based on wait time:
- Base tolerance varies by MMR tier
- Per-minute expansion linear
- Maximum caps prevent poor-quality matches

### Requeueing Logic (Current)
- Timeouts: requeue affected lobbies
- Decline: cancel match; no auto-requeue (future: smart requeue & priority bias)

---

## Performance
- Matchmaker: ~10–50ms per run (queue-size dependent)
- Queue operations: O(log N) Redis sorted set
- Match confirmation: O(1) Redis hash ops
- Cleanup: O(N) where N = active matches

---

## Testing
See `../testing/` for:
- Bot testing framework
- Acceptance flow tests
- Requeue validation

---

**Last Updated**: October 2025

