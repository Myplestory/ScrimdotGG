# Phase 3.1: Match Execution System - Setup & Testing

## ✅ Implementation Complete!

Phase 3.1 has been successfully implemented with all core components:

### **What We Built:**
1. ✅ Extended Match model with execution fields
2. ✅ Created MatchStatistics model for player stats
3. ✅ Created MatchRejoinToken model for disconnect handling
4. ✅ Implemented MatchExecutionManager (server-side)
5. ✅ Implemented MatchMonitor for live stats (server-side)
6. ✅ Updated Django consumer with match execution handlers
7. ✅ Updated client bootstrap.py with match flow handlers
8. ✅ Updated clientapi.py with match monitoring methods

---

## 🚀 **Setup Instructions**

### **Step 1: Run Database Migrations**

Navigate to the server directory and run migrations:

```powershell
cd server

# Create migration files
pipenv run python manage.py makemigrations

# Apply migrations
pipenv run python manage.py migrate
```

**Expected Output:**
```
Migrations for 'scrimgg':
  scrimgg/migrations/0XXX_auto_YYYYMMDD_HHMM.py
    - Alter field status on match
    - Add field constructor_puuid to match
    - Add field coregame_id to match
    - Add field current_round to match
    - Add field team_a_score to match
    - Add field team_b_score to match
    - Add field team_a_data to match
    - Add field team_b_data to match
    - ... (more fields)
    - Create model MatchStatistics
    - Create model MatchRejoinToken

Running migrations:
  Applying scrimgg.0XXX_auto_YYYYMMDD_HHMM... OK
```

### **Step 2: Verify Migrations**

Check that the models were created correctly:

```powershell
cd server
pipenv run python manage.py shell
```

```python
from scrimgg.models import Match, MatchStatistics, MatchRejoinToken

# Check Match model fields
match = Match.objects.first()
print(match.status)  # Should work
print(match.team_a_score)  # Should work

# Check new models exist
print(MatchStatistics.objects.count())
print(MatchRejoinToken.objects.count())

exit()
```

---

## 🧪 **Testing Instructions**

### **Test 1: Basic Match Flow (Manual)**

This test verifies the complete match execution flow.

**Prerequisites:**
- Redis running
- Django server running
- Celery worker running
- Celery beat running
- 2+ clients connected

**Steps:**

1. **Create test match data:**
```powershell
cd server
pipenv run python manage.py shell
```

```python
from scrimgg.models import Match, Player
from django.utils import timezone
import uuid

# Create test players
players = []
for i in range(10):
    player, created = Player.objects.get_or_create(
        puuid=f"test-player-{i}",
        defaults={
            'username': f"TestPlayer{i}",
            'alias': f"Player{i}",
            'region': 'na',
            'elo': 1500 + (i * 10),
            'rank': 'S',
            'team': 'none'
        }
    )
    players.append(player)

# Create test match
match = Match.objects.create(
    status='confirmed',
    selected_map='Haven',
    game_server='Virginia',
    team_a_data={
        'captain': {
            'puuid': players[0].puuid,
            'alias': players[0].alias,
            'elo': players[0].elo
        },
        'players': [
            {'puuid': p.puuid, 'alias': p.alias, 'elo': p.elo}
            for p in players[:5]
        ]
    },
    team_b_data={
        'captain': {
            'puuid': players[5].puuid,
            'alias': players[5].alias,
            'elo': players[5].elo
        },
        'players': [
            {'puuid': p.puuid, 'alias': p.alias, 'elo': p.elo}
            for p in players[5:]
        ]
    }
)

print(f"Created test match: {match.id}")
print(f"Constructor should be: {players[0].puuid}")
exit()
```

2. **Trigger match start:**
```python
cd server
pipenv run python manage.py shell
```

```python
import asyncio
from matchmaking.match_execution import MatchExecutionManager
from scrimgg.models import Match

# Get the test match
match = Match.objects.last()
print(f"Match ID: {match.id}")

# Trigger match start
result = asyncio.run(MatchExecutionManager.initiate_match_start(str(match.id)))
print(result)

# Verify status changed
match.refresh_from_db()
print(f"Status: {match.status}")  # Should be 'starting'
print(f"Constructor: {match.constructor_puuid}")  # Should be test-player-0

exit()
```

### **Test 2: Score Update Test**

Test the match monitoring and score update functionality:

```python
cd server
pipenv run python manage.py shell
```

```python
import asyncio
from match_system.monitor import MatchMonitor
from scrimgg.models import Match

# Get test match
match = Match.objects.last()
match.status = 'in_progress'
match.coregame_id = 'test-coregame-123'
match.save()

# Test score update
result = asyncio.run(MatchMonitor.update_match_score(
    str(match.id), 5, 3, 8
))

print(result)  # Should show {'status': 'success', 'changed': True}

# Verify scores
match.refresh_from_db()
print(f"Team A: {match.team_a_score}")  # Should be 5
print(f"Team B: {match.team_b_score}")  # Should be 3
print(f"Round: {match.current_round}")  # Should be 8

exit()
```

### **Test 3: Statistics Collection Test**

Test player statistics tracking:

```python
cd server
pipenv run python manage.py shell
```

