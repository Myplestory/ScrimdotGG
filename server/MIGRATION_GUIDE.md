# Complete Migration Guide - Matchmaking App Refactor

## Overview
This guide walks you through refactoring the monolithic `matchmaking` app into multiple focused apps following Strategy 1: Split into Multiple Focused Apps.

## Pre-Migration Checklist

- [ ] Backup your database: `python manage.py dumpdata > backup.json`
- [ ] Create git branch: `git checkout -b refactor/split-matchmaking-apps`
- [ ] Commit all current changes
- [ ] Ensure all tests pass
- [ ] Stop all running services (Django, Celery, Celery Beat)

## Phase 1: Add New Apps to INSTALLED_APPS

### Step 1.1: Update settings.py

Edit `server/scrimgg/settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    
    # ADD THESE NEW APPS IN THIS ORDER:
    'core',              # NEW: Shared utilities
    'match_system',      # NEW: Post-acceptance match flow
    'match_execution',   # NEW: Live game management  
    'realtime',          # NEW: WebSocket layer
    
    # KEEP EXISTING:
    'matchmaking',       # Will be refactored to queue + matchmaker only
    'lobby',             # Will be enhanced
]
```

### Step 1.2: Create initial migrations

```bash
cd server
python manage.py makemigrations core
python manage.py makemigrations match_system
python manage.py makemigrations match_execution
python manage.py makemigrations realtime
```

### Step 1.3: Run migrations

```bash
python manage.py migrate core
python manage.py migrate match_system
python manage.py migrate match_execution
python manage.py migrate realtime
```

**Expected result:** New apps are registered, no data migration yet.

---

## Phase 2: Move Models (Data Migration)

### Step 2.1: Understand the model migration

Models being moved:
- `matchmaking.models_match.Match` → `match_system.models.Match`
- `matchmaking.models_match.MatchPlayer` → `match_system.models.MatchPlayer`
- `matchmaking.models_match.VetoAction` → `match_system.models.VetoAction`

### Step 2.2: Update database table names

The new models use different table names to avoid conflicts:
- `matchmaking_match` → `match_system_match`
- `matchmaking_match_player` → `match_system_match_player`
- `matchmaking_veto_action` → `match_system_veto_action`

### Step 2.3: Migrate data (if you have existing matches)

**Option A: Fresh start (no existing match data)**
```bash
# Simply delete old tables if they're empty
python manage.py dbshell
> DROP TABLE IF EXISTS matchmaking_match;
> DROP TABLE IF EXISTS matchmaking_match_player;
> DROP TABLE IF EXISTS matchmaking_veto_action;
> EXIT;
```

**Option B: Migrate existing data**
```bash
# Create a data migration script
python manage.py makemigrations --empty match_system --name migrate_existing_matches
```

Then edit the migration file:
```python
# match_system/migrations/XXXX_migrate_existing_matches.py
from django.db import migrations

def migrate_matches(apps, schema_editor):
    # Copy data from old tables to new tables
    db_alias = schema_editor.connection.alias
    cursor = schema_editor.connection.cursor()
    
    # Copy Match data
    cursor.execute("""
        INSERT INTO match_system_match 
        SELECT * FROM matchmaking_match;
    """)
    
    # Copy MatchPlayer data
    cursor.execute("""
        INSERT INTO match_system_match_player 
        SELECT * FROM matchmaking_match_player;
    """)
    
    # Copy VetoAction data
    cursor.execute("""
        INSERT INTO match_system_veto_action 
        SELECT * FROM matchmaking_veto_action;
    """)

def reverse_migrate(apps, schema_editor):
    # Reverse migration if needed
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('match_system', 'PREVIOUS_MIGRATION'),
    ]
    
    operations = [
        migrations.RunPython(migrate_matches, reverse_migrate),
    ]
```

Run the migration:
```bash
python manage.py migrate match_system
```

---

## Phase 3: Update Import Statements

### Step 3.1: Create import mapping

Old imports → New imports:

```python
# Models
matchmaking.models_match → match_system.models

# Managers
matchmaking.match_manager → match_system.managers
matchmaking.match_confirmation → match_system.managers
matchmaking.lobby_manager → lobby.manager
matchmaking.match_execution → match_execution.execution_manager
matchmaking.match_monitor → match_execution.monitor

# Validators
matchmaking.match_state_validator → core.validators

# WebSocket
matchmaking.consumers → realtime.consumers
matchmaking.routing → realtime.routing
```

### Step 3.2: Update all import statements

Run find-and-replace across the codebase:

