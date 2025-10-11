# Redis Setup for Windows - Scrim.GG

Complete guide for installing and configuring Redis on Windows for Phase 2 matchmaking.

---

## 🎯 Quick Install (Recommended)

### Option 1: Using WSL2 (Windows Subsystem for Linux) ⭐ BEST

**Prerequisites:**
- Windows 10 version 2004+ or Windows 11
- WSL2 enabled

**Steps:**

1. **Enable WSL2** (if not already enabled)
```powershell
# Run as Administrator
wsl --install
```

2. **Install Ubuntu from Microsoft Store**
   - Open Microsoft Store
   - Search for "Ubuntu"
   - Install Ubuntu 22.04 LTS

3. **Install Redis in Ubuntu**
```bash
# Open Ubuntu terminal
sudo apt update
sudo apt install redis-server -y

# Start Redis
sudo service redis-server start

# Verify it's running
redis-cli ping
# Should return: PONG
```

4. **Make Redis start automatically**
```bash
# Edit sudoers to allow Redis without password
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/service redis-server start" | sudo tee -a /etc/sudoers

# Add to ~/.bashrc
echo "sudo service redis-server start > /dev/null 2>&1" >> ~/.bashrc
```

---

### Option 2: Memurai (Native Windows Redis) 💰

**Memurai is a native Windows port of Redis (free for development)**

1. **Download Memurai**
   - Visit: https://www.memurai.com/get-memurai
   - Download Memurai Developer Edition (FREE)

2. **Install**
   - Run the installer
   - Default settings are fine
   - It will install as a Windows Service

3. **Verify Installation**
```powershell
# Memurai installs its own CLI
memurai-cli ping
# Should return: PONG
```

4. **Configuration** (optional)
   - Config file: `C:\Program Files\Memurai\memurai.conf`
   - Default port: 6379 (same as Redis)

---

### Option 3: Docker 🐳

**If you have Docker Desktop installed**

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop/

2. **Run Redis Container**
```powershell
docker run -d --name redis-scrimgg -p 6379:6379 redis:alpine

# Verify
docker exec -it redis-scrimgg redis-cli ping
# Should return: PONG
```

3. **Auto-start on boot**
```powershell
docker update --restart unless-stopped redis-scrimgg
```

---

## ✅ Verify Redis is Working

### Test Connection

**From PowerShell:**
```powershell
# If using WSL
wsl redis-cli ping

# If using Memurai
memurai-cli ping

# If using Docker
docker exec -it redis-scrimgg redis-cli ping
```

**From Python:**
```python
# Run this in server directory
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(r.ping())"
# Should print: True
```

---

## 🔧 Configure Django to Use Redis

Your `server/scrimgg/settings.py` already has Redis configured:

```python
# Django Cache (Redis)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Celery (Background tasks)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

**For production, uncomment the Redis Channel Layer:**
```python
# In settings.py, replace InMemoryChannelLayer with:
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

---

## 🧪 Test Redis with Scrim.GG

Create a test file: `server/test_redis.py`

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from django.core.cache import cache
from django_redis import get_redis_connection

# Test Django cache
print("Testing Django cache...")
cache.set('test_key', 'Hello Redis!', 30)
value = cache.get('test_key')
print(f"✓ Cache test: {value}")

# Test direct Redis connection
print("\nTesting direct Redis connection...")
redis_conn = get_redis_connection("default")
redis_conn.set('direct_test', 'Direct connection works!')
value = redis_conn.get('direct_test')
print(f"✓ Direct test: {value.decode()}")

# Test Redis operations for matchmaking
print("\nTesting matchmaking queue operations...")
redis_conn.delete('test_queue')  # Clean up
redis_conn.zadd('test_queue', {'lobby1': 1500, 'lobby2': 1600})
queue_size = redis_conn.zcard('test_queue')
print(f"✓ Queue size: {queue_size}")

