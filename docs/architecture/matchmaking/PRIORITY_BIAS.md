# Priority Bias (Concise)

## Summary
Priority bias reduces wait time for lobbies that accepted recent matches or were negatively impacted by declines/timeouts. It adjusts candidate ordering and tolerance to favor compliant lobbies while preserving quality constraints.

## Signals
- acceptance_count (recent window)
- consecutive_accepts (streak)
- last_decline_age (negative signal)
- time_in_queue (baseline)

## Scoring
We compute a bias score per lobby and add it to the base ranking used by the matchmaker:

```
base_score = f(team_rating, time_in_queue, tolerance)
bias = w1*acceptance_count + w2*consecutive_accepts - w3*recent_decline_penalty
rank_score = base_score + bias
```

- Weights (w1..w3) are small vs. quality terms; they nudge but do not override constraints.
- recent_decline_penalty decays with time (e.g., exponential half-life).

## Application
- Ordering: rank candidate combinations by sum of member lobby rank_scores.
- Tolerance: optionally expand tolerance slightly (within caps) for high-bias lobbies.
- Persistence: store acceptance/decline metadata with match confirmations for accurate attribution.

## Constraints & Safeguards
- Never bypass hard quality limits (team diff, individual gap, max imbalance).
- Bias capped to prevent extreme prioritization.
- Reset/decay bias after successful matches to prevent permanent advantage.

## Implementation Notes
- Storage: Redis or DB fields for per-lobby acceptance/decline counters and timestamps.
- Update points: on match proposal outcome (accept/decline/timeout) and on cleanup.
- Observability: log rank_score components for audit and tuning.
