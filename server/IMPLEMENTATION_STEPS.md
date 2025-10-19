# Final Implementation Steps - Ready to Test

## 🎯 Your refactor is complete and ready for testing!

All code has been created. Follow these steps to implement and test.

---

## Step 1: Update Configuration Files (5 minutes)

### 1.1: Update `settings.py`

Open `server/scrimgg/settings.py` and add new apps to `INSTALLED_APPS`:

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
    
    # ADD THESE NEW APPS (before existing apps):
    'core',              # NEW
    'match_system',      # NEW
    'match_execution',   # NEW
    'realtime',          # NEW
    
    # Existing apps:
    'scrimgg',
    'riotlogin',
    'users',
    'lobby',
    'maps',
    'match',
    'matchmaking',
]
```

### 1.2: Update `asgi.py`

Open `server/scrimgg/asgi.py` and update the import:

```python
# OLD:
from matchmaking.routing import websocket_urlpatterns

# NEW:
from realtime.routing import websocket_urlpatterns
```

### 1.3: Update `celery.py` (Optional - for now tasks still work from matchmaking)

The Celery tasks will continue to work from matchmaking for now. We're using import wrappers to maintain compatibility.

---

## Step 2: Verify Configuration (2 minutes)

Run the verification script:

```bash
cd server
python VERIFY_REFACTOR.py
```

**Expected output:**
```
✅ core is in INSTALLED_APPS
✅ match_system is in INSTALLED_APPS
✅ match_execution is in INSTALLED_APPS
✅ realtime is in INSTALLED_APPS
...
Results: 7/7 checks passed
✨ All checks passed! Ready for testing.
```

**If you see errors:**
- Check that you added apps to INSTALLED_APPS correctly
- Check that you updated asgi.py import
- Read the error messages for specific fixes

---

## Step 3: Create and Run Migrations (3 minutes)

```bash
cd server

# Create migrations for new apps
python manage.py makemigrations core
python manage.py makemigrations match_system
python manage.py makemigrations match_execution
python manage.py makemigrations realtime

# Run migrations
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  Applying match_system.0001_initial... OK
  ...
```

---

## Step 4: Run End-to-End Tests (2 minutes)

```bash
python TEST_REFACTOR.py
```

**Expected output:**
```
✅ Imports: PASSED
✅ Redis Connection: PASSED
✅ WebSocket Routing: PASSED
✅ Model Operations: PASSED
✅ Handler Initialization: PASSED
✅ Celery Tasks: PASSED

Results: 6/6 tests passed
✨ All tests passed! Refactor is working correctly.
```

---

## Step 5: Start Services and Test (5 minutes)

### 5.1: Start Django

```bash
# Terminal 1
cd server
python manage.py runserver
```

Check for startup errors. You should see:
```
Starting development server at http://127.0.0.1:8000/
```

### 5.2: Start Celery Worker

```bash
# Terminal 2
cd server
celery -A scrimgg worker --loglevel=info --pool=solo
```

Check for startup errors. You should see tasks registered.

### 5.3: Start Celery Beat

```bash
# Terminal 3
cd server
celery -A scrimgg beat --loglevel=info
```

### 5.4: Test WebSocket Connection

```bash
# Terminal 4
cd server/testing
python test_websocket_connection.py
```

**Expected:**
```
WebSocket connection established
```

### 5.5: Test Full Matchmaking Flow

```bash
cd server/testing
python test_queue_with_bots_v5.py
```

Watch the bots queue, match, accept, veto, and complete the flow.

---

## Step 6: Verify Everything Works (5 minutes)

### Check Admin Panel

Visit: `http://localhost:8000/admin/`

You should see new sections:
- **Core** (may be empty)
- **Match System** (with Match, MatchPlayer, VetoAction models)
- **Match Execution**
- **Realtime**

### Check Celery Tasks

In the Celery Beat terminal, you should see:
```
Scheduler: Sending due task periodic-matchmaking
Scheduler: Sending due task check-veto-timeouts
Scheduler: Sending due task cleanup-expired-matches
```

### Check Logs

```bash
tail -f server/logs/matchmaking.log
tail -f server/logs/errors.log
```

Look for any errors or warnings.

---

## Troubleshooting

### Issue: "No module named 'core'"

**Fix:** Add `'core'` to INSTALLED_APPS in settings.py

### Issue: "No module named 'realtime.routing'"

**Fix:** Update asgi.py to import from `realtime.routing` instead of `matchmaking.routing`

### Issue: "Table doesn't exist"

**Fix:** Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Issue: WebSocket won't connect

**Fix:** 
1. Check asgi.py has correct import
2. Restart Django server
3. Check for errors in Django terminal

### Issue: Celery tasks not running

**Fix:**
1. Restart Celery worker and beat
2. Check task names in celery.py match the new module paths
3. For now, matchmaking tasks still work from matchmaking module

---

## What Changed vs. Before

### Client Code: NO CHANGES ✅

Your client code continues to work exactly as before:
- Same WebSocket URL: `ws://server/ws/matchmaking/{puuid}/`
- Same event names
- Same message format

### Server Code: Better Organized ✅

- **Matchmaking app:** Now only handles queue and matchmaking algorithm
- **Match System app:** Handles post-acceptance match flow (veto, confirmation)
- **Match Execution app:** Handles live game management
- **Realtime app:** Handles WebSocket communication (split into handlers)
- **Core app:** Shared utilities (Redis, WebSocket broadcasting)

### Benefits

1. ✅ Code is organized by domain
2. ✅ Easier to find and fix bugs
3. ✅ Easier to test
4. ✅ Ready for future scaling
5. ✅ No client changes needed

---

## Success Criteria

You'll know it's working when:

- [x] Django starts without errors
- [x] Celery worker starts without errors
- [x] WebSocket test connects successfully
- [x] Admin panel shows new apps
- [x] Bot test completes full matchmaking flow
- [x] No errors in logs

---

## Next Steps After Successful Testing

1. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Refactor: Split matchmaking into focused apps"
   ```

2. **Deploy to staging** (if you have one)

3. **Monitor for issues**

4. **Gradually migrate code** from matchmaking to new apps
   - The manager wrappers allow gradual migration
   - No rush - everything works as-is

5. **Clean up old files** (ONLY after thorough testing)
   ```bash
   # Don't do this yet!
   # rm server/matchmaking/consumers.py
   # rm server/matchmaking/match_manager.py
   # etc.
   ```

---

## Getting Help

If you encounter issues:

1. Check the error message carefully
2. Look in `server/logs/errors.log`
3. Run `python VERIFY_REFACTOR.py` again
4. Check the troubleshooting section above
5. Review `MIGRATION_GUIDE.md` for detailed explanations

---

## Current Status

✅ All code created
✅ All imports wrapped for compatibility  
✅ Verification scripts ready
✅ Test scripts ready
✅ Documentation complete

**Ready to implement!** Start with Step 1 above.

---

## Time Estimate

- Configuration: 5 minutes
- Verification: 2 minutes
- Migrations: 3 minutes
- Testing: 7 minutes
- **Total: ~15-20 minutes**

Good luck! 🚀

