# MMR/ELO System (Concise)

## Summary
Hybrid system uses hidden MMR (TrueSkill-based) for matchmaking and display ELO for user-facing rank. We approximate conservative skill as `mu - k*sigma` and map `mu` to MMR/ELO for presentation. Adaptive weighting blends hidden MMR and display ELO based on convergence. Rank-aware tolerance expands matchmaking ranges over time with tier caps.

## Current Implementation
- Hidden MMR/TrueSkill: server/matchmaking/trueskill_manager.py
- Adaptive weighting: server/matchmaking/adaptive_weighting.py
- Tolerance and queue orchestration: server/matchmaking/matchmaking.py, server/matchmaking/tasks.py
- Display ELO presentation: client/frontend/src/utils/rankprog.jsx

## Key Details
- TrueSkill params (typical): `mu ≈ 25.0`, `sigma ≈ 9.0` on new players.
- Conservative rating used for matching: `R_conservative = mu - k*sigma` (we use `k = 2.5–3.0`).
- Mapping to hidden MMR: linear scale of `mu` to an internal MMR range used by the matchmaker.
- Mapping to display ELO: stable scale of `mu` to player-facing ELO; display intentionally lags toward hidden MMR.
- Adaptive weighting (blend of averages when comparing lobbies):
  - Early (unsettled): emphasize hidden MMR (handles smurfs/new players).
  - Mid: balanced.
  - Converged: emphasize display ELO slightly for rank coherence.
- Rank-aware tolerance by tier expands linearly with wait time and caps per tier to keep quality reasonable.

## Team Rating & Constraints
- Team rating approximation:
  - `team_rating = (avg_hidden_mmr × w_mmr) + (avg_display_elo × w_display)`
  - Weights selected from the convergence state (see adaptive weighting above).
- Hard bounds enforced when forming matches (team and individual diffs, maximum imbalance thresholds).

## Known Limitations
- Parameter tuning (sigma/tau, tolerance caps) is empirical and may evolve.
- No separate solo/party MMR yet.

## Next Steps
- Monitor convergence and adjust weights.
- Add role/party-aware adjustments if needed.

