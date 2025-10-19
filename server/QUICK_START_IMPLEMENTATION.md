# Quick Start Implementation Guide

## For the Impatient Developer 🚀

This guide provides the fastest path to implement the refactor. For detailed explanations, see `MIGRATION_GUIDE.md`.

## Prerequisites

```bash
# 1. Backup your database
cd server
python manage.py dumpdata > ../backup_$(date +%Y%m%d_%H%M%S).json

# 2. Create git branch
git checkout -b refactor/split-matchmaking-apps
git add .
git commit -m "Pre-refactor checkpoint"

# 3. Stop all services
# Kill Django server, Celery worker, Celery Beat
```

## Step 1: Add New Apps to INSTALLED_APPS (2 minutes)

Edit `server/scrimgg/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'channels',
    
    # ADD THESE NEW APPS:
    'core',              # NEW
    'match_system',      # NEW
    'match_execution',   # NEW
    'realtime',          # NEW
    
    # EXISTING (keep these):
    'scrimgg',
    'riotlogin',
    'users',
    'lobby',
    'maps',
    'match',
    'matchmaking',
]
```

## Step 2: Run Migrations (1 minute)

```bash
python manage.py makemigrations
python manage.py migrate
```

**Expected output:** 
```
Migrations for 'core':
  ...
Migrations for 'match_system':
  match_system/0001_initial.py
    - Create model Match
    - Create model MatchPlayer
    - Create model VetoAction
...
```

## Step 3: Update ASGI Configuration (1 minute)

Edit `server/scrimgg/asgi.py`:

```python
# OLD:
from matchmaking.routing import websocket_urlpatterns

# NEW:
from realtime.routing import websocket_urlpatterns
```

## Step 4: Update Celery Configuration (2 minutes)

Edit `server/scrimgg/celery.py`:

```python
app.conf.beat_schedule = {
    'periodic-matchmaking': {
        'task': 'matchmaking.tasks.periodic_matchmaking',
        'schedule': 10.0,
    },
    'cleanup-expired-matches': {
        'task': 'match_system.tasks.cleanup_expired_matches',  # CHANGED
        'schedule': 10.0,
    },
    'cleanup-expired-queues': {
        'task': 'matchmaking.tasks.cleanup_expired_queues',
        'schedule': 300.0,
    },
    'check-veto-timeouts': {
        'task': 'match_system.tasks.check_veto_timeouts',  # CHANGED
        'schedule': 3.0,
    },
}
```

Edit `server/scrimgg/settings.py` (Celery task routes):

```python
CELERY_TASK_ROUTES = {
    'matchmaking.tasks.*': {'queue': 'matchmaking'},
    'matchmaking.tasks.periodic_matchmaking': {'queue': 'matchmaking'},
    'matchmaking.tasks.cleanup_expired_queues': {'queue': 'cleanup'},
    'match_system.tasks.*': {'queue': 'match_system'},  # NEW
    'match_system.tasks.cleanup_expired_matches': {'queue': 'cleanup'},  # NEW
}
```

## Step 5: Update Critical Imports (5 minutes)

### 5.1: Update matchmaking/tasks.py

Find and replace in `server/matchmaking/tasks.py`:

```python
# OLD:
from .models_match import Match
from .match_manager import MatchManager
from .match_confirmation import MatchConfirmationManager

# NEW:
from match_system.models import Match
from match_system.managers import MatchManager, MatchConfirmationManager
```

### 5.2: Update any test files

Search for imports:
```bash
grep -r "from matchmaking.models_match" server/ --include="*.py"
grep -r "from matchmaking.match_manager" server/ --include="*.py"
grep -r "from matchmaking.consumers" server/ --include="*.py"
```

Replace with:
```python
from match_system.models import Match, MatchPlayer, VetoAction
from match_system.managers import MatchManager
from realtime.consumers import RealtimeConsumer
```

## Step 6: Handle Existing Match Data (Choose One)

### Option A: No Existing Matches (Development)

```bash
# Just delete old tables if empty
python manage.py dbshell
```

```sql
DROP TABLE IF EXISTS matchmaking_match;
DROP TABLE IF EXISTS matchmaking_match_player;
DROP TABLE IF EXISTS matchmaking_veto_action;
\q
```

### Option B: Migrate Existing Matches (Production)

```bash
# Use the data migration script from MIGRATION_GUIDE.md
# This will copy data from old tables to new tables
```

## Step 7: Clean Up Old Files (2 minutes)

**IMPORTANT:** Only do this AFTER verifying everything works!

