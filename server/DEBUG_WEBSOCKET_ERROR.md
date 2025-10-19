# 🔍 Debugging WebSocket HTTP 500 Error

## The Issue

You're seeing: `❌ WebSocket error: server rejected WebSocket connection: HTTP 500`

This means Django encountered an error when trying to handle the WebSocket connection.

## Most Likely Cause

The new apps haven't been migrated to the database yet, OR there's an import error.

## Quick Fix - Try These Steps:

### Step 1: Run Migrations First
```bash
cd server
pipenv shell
python manage.py makemigrations
python manage.py migrate
```

### Step 2: Check Django Configuration
```bash
pipenv run python manage.py check
```

### Step 3: Look at the Error Logs

Django should have logged the actual error. Check:
```bash
# In Django terminal where runserver is running, look for the error
# OR check the logs
tail -100 logs/errors.log
```

### Step 4: Test Django Directly First
```bash
pipenv run python manage.py runserver
```

Then visit: `http://localhost:8000/admin/`

If admin works, the issue is WebSocket-specific.
If admin doesn't work, it's a Django configuration issue.

## Common Issues & Solutions

### Issue 1: Migrations Not Run
**Symptom:** HTTP 500, error about tables not existing

**Fix:**
```bash
pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
```

### Issue 2: Import Error in New Apps
**Symptom:** HTTP 500, error about importing modules

**Fix:** Check if all new apps have proper `__init__.py` files:
- `core/__init__.py` ✅
- `match_system/__init__.py` ✅
- `match_execution/__init__.py` ✅
- `realtime/__init__.py` ✅

### Issue 3: Missing Dependencies
**Symptom:** ModuleNotFoundError

**Fix:**
```bash
pipenv install django channels channels-redis django-redis celery
```

### Issue 4: ASGI Import Error
**Symptom:** Error importing from realtime.routing

**Fix:** Check `server/scrimgg/asgi.py` line 24:
```python
from realtime.routing import websocket_urlpatterns
```

Should be importing from `realtime`, not `matchmaking`.

## Debug Commands

Run these to diagnose:

```bash
cd server
pipenv shell

# 1. Check Django can import new apps
python -c "import core; import match_system; import realtime; print('✅ Imports OK')"

# 2. Check migrations
python manage.py showmigrations

# 3. Check for errors
python manage.py check --deploy

# 4. Test WebSocket routing
python -c "from realtime.routing import websocket_urlpatterns; print(f'✅ {len(websocket_urlpatterns)} routes')"
```

## Get the Actual Error

The HTTP 500 means there's a Python exception. To see it:

1. **In the Django terminal** (where `runserver` is running), scroll up to see the full traceback
2. **Or check logs:** `tail -100 logs/errors.log`
3. **Or run with verbose logging:**
   ```bash
   pipenv run python manage.py runserver --verbosity 3
   ```

Then try connecting WebSocket again and watch the output.

## Most Likely Solution

Based on the error, you probably just need to:

```bash
cd server
pipenv shell
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Then try the WebSocket test again.

## If Still Broken

Share the error from Django terminal or logs, and I can help debug further!

The error will look something like:
```
Traceback (most recent call last):
  File "...", line X, in ...
    ...
ImportError: No module named 'XXX'
```

That will tell us exactly what's wrong.