```bash
# Find all files importing from matchmaking
grep -r "from matchmaking" server/ --include="*.py"

# Examples of replacements needed:
# from matchmaking.models_match import Match
# → from match_system.models import Match

# from matchmaking.match_manager import MatchManager  
# → from match_system.managers import MatchManager

# from matchmaking.consumers import PugSocketConsumer
# → from realtime.consumers import RealtimeConsumer
```

**Critical files to update:**
1. `matchmaking/tasks.py` - Update model imports
2. `client/backend/pugapi.py` - WebSocket URL (optional, see Phase 4)
3. `scrimgg/asgi.py` - WebSocket routing
4. Any test files

### Step 3.3: Update Celery task imports

Edit files that import Celery tasks:

```python
# OLD:
from matchmaking.tasks import check_veto_timeouts

# NEW:
from match_system.tasks import check_veto_timeouts
```

---

## Phase 4: Update WebSocket Configuration

### Step 4.1: Update ASGI routing

Edit `server/scrimgg/asgi.py`:

```python
# OLD:
from matchmaking.routing import websocket_urlpatterns

# NEW:
from realtime.routing import websocket_urlpatterns
```

### Step 4.2: Client WebSocket URL (backward compatible)

The new routing supports both old and new URLs:
- Old: `ws://server/ws/matchmaking/{puuid}/` ✅ Still works!
- New: `ws://server/ws/realtime/{puuid}/` ✅ Alternative

**No client changes required!** The old URL still works.

---

## Phase 5: Update Celery Configuration

### Step 5.1: Update settings.py Celery config

Edit `server/scrimgg/settings.py`:

```python
# Updated task routing
CELERY_TASK_ROUTES = {
    'matchmaking.tasks.periodic_matchmaking': {'queue': 'matchmaking'},
    'matchmaking.tasks.cleanup_expired_queues': {'queue': 'cleanup'},
    'match_system.tasks.cleanup_expired_matches': {'queue': 'cleanup'},  # NEW
    'match_system.tasks.check_veto_timeouts': {'queue': 'match_system'},  # NEW
}
```

### Step 5.2: Update Celery Beat schedule

Edit `server/scrimgg/celery.py`:

```python
app.conf.beat_schedule = {
    'periodic-matchmaking': {
        'task': 'matchmaking.tasks.periodic_matchmaking',
        'schedule': 10.0,
    },
    'cleanup-expired-matches': {
        'task': 'match_system.tasks.cleanup_expired_matches',  # UPDATED
        'schedule': 10.0,
    },
    'cleanup-expired-queues': {
        'task': 'matchmaking.tasks.cleanup_expired_queues',
        'schedule': 300.0,
    },
    'check-veto-timeouts': {
        'task': 'match_system.tasks.check_veto_timeouts',  # UPDATED
        'schedule': 3.0,
    },
}
```

---

## Phase 6: Refactor Matchmaking App

### Step 6.1: Clean up matchmaking app

Files to MOVE or DELETE from `matchmaking/`:

**Move these files:**
- `models_match.py` → Already in `match_system/models.py` (delete old)
- `match_manager.py` → `match_system/managers/match_manager.py`
- `match_confirmation.py` → `match_system/managers/confirmation_manager.py`
- `match_execution.py` → `match_execution/execution_manager.py`
- `match_monitor.py` → `match_execution/monitor.py`
- `lobby_manager.py` → `lobby/manager.py`
- `consumers.py` → Split into `realtime/handlers/`
- `routing.py` → `realtime/routing.py`

