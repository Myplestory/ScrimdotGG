# MMR/ELO System Documentation

## Overview

The Scrim.GG matchmaking system uses a **dual rating system** combining:
- **Display ELO**: Visible ranking (current ladder 0-7500+)
- **Hidden MMR**: Matchmaking rating (approved distribution with TrueSkill)

This provides accurate skill-based matchmaking while maintaining a stable, understandable display rank.

---

## System Components

### 1. Display ELO (Visible Ranking)

**Purpose**: Visual rank representation for players

**Current Ladder**:
```
S:   7500+      (Top tier)
G:   6250-7499  
A+:  5500-6249  
A:   5000-5499  
A-:  4500-4999  
B+:  4000-4499  
B:   3500-3999  
B-:  3000-3499  
C+:  2500-2999  (Starting: 2750)
C:   2000-2499  
C-:  1500-1999  
D+:  1000-1499  
D:   500-999    
D-:  0-499      
```

**Starting Value**: 2750 (C+ rank)

**Update Method**: Based on MMR-ELO gap with multipliers
- Large gap (500+): 3x speed
- Medium gap (300-500): 2.5x speed
- Small gap (150-300): 2x speed
- Aligned (<150): 1x speed

---

### 2. Hidden MMR (Matchmaking Rating)

**Purpose**: Accurate skill measurement for matchmaking

**MMR Distribution** (Target percentiles):
```
S:   8500+      (Top 0.1%)
G:   7500-8499  (Top 1%)
A+:  6750-7499  (Top 3%)
A:   6250-6749  (Top 6%)
A-:  5750-6249  (Top 10%) ✅
B+:  5250-5749  (Top 20%)
B:   4900-5249  (Top 35%)
B-:  4250-4899  (Top 50%) ✅ Half Marker
C+:  3750-4249  (Top 65%, Median Zone)
C:   3250-3749  (Top 78%)
C-:  2750-3249  (Top 88%)
D+:  2250-2749  (Top 94%)
D:   1750-2249  (Top 98%)
D-:  0-1749     (Bottom 2%)
```

**Starting Value**: 4350.0 (~48th percentile, B-/C+ border)

**Update Method**: TrueSkill algorithm with 45-60 game convergence

---

### 3. TrueSkill Components

**Configuration** (45-60 game convergence):
```python
mu (skill): 25.0 (default, maps to 4350 MMR)
sigma (uncertainty): 9.0 (settles in 45-60 games)
beta (variance): 4.5
tau (adaptation): 0.083
```

**Convergence**:
- Settled: σ < 3.0 (45-60 games)
- Highly Confident: σ < 2.0 (70+ games)

**Scaling**:
- mu 25.0 = MMR 4350
- Scaling factor: 174 (4350 / 25)

---

## Adaptive Weighting System

### Purpose
Balance MMR (true skill) and Display ELO (perception) based on convergence state.

### Weighting Stages

**Early Convergence** (gap > 1000, games 1-20):
```
Weights: 60% MMR, 40% Display
Handles: Smurfs, bought accounts, new players
```

**Mid Convergence** (gap 500-1000, games 20-45):
```
Weights: 75% MMR, 25% Display
Handles: Climbing/falling players, partial convergence
```

**Converged** (gap < 500, games 45+):
```
Weights: 85% MMR, 15% Display
Handles: Settled players, highest game quality
```

### Team Rating Calculation

```python
team_rating = (avg_mmr × mmr_weight) + (avg_display × display_weight)
```

### Examples

**Smurf (early, gap 2400)**:
```
Display ELO: 2800, MMR: 5200
Team Rating = (5200 × 0.60) + (2800 × 0.40) = 4240
Matches at B-/C+ level (protected from low ranks)
```

**Settled Player (gap 200)**:
```
Display ELO: 5200, MMR: 5400
Team Rating = (5400 × 0.85) + (5200 × 0.15) = 5370
Matches at true skill (mostly MMR-based)
```

---

## Rank-Aware Tolerance System

### Configuration by MMR Tier

**Elite** (MMR 6750+):
```
Base: ±750
Growth: +210/min
Max: ±1800 (5 min to cap)
```

**High** (MMR 5750-6749):
```
Base: ±550
Growth: +150/min
Max: ±1500 (6 min to cap)
```

**Mid** (MMR 4250-5749):
```
Base: ±450
Growth: +125/min
Max: ±1300 (7 min to cap)
```

**Low** (MMR 2750-4249):
```
Base: ±400
Growth: +125/min
Max: ±1200 (6 min to cap)
```

**Entry** (MMR 0-2749):
```
Base: ±500
Growth: +150/min
Max: ±1400 (6 min to cap)
```

### Purpose
- Elite ranks: Wider tolerance (small player pool)
- Entry ranks: Wider tolerance (retention critical)
- Mid ranks: Balanced tolerance (large player pool)

---

## Uncertainty Decay (Returning Players)

### Configuration
```
No decay: < 14 days (2 weeks)
Linear scaling: 14-60 days
Max decay: 1.5x at 60+ days (2 months)
```

### Formula
```python
if days < 14:
    multiplier = 1.0
elif days >= 60:
    multiplier = 1.5
else:
    progress = (days - 14) / (60 - 14)
    multiplier = 1.0 + (0.5 × progress)

new_sigma = current_sigma × multiplier
```

### Examples
- 21 days (3 weeks): 1.08x (light decay)
- 42 days (6 weeks): 1.30x (moderate decay)
- 60 days (2 months): 1.50x (max decay)

---

## Player Journeys

