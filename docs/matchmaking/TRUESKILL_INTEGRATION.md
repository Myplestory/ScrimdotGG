# TrueSkill Integration Plan

## Current State
- **System**: Using flat ELO (Integer, default 6493)
- **Matchmaking**: Simple ELO averaging and range checking
- **Status**: TrueSkill library installed but not integrated

## Why TrueSkill?
TrueSkill provides better matchmaking than flat ELO because:

1. **Uncertainty Tracking**: New players start with high uncertainty (sigma), preventing premature rank inflation
2. **Team Games**: Designed for team-based games, not 1v1
3. **Faster Convergence**: Player skill estimates stabilize faster with fewer games
4. **Probabilistic**: Uses Bayesian inference instead of linear point changes

## Implementation Plan (Phase 4+)

### 1. Database Migration
Add TrueSkill fields to `Player` model:

```python
class Player(models.Model):
    # Existing fields
    elo = models.IntegerField(default=6493)  # Keep for display/legacy
    
    # TrueSkill fields (NEW)
    mu = models.FloatField(default=25.0)      # Skill estimate (mean)
    sigma = models.FloatField(default=8.333)  # Uncertainty (std dev)
    
    @property
    def trueskill_rating(self):
        """Conservative skill estimate for matchmaking (mu - 3*sigma)"""
        return self.mu - (3 * self.sigma)
    
    @property
    def display_rating(self):
        """User-facing rating (scale mu to 0-10000 range)"""
        return int((self.mu / 50.0) * 10000)
```

### 2. Matchmaking Integration

Update `matchmaker.py` to use TrueSkill ratings:

```python
# In _check_elo_compatibility()
trueskill_ratings = [
    lobby['average_mu'] - (3 * lobby['average_sigma'])
    for lobby in lobbies
]
min_rating = min(trueskill_ratings)
max_rating = max(trueskill_ratings)
rating_range = max_rating - min_rating
```

### 3. Post-Match Rating Updates

Update `match_execution.py` to call TrueSkill after match completion:

```python
from matchmaking.trueskill_manager import TrueSkillManager

async def handle_match_completion(match_id, winner_team):
    # ... existing code ...
    
    # Update TrueSkill ratings
    await TrueSkillManager.update_ratings(
        team_a_players=match.team_a_data['players'],
        team_b_players=match.team_b_data['players'],
        winner='team_a' if winner_team == 'a' else 'team_b'
    )
```

### 4. Create TrueSkillManager

Create `server/matchmaking/trueskill_manager.py`:

```python
import trueskill
from django.apps import apps
from asgiref.sync import sync_to_async

# Configure TrueSkill environment
# draw_probability=0 for Valorant (no draws)
env = trueskill.TrueSkill(
    mu=25.0,
    sigma=8.333,
    beta=4.166,
    tau=0.083,
    draw_probability=0
)

class TrueSkillManager:
    @staticmethod
    async def update_ratings(team_a_players, team_b_players, winner):
        """Update TrueSkill ratings after match"""
        Player = apps.get_model('scrimgg', 'Player')
        
        def update_db():
            # Fetch players
            team_a = [Player.objects.get(puuid=p['puuid']) for p in team_a_players]
            team_b = [Player.objects.get(puuid=p['puuid']) for p in team_b_players]
            
            # Convert to TrueSkill Rating objects
            team_a_ratings = {p: env.create_rating(p.mu, p.sigma) for p in team_a}
            team_b_ratings = {p: env.create_rating(p.mu, p.sigma) for p in team_b}
            
            # Calculate new ratings
            if winner == 'team_a':
                ranks = [0, 1]  # team_a won
            else:
                ranks = [1, 0]  # team_b won
            
            new_ratings = env.rate(
                [list(team_a_ratings.values()), list(team_b_ratings.values())],
                ranks=ranks
            )
            
            # Update database
            for player, new_rating in zip(team_a + team_b, new_ratings[0] + new_ratings[1]):
                player.mu = new_rating.mu
                player.sigma = new_rating.sigma
                player.elo = int((new_rating.mu / 50.0) * 10000)  # Update display ELO
                player.save(update_fields=['mu', 'sigma', 'elo'])
        
        await sync_to_async(update_db)()
```

## Migration Strategy

1. **Phase 3 (Current)**: Use flat ELO, get match execution working
2. **Phase 4**: Add TrueSkill fields via migration, dual-track both systems
3. **Phase 5**: Switch matchmaking to TrueSkill, keep ELO for display
4. **Phase 6**: Deprecate flat ELO updates, TrueSkill only

## References
- TrueSkill Paper: https://www.microsoft.com/en-us/research/publication/trueskill-2-improved-bayesian-skill-rating-system/
- Python Library: https://trueskill.org/
- Existing Code: `server/matchmaking/matchmaking.py` (legacy)

## Notes
- TrueSkill is already in `Pipfile`
- Legacy `matchmaking.py` has example code (unused)
- Current system works fine for initial launch
- TrueSkill adds ~15% more accuracy but 3x complexity