**Keep in matchmaking/**
- `queue_manager.py` ✅
- `matchmaker_v2.py` ✅
- `trueskill_manager.py` ✅
- `adaptive_weighting.py` ✅
- `models.py` (if it imports from models_match, update imports)

### Step 6.2: Update matchmaking/tasks.py

Remove tasks that were moved:

```python
# DELETE from matchmaking/tasks.py:
# - cleanup_expired_matches → Now in match_system/tasks.py
# - check_veto_timeouts → Now in match_system/tasks.py
# - notify_match_* helpers → Now use core.websocket_utils

# KEEP in matchmaking/tasks.py:
# - periodic_matchmaking
# - cleanup_expired_queues
# - manual_matchmaking
```

---

## Phase 7: Testing

### Step 7.1: Run all migrations

```bash
python manage.py migrate
python manage.py makemigrations --check --dry-run
```

Expected: No pending migrations.

### Step 7.2: Start services

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery worker
celery -A scrimgg worker --loglevel=info

# Terminal 3: Celery Beat
celery -A scrimgg beat --loglevel=info
```

### Step 7.3: Test WebSocket connection

```bash
cd server/testing
python test_websocket_connection.py
```

Expected: Connection successful, events routing correctly.

### Step 7.4: Test matchmaking flow

```bash
python testing/test_queue_with_bots_v5.py
```

Expected: Full flow works (queue → match → veto → game).

### Step 7.5: Check Celery tasks

```bash
# In Django shell
python manage.py shell
>>> from match_system.tasks import check_veto_timeouts
>>> check_veto_timeouts.delay()
```

Expected: Task runs without errors.

---

## Phase 8: Cleanup

### Step 8.1: Delete old files

Once everything works:

```bash
cd server/matchmaking
rm models_match.py
rm match_manager.py
rm match_confirmation.py
rm match_execution.py
rm match_monitor.py
rm lobby_manager.py
rm consumers.py
rm routing.py
```

### Step 8.2: Update matchmaking __init__.py

```python
# matchmaking/__init__.py
"""
Matchmaking - Queue management and matchmaker algorithm only.
Post-acceptance flow moved to match_system app.
"""
```

---

## Rollback Procedure

If something goes wrong:

```bash
# 1. Restore database
python manage.py flush
python manage.py loaddata backup.json

# 2. Checkout previous commit
git checkout main

# 3. Restart services
```

---

## Verification Checklist

After migration, verify:

- [ ] Django starts without errors
- [ ] Celery worker starts without errors
- [ ] Celery Beat tasks are scheduled
- [ ] WebSocket connections work
- [ ] Lobby creation works
- [ ] Queue operations work
- [ ] Matchmaking creates matches
- [ ] Match confirmation works
- [ ] Veto system works
- [ ] Side selection works
- [ ] No import errors in logs
- [ ] Admin panel shows new apps
- [ ] All database migrations applied

---

## Benefits After Migration

✅ **Cleaner code organization** - Each app has a single purpose
✅ **Easier testing** - Test apps in isolation
✅ **Better scalability** - Can deploy as microservices later
✅ **Improved maintainability** - Easier to find and fix bugs
✅ **Team collaboration** - Multiple devs can work on different apps
✅ **Backward compatible** - No client changes required

---

## Support

If you encounter issues:
1. Check logs: `server/logs/matchmaking.log`, `server/logs/errors.log`
2. Verify imports: `python manage.py check`
3. Check migrations: `python manage.py showmigrations`
4. Review this guide's troubleshooting section

## Common Issues

### Issue: Import errors
**Solution:** Update all import statements as per Phase 3

### Issue: Database errors
**Solution:** Ensure migrations ran successfully in correct order

### Issue: WebSocket not connecting
**Solution:** Check `realtime/routing.py` is correctly imported in `asgi.py`

### Issue: Celery tasks not running
**Solution:** Update task names in `celery.py` and `settings.py`

---

## Next Steps

After successful migration:
1. Update documentation
2. Update team on new structure
3. Create new tests for individual apps
4. Consider adding API versioning
5. Plan microservices split (if needed)

## File Structure Summary

```
server/
├── core/                     # ✨ NEW: Shared utilities
│   ├── redis_manager.py
│   ├── websocket_utils.py
│   └── exceptions.py
│
├── match_system/             # ✨ NEW: Post-acceptance match flow
│   ├── models.py             # Match, MatchPlayer, VetoAction
│   ├── managers/
│   │   ├── match_manager.py
│   │   ├── confirmation_manager.py
│   │   └── veto_manager.py
│   └── tasks.py              # Veto timeouts, cleanup
│
├── match_execution/          # ✨ NEW: Live game management
│   ├── execution_manager.py
│   └── monitor.py
│
├── realtime/                 # ✨ NEW: WebSocket layer
│   ├── consumers.py          # Main consumer
│   ├── routing.py
│   └── handlers/
│       ├── lobby_handler.py
│       ├── match_handler.py
│       ├── veto_handler.py
│       └── execution_handler.py
│
├── matchmaking/              # 📦 REFACTORED: Queue + Matchmaker only
│   ├── queue_manager.py      # ✅ Keep
│   ├── matchmaker_v2.py      # ✅ Keep
│   ├── trueskill_manager.py  # ✅ Keep
│   └── tasks.py              # ✅ Keep (matchmaking tasks only)
│
└── lobby/                    # 🔧 ENHANCED
    ├── models.py             # ✅ Existing
    └── manager.py            # ✨ NEW: Moved from matchmaking
```

