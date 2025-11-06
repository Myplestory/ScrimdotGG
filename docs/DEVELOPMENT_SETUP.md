# Development Setup Guide

## 🚀 Quick Start (Development)

### Prerequisites
- Docker Desktop installed and running
- Python 3.12+ with pipenv

### 1. Start Redis
```powershell
# Run Redis container
docker run -d --name redis-scrimgg -p 6379:6379 --restart unless-stopped redis:alpine

# Test Redis connection
docker exec -it redis-scrimgg redis-cli ping
# Should return: PONG
```

### 2. Start All Services

**Important:** All commands must be run from the `server` directory!

```powershell
# Navigate to server directory
cd server

# Terminal 1: Django Server
pipenv run python manage.py runserver

# Terminal 2: Celery Worker
pipenv run celery -A scrimgg worker --loglevel=info

# Terminal 3: Celery Beat (Periodic Tasks)
pipenv run celery -A scrimgg beat --loglevel=info

# Terminal 4: Optional - Celery Monitoring
pipenv run celery -A scrimgg flower
```

### 3. Test Everything Works

```powershell
cd server

# Test Redis connection
pipenv run python test_redis.py

# Test queue operations
pipenv run python test_simple_queue.py

# Test Celery tasks
pipenv run python test_celery_complete.py
```

---

## 🔧 Common Issues

### Issue: "celery is not recognized"
**Problem:** Running Celery from wrong directory or virtual environment not activated.

**Solution:**
```powershell
# Make sure you're in the server directory
cd server

# Use pipenv to run celery
pipenv run celery -A scrimgg worker --loglevel=info
```

### Issue: "Redis connection failed"
**Problem:** Redis container not running or wrong port.

**Solution:**
```powershell
# Check if Redis container is running
docker ps

# If not running, start it
docker run -d --name redis-scrimgg -p 6379:6379 --restart unless-stopped redis:alpine

# Test connection
docker exec -it redis-scrimgg redis-cli ping
```

### Issue: "No module named django"
**Problem:** Virtual environment not activated or dependencies not installed.

**Solution:**
```powershell
cd server
pipenv install
pipenv run python manage.py runserver
```

---

## 📋 Service Status Check

### Check if services are running:

```powershell
# Check Redis container
docker ps | findstr redis-scrimgg

# Check Django server (should show "Starting development server")
# Look for: "Starting development server at http://127.0.0.1:8000/"

# Check Celery worker (should show "ready")
# Look for: "celery@hostname ready."

# Check Celery beat (should show "beat: Starting...")
# Look for: "beat: Starting..."
```

### Test WebSocket connection:
- Open browser to `http://localhost:8000`
- Check browser console for WebSocket connection errors
- Test lobby creation and queue operations

---

## 🎯 What Each Service Does

### Django Server (`runserver`)
- Handles HTTP requests
- WebSocket connections for real-time updates
- Database operations
- REST API endpoints

### Celery Worker (`celery worker`)
- Processes background tasks
- Handles matchmaking algorithm
- Processes match confirmations
- Handles cleanup operations

### Celery Beat (`celery beat`)
- Schedules periodic tasks
- Runs matchmaking every 30 seconds
- Runs cleanup every 60 seconds
- Runs queue maintenance every 5 minutes

### Redis Container
- Stores matchmaking queue
- Stores match confirmation data
- Celery task broker
- Django cache backend

---

## 🚀 Production vs Development

### Development (Current Setup)
- **3 Terminal Windows** running different services
- **Docker Redis** container on localhost
- **Debug mode** enabled
- **Console logging** for all services

### Production (Future)
- **systemd services** for automatic startup
- **Managed Redis** service in cloud
- **Production logging** to files
- **Process monitoring** and auto-restart

---

## 📝 Quick Commands Reference

```powershell
# Start Redis
docker run -d --name redis-scrimgg -p 6379:6379 --restart unless-stopped redis:alpine

# Test Redis
docker exec -it redis-scrimgg redis-cli ping

# Start Django (Terminal 1)
cd server && pipenv run python manage.py runserver

# Start Celery Worker (Terminal 2)
cd server && pipenv run celery -A scrimgg worker --loglevel=info

# Start Celery Beat (Terminal 3)
cd server && pipenv run celery -A scrimgg beat --loglevel=info

# Test everything
cd server && pipenv run python test_redis.py
```

**Remember:** Always run commands from the `server` directory! 🎯