lobbies = redis_conn.zrange('test_queue', 0, -1, withscores=True)
print(f"✓ Lobbies in queue: {lobbies}")

redis_conn.delete('test_queue')  # Cleanup

print("\n✅ All Redis tests passed!")
```

**Run the test:**
```bash
cd server
python test_redis.py
```

---

## 🚀 Starting Redis for Development

### Daily Workflow

**WSL:**
```bash
# In Ubuntu terminal
sudo service redis-server start
```

**Memurai:**
- No action needed - runs as Windows Service

**Docker:**
```powershell
docker start redis-scrimgg
```

---

## 🔍 Monitoring Redis

### Check if Redis is Running

**WSL:**
```bash
sudo service redis-server status
```

**Memurai:**
```powershell
# Check Windows Services
Get-Service Memurai
```

**Docker:**
```powershell
docker ps | findstr redis
```

### Redis CLI Commands

```bash
# Connect to Redis
redis-cli  # or memurai-cli

# Common commands:
PING                    # Test connection
INFO                    # Server info
KEYS *                  # List all keys (dev only!)
GET key                 # Get value
SET key value           # Set value
DEL key                 # Delete key
FLUSHALL                # Clear all data (careful!)
```

### Monitor Queue in Real-Time

```bash
redis-cli

# Watch queue operations
MONITOR

# In another terminal, run your matchmaking
# You'll see all Redis operations in real-time
```

---

## 🐛 Troubleshooting

### "Connection refused"

**WSL:**
```bash
sudo service redis-server start
sudo service redis-server status
```

**Memurai:**
```powershell
# Restart service
Restart-Service Memurai
```

**Docker:**
```powershell
docker start redis-scrimgg
docker logs redis-scrimgg
```

### Port 6379 Already in Use

```powershell
# Find what's using port 6379
netstat -ano | findstr :6379

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### Django can't connect to Redis

1. Check Redis is running
2. Verify port 6379 is open
3. Check Windows Firewall
4. Try: `pip install redis django-redis`

### Performance Issues

**WSL:** 
- Make sure you're using WSL2 (not WSL1)
- Check: `wsl --list --verbose`

**Docker:**
- Allocate more memory to Docker Desktop
- Settings → Resources → Memory (4GB+)

---

## 📊 Redis Performance Tips

### Memory Management

```bash
# Check memory usage
redis-cli INFO memory

# Set max memory (optional)
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Persistence

For development, you don't need persistence. For production:

```bash
# Enable persistence (WSL/Docker)
redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

---

## 🎯 Quick Reference

| Task | WSL Command | Memurai | Docker |
|------|------------|---------|--------|
| Start | `sudo service redis-server start` | Auto-starts | `docker start redis-scrimgg` |
| Stop | `sudo service redis-server stop` | `Stop-Service Memurai` | `docker stop redis-scrimgg` |
| Status | `sudo service redis-server status` | `Get-Service Memurai` | `docker ps` |
| CLI | `redis-cli` | `memurai-cli` | `docker exec -it redis-scrimgg redis-cli` |
| Ping | `redis-cli ping` | `memurai-cli ping` | `docker exec -it redis-scrimgg redis-cli ping` |

---

## ✅ Ready for Phase 2?

Once Redis is installed and `redis-cli ping` returns `PONG`, you're ready!

**Next steps:**
1. ✅ Redis installed and running
2. ✅ Python test passes (`python test_redis.py`)
3. 🚀 Proceed with Phase 2 implementation

---

## 💡 Recommendation

For Windows development, I recommend **WSL2 + Redis** because:
- ✅ Most authentic (same as production Linux)
- ✅ Free and well-supported
- ✅ Easy to manage
- ✅ Great performance with WSL2

If you can't use WSL2, **Memurai** is excellent for native Windows.

---

**Need help?** Check Redis logs:
- WSL: `/var/log/redis/redis-server.log`
- Memurai: Event Viewer → Windows Logs → Application
- Docker: `docker logs redis-scrimgg`

