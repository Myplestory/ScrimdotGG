# Matchmaking System Documentation

Documentation for the core matchmaking algorithm, MMR/ELO systems, and requeueing logic.

---

## Core System

### Rating Systems
- **[MMR_ELO_SYSTEM.md](./MMR_ELO_SYSTEM.md)** - Hybrid MMR/ELO rating system design
  - Hidden MMR for accurate skill tracking
  - Display ELO for player-facing ranks
  - Adaptive weighting based on convergence

- **[TRUESKILL_INTEGRATION.md](./TRUESKILL_INTEGRATION.md)** - TrueSkill integration
  - Uncertainty (sigma) management
  - Skill estimation (mu) calculations
  - Return player uncertainty decay

### Matchmaking Algorithm
- **[MATCHMAKING_SCHEDULE_ANALYSIS.md](./MATCHMAKING_SCHEDULE_ANALYSIS.md)** - Task scheduling
  - Matchmaker runs every 10 seconds
  - Cleanup runs every 10 seconds
  - Industry-standard timings

- **[PRIORITY_BIAS_STATUS.md](./PRIORITY_BIAS_STATUS.md)** - Time tolerance & bias
  - Rank-aware tolerance tiers
  - Time-based tolerance expansion
  - Adaptive weighting implementation

- **[MATCHMAKER_FIX.md](./MATCHMAKER_FIX.md)** - Core algorithm fixes

---

## Requeue System

The requeue system handles match timeouts and returns lobbies to the queue.

### Comprehensive Documentation
- **[FINAL_REQUEUE_FIXES_COMPLETE.md](./FINAL_REQUEUE_FIXES_COMPLETE.md)** - ⭐ **START HERE**
  - Complete implementation details
  - All fixes consolidated
  - Per-lobby acceptance logic

- **[ALL_REQUEUE_FIXES_FINAL_SUMMARY.md](./ALL_REQUEUE_FIXES_FINAL_SUMMARY.md)** - Executive summary
  - High-level overview
  - Key changes summary

### Analysis & Debugging
- **[COMPREHENSIVE_REQUEUE_ANALYSIS.md](./COMPREHENSIVE_REQUEUE_ANALYSIS.md)** - Deep dive analysis
- **[CRITICAL_BUG_FOUND_MATCH_LOBBIES.md](./CRITICAL_BUG_FOUND_MATCH_LOBBIES.md)** - Critical bug fix
  - `match_lobbies` preservation issue
  - Data structure fix

### Historical Fixes
- [REQUEUE_FUNCTIONALITY_REVIEW.md](./REQUEUE_FUNCTIONALITY_REVIEW.md) - Functionality review
- [REQUEUE_FIXES_COMPLETE.md](./REQUEUE_FIXES_COMPLETE.md) - Initial fixes
- [REQUEUE_FIX_FINAL.md](./REQUEUE_FIX_FINAL.md) - Final implementation
- [REQUEUE_ISSUES_ANALYSIS.md](./REQUEUE_ISSUES_ANALYSIS.md) - Issue analysis
- [REQUEUE_LOGIC_ISSUES_ANALYSIS.md](./REQUEUE_LOGIC_ISSUES_ANALYSIS.md) - Logic debugging

### UI Integration
- [COMPLETE_REQUEUE_AND_UI_FIXES.md](./COMPLETE_REQUEUE_AND_UI_FIXES.md) - Frontend integration
  - Timer fixes
  - Queue button state
  - User acceptance tracking

---

## Architecture

### Key Components

#### 1. **MatchmakerV2** (`matchmaker_v2.py`)
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
- `cleanup_expired_matches` - every 10 seconds
- Handles timeouts and requeueing
- Preserves original queue timestamps

---

## 📊 Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  1. Lobbies Enter Queue (with queued_at timestamp)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Matchmaker Runs (every 10s)                             │
│     - Calculates time_in_queue for each lobby               │
│     - Applies rank-aware tolerance (expands with time)      │
│     - Finds compatible combinations                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Match Proposed (30s acceptance window)                  │
│     - All players notified via WebSocket                    │
│     - Tracks acceptances per lobby                          │
└────────────────────────┬────────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
    ┌──────────────┐         ┌──────────────┐
    │ All Accept   │         │ Some Decline │
    │ (within 30s) │         │ or Timeout   │
    └──────┬───────┘         └──────┬───────┘
           │                        │
           ▼                        ▼
    ┌──────────────┐         ┌──────────────────────────────┐
    │ Match Ready  │         │ Cleanup Task (every 10s)     │
    └──────────────┘         │ - Identifies expired match   │
                             │ - Checks per-lobby acceptance│
                             │ - Requeues lobbies with      │
                             │   100% acceptance            │
                             │ - Preserves queued_at        │
                             └──────────────────────────────┘
```

---

## Key Concepts

### Adaptive Weighting
Balances hidden MMR and display ELO based on convergence state:
- **Converged** (gap < 150): More weight on display ELO
- **Diverging** (gap > 500): More weight on hidden MMR
- **Moderate** (gap 150-500): Balanced weighting

### Time Tolerance
Expands matchmaking range based on wait time:
- **Base Tolerance**: Starting range (varies by MMR tier)
- **Per-Minute Expansion**: Increases tolerance linearly
- **Maximum Cap**: Prevents extremely unbalanced matches

**Example (Elite Tier):**
- 0 minutes: ±750 MMR
- 5 minutes: ±1800 MMR (capped)

### Requeueing Logic
Only requeues lobbies where:
1. Match timed out (30+ seconds)
2. **ALL players in that lobby accepted**
3. At least one other lobby didn't fully accept

This ensures:
- Players who accepted don't get penalized
- Players who declined/AFK don't get rewarded
- Fair treatment for mixed parties

---

## Common Issues

### Issue: Lobbies not requeued after timeout
**Cause**: Missing `match_lobbies` data or incorrect acceptance tracking  
**Fix**: See [CRITICAL_BUG_FOUND_MATCH_LOBBIES.md](./CRITICAL_BUG_FOUND_MATCH_LOBBIES.md)

### Issue: Modal shows incorrect acceptance count
**Cause**: WebSocket broadcast only to accepting lobby  
**Fix**: See [COMPLETE_REQUEUE_AND_UI_FIXES.md](./COMPLETE_REQUEUE_AND_UI_FIXES.md)

### Issue: Time tolerance not expanding
**Cause**: `queued_at` timestamp not preserved or missing  
**Fix**: Verify QueueManager stores `queued_at` on enqueue

---

## Performance

- **Matchmaker**: ~10-50ms per run (depends on queue size)
- **Queue Operations**: O(log N) for Redis sorted set
- **Match Confirmation**: O(1) for Redis hash operations
- **Cleanup**: O(N) where N = active matches (typically 1-5)

---

## Testing

See [../testing/](../testing/) for:
- Bot testing framework
- Acceptance flow tests
- Requeue validation

---

**Last Updated**: October 2025