### New Player (Average Skill)
```
Starting:
├─ Display ELO: 2750 (C+)
├─ MMR: 4350 (B-/C+ border)
└─ Gap: 1600 (buffer zone)

After 20 games (50% WR):
├─ Display ELO: ~2700 (C+)
├─ MMR: ~4200 (C+)
├─ Gap: ~1500 (converging slowly)
└─ Convergence: Early/Mid

After 50 games:
├─ Display ELO: ~2750 (C+)
├─ MMR: ~4350 (B-/C+ border)
├─ Gap: ~600 (converged)
└─ Settled: σ < 3.0 ✅
```

### Smurf (Elite Skill)
```
Starting:
├─ Display ELO: 2750 (C+)
├─ MMR: 4350
└─ Gap: 1600

After 10 games (90% WR):
├─ Display ELO: ~3050 (C)
├─ MMR: ~7400 (G rank!)
├─ Gap: ~4350 (huge)
├─ Matches: G rank players
└─ Detected: Fast climb

After 30 games:
├─ Display ELO: ~4900 (A-)
├─ MMR: ~7600 (G rank)
├─ Gap: ~2700
└─ Catching up

After 60 games:
├─ Display ELO: ~6800 (G rank)
├─ MMR: ~7700 (G rank)
├─ Gap: ~900
└─ Nearly converged
```

### Bought Account (Falling)
```
Starts at:
├─ Display ELO: 6500 (A)
├─ MMR: 6500
└─ True skill: C+ (~3800)

After 10 games (30% WR):
├─ Display ELO: ~5700 (B+)
├─ MMR: ~3800 (C+)
├─ Gap: ~1900
└─ Matches: C+/B- players (protected)

After 50 games:
├─ Display ELO: ~3900 (C+)
├─ MMR: ~3700 (C+)
├─ Gap: ~200
└─ Converged at true skill ✅
```

---

## Quality Constraints

Even with adaptive weighting, enforce hard limits:

```python
max_mmr_diff: 800         # Max MMR between teams
max_display_diff: 1200    # Max display ELO between teams
max_team_balance: 400     # Max team A vs B imbalance
max_individual_gap: 2000  # Max gap between any 2 players
```

---

## Database Schema

### Player Model Fields

```python
# Display ELO
elo = IntegerField(default=2750)  # C+ rank

# Hidden MMR
mmr = FloatField(default=4350.0)  # ~48th percentile

# TrueSkill
trueskill_mu = FloatField(default=25.0)
trueskill_sigma = FloatField(default=9.0)

# Activity tracking
last_game_timestamp = FloatField(default=0.0)
games_played = IntegerField(default=0)
is_in_placement = BooleanField(default=True)
is_settled = BooleanField(default=False)
```

---

## Migration Steps

1. **Create migrations**:
   ```bash
   pipenv run python manage.py makemigrations
   ```

2. **Apply migrations**:
   ```bash
   pipenv run python manage.py migrate
   ```

3. **Update existing players** (optional):
   ```python
   # Option 1: Set all to defaults (recommended)
   Player.objects.all().update(
       mmr=4350.0,
       trueskill_mu=25.0,
       trueskill_sigma=9.0,
       is_in_placement=True
   )
   
   # Option 2: Keep existing ELO, estimate MMR
   for player in Player.objects.all():
       player.mmr = player.elo * 0.67  # Rough estimate
       player.trueskill_mu = mmr_to_trueskill_mu(player.mmr)
       player.save()
   ```

---

## Testing

Run the test suite:
```bash
pipenv run python testing/test_mmr_system.py
```

Expected output:
- ✅ Model defaults correct
- ✅ MMR/TrueSkill conversions working
- ✅ Uncertainty decay functioning
- ✅ Adaptive weighting calculating correctly
- ✅ Tolerance system working
- ✅ Match quality validation passing
- ✅ Player journey simulations complete

---

## Next Steps

After migrations complete:

1. **Update existing players** (run migration script)
2. **Test with bots** (update bot creation to use new defaults)
3. **Monitor convergence** (track how fast players settle)
4. **Tune parameters** (adjust sigma/tau if needed)
5. **Implement priority bias** (next phase)

---

## Configuration Files

- **Models**: `server/scrimgg/models.py`
- **TrueSkill**: `server/matchmaking/trueskill_manager.py`
- **Adaptive Weighting**: `server/matchmaking/adaptive_weighting.py`
- **Matchmaker**: `server/matchmaking/matchmaker_v2.py`
- **Queue Manager**: `server/matchmaking/queue_manager.py`
- **Celery Tasks**: `server/matchmaking/tasks.py`
- **Frontend Ranks**: `client/frontend/src/utils/rankprog.jsx`

---

## Performance Notes

- **TrueSkill calculations**: ~1-2ms per match
- **Adaptive weighting**: Negligible (<0.1ms)
- **Tolerance calculations**: Negligible (<0.1ms)
- **Total overhead**: ~2-3ms per matchmaking iteration

**Impact**: Minimal - won't affect matchmaking speed.

---

## Troubleshooting

### Issue: Players not converging
**Solution**: Check sigma values, may need to adjust tau parameter

### Issue: Smurfs detected too slowly
**Solution**: Increase sigma to 10.0 or 11.0 for faster initial swings

### Issue: Ratings too volatile
**Solution**: Decrease sigma to 8.0 or 8.5 for more stability

### Issue: Match quality poor
**Solution**: Review adaptive weighting thresholds, may need stricter constraints

---

## Future Enhancements

- [ ] Separate Solo/Party MMR
- [ ] Role-based matchmaking
- [ ] Region-locked queues
- [ ] Premium queue with stricter tolerances
- [ ] Seasonal MMR resets
- [ ] Leaderboards (Top 500 by MMR)