```python
import asyncio
from match_system.monitor import MatchMonitor
from scrimgg.models import Match, MatchStatistics

# Get test match
match = Match.objects.last()

# Create test player stats
player_stats = {
    'test-player-0': {
        'team': 'team_a',
        'kills': 15,
        'deaths': 8,
        'assists': 5,
        'headshots': 8,
        'bodyshots': 7,
        'legshots': 0,
        'damage_dealt': 2400,
        'damage_received': 1600
    },
    'test-player-1': {
        'team': 'team_a',
        'kills': 12,
        'deaths': 10,
        'assists': 7,
        'headshots': 5,
        'bodyshots': 7,
        'legshots': 0,
        'damage_dealt': 2100,
        'damage_received': 1800
    }
}

# Update stats
result = asyncio.run(MatchMonitor.update_player_statistics(
    str(match.id), player_stats
))

print(result)

# Verify stats created
stats = MatchStatistics.objects.filter(match=match)
for stat in stats:
    print(f"{stat.player.alias}: {stat.kills}/{stat.deaths}/{stat.assists} - ADR: {stat.adr:.1f}")

exit()
```

### **Test 4: Rejoin Token Test**

Test disconnect/rejoin functionality:

```python
cd server
pipenv run python manage.py shell
```

```python
import asyncio
from matchmaking.match_execution import MatchExecutionManager
from scrimgg.models import Match

# Get test match
match = Match.objects.last()
match.status = 'in_progress'
match.save()

# Generate rejoin token
token = asyncio.run(MatchExecutionManager.generate_rejoin_token(
    str(match.id), 'test-player-0'
))

print(f"Rejoin token: {token}")

# Validate token
validation = asyncio.run(MatchExecutionManager.validate_rejoin_token(token))
print(validation)
# Should show: {'valid': True, 'match_id': '...', 'player_puuid': 'test-player-0', 'pregame_id': '...'}

# Try to use token again (should fail)
validation2 = asyncio.run(MatchExecutionManager.validate_rejoin_token(token))
print(validation2)
# Should show: {'valid': False, 'reason': 'Invalid token'} (already used)

exit()
```

---

## 📊 **Performance Verification**

### **Check Heartbeat Behavior**

Verify that heartbeat stops during matches:

1. Start client with one player
2. Watch logs for "[HEARTBEAT] Starting..." messages (every 3 seconds)
3. Trigger match start for that player
4. Heartbeat should stop with "[HEARTBEAT] Stopping..."
5. After match ends, heartbeat should restart

### **Check Match Monitoring Performance**

Verify 30-second polling interval:

1. Constructor creates custom game
2. Match monitoring starts
3. Check logs - should see score updates every ~30 seconds, not 3 seconds
4. Verify CPU usage remains < 0.5% during monitoring

---

## 🐛 **Common Issues & Solutions**

### **Issue 1: Migration Fails**

**Error:** `django.db.utils.OperationalError: no such column`

**Solution:**
```powershell
cd server
pipenv run python manage.py migrate --fake-initial
```

### **Issue 2: Import Errors**

**Error:** `ModuleNotFoundError: No module named 'matchmaking.match_execution'`

**Solution:**
- Verify files exist in `server/matchmaking/`
- Restart Django server
- Clear Python cache: `find . -type d -name __pycache__ -exec rm -r {} +`

### **Issue 3: WebSocket Events Not Received**

**Error:** Client doesn't receive `match_starting` event

**Solution:**
- Verify player PUUID matches the one in match data
- Check Django server logs for broadcast messages
- Verify client is connected to WebSocket
- Check channel layer is working: Redis should be running

### **Issue 4: Constructor Not Creating Game**

**Error:** Constructor handler not triggered

**Solution:**
- Verify `is_constructor` flag is True in event payload
- Check bootstrap.py event routing includes `'match_starting'`
- Verify ValClient is authenticated
- Check Valorant game is running

---

## ✅ **Verification Checklist**

Before proceeding to Phase 3.2, verify:

- [ ] Migrations applied successfully
- [ ] Match model has new fields (`status`, `team_a_score`, etc.)
- [ ] MatchStatistics model created
- [ ] MatchRejoinToken model created
- [ ] Can create test match and trigger match start
- [ ] Score updates work correctly
- [ ] Statistics collection works
- [ ] Rejoin tokens can be generated and validated
- [ ] Django consumer routes match execution events
- [ ] Client bootstrap.py handles match events
- [ ] Match monitoring polls every 30 seconds (not 3)
- [ ] Heartbeat stops during matches

---

## 🚀 **Next Steps**

Once all tests pass:

1. **Phase 3.2: Real-Time Match Monitoring**
   - Celery tasks for automated monitoring
   - WebSocket broadcasting optimization
   - Spectator functionality

2. **Phase 3.3: Match Room Frontend**
   - React component for live match viewing
   - Real-time scoreboard
   - Player statistics display
   - Spectator chat

3. **Phase 3.4: Post-Match Processing**
   - ELO calculation and updates
   - Match history storage
   - Player achievements
   - Performance metrics

---

## 📝 **Documentation References**

- **Implementation Plan**: `docs/PHASE_3_IMPLEMENTATION_PLAN.md`
- **Development Setup**: `docs/DEVELOPMENT_SETUP.md`
- **Production Deployment**: `docs/PRODUCTION_DEPLOYMENT.md`

---

**Phase 3.1 is complete and ready for testing!** 🎉

