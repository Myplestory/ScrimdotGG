# MMR/ELO System Migration Steps

## ✅ Completed
- Updated Player model with MMR, TrueSkill, and activity tracking fields
- Created TrueSkill manager (45-60 game convergence, 1.5x decay)
- Created adaptive weighting system (60/40 → 75/25 → 85/15)
- Created MatchmakerV2 with MMR-based matching
- Updated queue manager to apply uncertainty decay
- Updated Celery tasks to use new matchmaker
- Updated frontend rank display (rankprog.jsx)

---

## 📋 Next Steps

### Step 1: Apply Database Migrations

Since you've already run `makemigrations`, now apply them:

```powershell
# From project root
pipenv run python server/manage.py migrate
```

This will add the new fields to your database:
- `mmr` (Float, default 4350.0)
- `trueskill_mu` (Float, default 25.0)
- `trueskill_sigma` (Float, default 9.0)
- `last_game_timestamp` (Float, default 0.0)
- `games_played` (Integer, default 0)
- `is_in_placement` (Boolean, default True)
- `is_settled` (Boolean, default False)

**Note**: Existing players will get default values, which need to be migrated.

---

### Step 2: Migrate Existing Players

Run the migration script to update existing players:

```powershell
# From project root
pipenv run python server/testing/migrate_existing_players.py
```

This will:
1. Keep their current Display ELO
2. Estimate MMR from their ELO
3. Set TrueSkill components
4. Mark them as settled (σ = 2.5)
5. Set games_played = 50

**Your player (evisc#erate, ELO 6400)**:
```
Before:
└─ ELO: 6400

After:
├─ Display ELO: 6400 (unchanged)
├─ Estimated MMR: 6080 (6400 × 0.95)
├─ TrueSkill: μ=34.94, σ=2.5
└─ Games: 50, Settled: True
```

---

### Step 3: Update Bot Test Scripts

Update `test_queue_with_bots.py` to use new defaults:

```python
# In create_bot_player function:
bot.elo = 2750 + random.randint(-50, 50)  # C+ rank
bot.mmr = 4350 + random.randint(-50, 50)  # Similar MMR
bot.trueskill_mu = mmr_to_trueskill_mu(bot.mmr)
bot.trueskill_sigma = 9.0  # New player uncertainty
```

---

### Step 4: Test the System

Run the MMR system test:

```powershell
pipenv run python server/testing/test_mmr_system.py
```

Then test matchmaking with bots:

```powershell
# Terminal 1: Redis (if not running)
docker start redis

# Terminal 2: Daphne
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application

# Terminal 3: Celery Worker
pipenv run celery -A scrimgg worker --loglevel=info --pool=gevent

# Terminal 4: Celery Beat
pipenv run celery -A scrimgg beat --loglevel=info

# Terminal 5: Run bot test
pipenv run python server/testing/test_queue_with_bots.py
```

---

### Step 5: Verify Matchmaking

Check that:
1. ✅ Bots are created with correct MMR/ELO defaults
2. ✅ Lobbies serialize MMR data correctly
3. ✅ Matchmaker uses adaptive weighting
4. ✅ Tolerance system works (rank-aware)
5. ✅ Matches are balanced using team ratings
6. ✅ Your client joins queue and matches with bots

---

### Step 6: Monitor and Tune

After initial testing:

1. **Check match quality**:
   - Are teams balanced?
   - Are queue times acceptable?
   - Is convergence happening smoothly?

2. **Adjust parameters if needed**:
   ```python
   # In trueskill_manager.py
   sigma = 9.0  # Increase for faster convergence
   tau = 0.083  # Increase for faster adaptation
   ```

3. **Monitor logs**:
   - Look for adaptive weighting states
   - Check tolerance calculations
   - Verify MMR-based matching

---

## Configuration Summary

### New Player Defaults
```
Display ELO: 2750 (C+ rank)
Hidden MMR: 4350 (~48th percentile)
TrueSkill: μ=25.0, σ=9.0
Gap: 1600 ELO (buffer zone)
```

### Adaptive Weighting
```
Early (gap >1000):  60% MMR, 40% Display
Mid (gap 500-1000): 75% MMR, 25% Display
Converged (gap <500): 85% MMR, 15% Display
```

### Rank-Aware Tolerance
```
Elite: ±750 base, +210/min, ±1800 max (5 min)
High: ±550 base, +150/min, ±1500 max (6 min)
Mid: ±450 base, +125/min, ±1300 max (7 min)
Low: ±400 base, +125/min, ±1200 max (6 min)
Entry: ±500 base, +150/min, ±1400 max (6 min)
```

### Uncertainty Decay
```
< 14 days: No decay
14-60 days: Linear 1.0x → 1.5x
60+ days: 1.5x max
```

---

## Troubleshooting

### PowerShell '&&' Error
Use semicolons or separate commands:
```powershell
cd server
pipenv run python manage.py migrate
```

### Import Errors
Make sure you're in the virtual environment:
```powershell
pipenv shell
python manage.py migrate
```

### Migration Conflicts
If migrations conflict:
```powershell
pipenv run python server/manage.py migrate --fake scrimgg zero
pipenv run python server/manage.py migrate scrimgg
```

---

## Files Modified

### Backend
- ✅ `server/scrimgg/models.py` - Added MMR/TrueSkill fields
- ✅ `server/matchmaking/trueskill_manager.py` - New file
- ✅ `server/matchmaking/adaptive_weighting.py` - New file
- ✅ `server/matchmaking/matchmaker_v2.py` - New file
- ✅ `server/matchmaking/queue_manager.py` - Added uncertainty decay
- ✅ `server/matchmaking/lobby_manager.py` - Serialize MMR data
- ✅ `server/matchmaking/tasks.py` - Use MatchmakerV2

### Frontend
- ✅ `client/frontend/src/utils/rankprog.jsx` - Added comments

### Testing
- ✅ `server/testing/test_mmr_system.py` - New test suite
- ✅ `server/testing/migrate_existing_players.py` - New migration script

### Documentation
- ✅ `server/docs/MMR_ELO_SYSTEM.md` - Complete system docs
- ✅ `server/MIGRATION_STEPS.md` - This file

---

**You're ready to complete the migration! Run the commands above in order.** 🚀

