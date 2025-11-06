# TrueSkill Integration (Concise)

## Summary
TrueSkill provides probabilistic team-based ratings with uncertainty (sigma). We track `(mu, sigma)` per player. For matchmaking, we use a conservative approximation `R_conservative = mu - k*sigma` (k≈2.5–3.0) to avoid overrating high-uncertainty players. Display ELO is derived from `mu` and converges over time.

## Current Implementation
- Storage and helpers: `server/matchmaking/trueskill_manager.py`
- Ratings updated on match completion for both teams (compute new `(mu, sigma)` and persist)
- Display ELO derived from `mu` via linear mapping; uncertainty decays for inactive players to reflect rust

## Matching Usage
- Conservative comparison: `mu - k*sigma` per player; aggregate by lobby averages
- Combine with adaptive weighting of hidden MMR (from TrueSkill) and display ELO when ranking candidates

## Notes
- Draw probability = 0 (Valorant-like)
- Tunables: mu, sigma, beta, tau; target convergence ~45–60 games

## Follow-ups
- Persist acceptance metadata to support priority bias
- Add solo/party separation when implemented