```bash
cd server/matchmaking

# Backup first
mkdir ../OLD_MATCHMAKING_BACKUP
cp models_match.py match_manager.py match_confirmation.py ../OLD_MATCHMAKING_BACKUP/
cp match_execution.py match_monitor.py lobby_manager.py ../OLD_MATCHMAKING_BACKUP/
cp consumers.py routing.py ../OLD_MATCHMAKING_BACKUP/

# Then delete (only after testing!)
# rm models_match.py
# rm match_manager.py  
# rm match_confirmation.py
# rm match_execution.py
# rm match_monitor.py
# rm lobby_manager.py
# rm consumers.py
# rm routing.py
```

## Step 8: Test (5 minutes)

### 8.1: Check for errors

```bash
python manage.py check
python manage.py check --deploy
```

Expected: `System check identified no issues.`

### 8.2: Start services

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery worker  
celery -A scrimgg worker --loglevel=info --pool=solo

# Terminal 3: Celery Beat
celery -A scrimgg beat --loglevel=info
```

Check for errors in startup logs.

### 8.3: Test WebSocket connection

```bash
cd testing
python test_websocket_connection.py
```

Expected: `WebSocket connection established`

### 8.4: Test full matchmaking flow

```bash
python test_queue_with_bots_v5.py
```

Expected: Bots queue → match → accept → veto → game

## Step 9: Verify in Admin Panel (2 minutes)

```bash
# Visit http://localhost:8000/admin/
```

Check that you see:
- ✅ Core (new section)
- ✅ Match System (new section with Match, MatchPlayer, VetoAction)
- ✅ Match Execution
- ✅ Realtime

## Step 10: Commit (1 minute)

```bash
git add .
git commit -m "Refactor: Split matchmaking into focused apps

- Created core, match_system, match_execution, realtime apps
- Split 2043-line consumer into organized handlers
- Moved models to match_system
- Updated Celery task distribution
- Maintained 100% backward compatibility"
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'match_system'"

**Solution:** Did you add the apps to INSTALLED_APPS? Run `python manage.py check`

### "django.db.utils.ProgrammingError: relation does not exist"

**Solution:** Did you run migrations? Run `python manage.py migrate`

### "ImportError: cannot import name 'Match'"

**Solution:** Update imports from `matchmaking.models_match` to `match_system.models`

### WebSocket won't connect

**Solution:** Did you update asgi.py? Check the import line.

### Celery tasks not running

**Solution:** Did you update task names in celery.py?

## Rollback (if needed)

```bash
# Restore database
python manage.py flush --no-input
python manage.py loaddata ../backup_YYYYMMDD_HHMMSS.json

# Checkout previous commit
git checkout main
```

## Total Time: ~20 minutes

- Configuration updates: 5 min
- Migrations: 2 min
- Import updates: 5 min
- Testing: 5 min
- Verification: 3 min

## Success Criteria

✅ Django starts without errors  
✅ Celery worker starts without errors  
✅ WebSocket connects successfully  
✅ Admin panel shows new apps  
✅ Full matchmaking flow works  
✅ No import errors in logs  

## Next Steps After Success

1. Read `REFACTOR_SUMMARY.md` for full understanding
2. Update team documentation
3. Clean up old files (after thorough testing)
4. Write tests for new apps
5. Deploy to staging environment

## Need Help?

- **Detailed guide:** See `MIGRATION_GUIDE.md`
- **Architecture overview:** See `REFACTOR_SUMMARY.md`
- **Check logs:** `server/logs/matchmaking.log` and `server/logs/errors.log`

## What's Different for Developers?

### Before (Old Imports)
```python
from matchmaking.models_match import Match
from matchmaking.match_manager import MatchManager
from matchmaking.consumers import PugSocketConsumer
```

### After (New Imports)
```python
from match_system.models import Match
from match_system.managers import MatchManager
from realtime.consumers import RealtimeConsumer
```

### WebSocket Events (No Change!)
```python
# Client code - NO CHANGES NEEDED
await websocket.send(json.dumps({
    "event": "veto_map",
    "payload": {"match_id": "abc", "map": "Bind"}
}))
```

## Pro Tips

1. **Do this on a Friday afternoon** - gives you the weekend if issues arise
2. **Have a rollback plan** - keep the database backup handy
3. **Test incrementally** - verify each step before moving on
4. **Use git** - commit after each successful phase
5. **Check logs constantly** - catch errors early

## That's It! 🎉

You now have a clean, modular Django architecture following best practices, with zero client-side changes required!

