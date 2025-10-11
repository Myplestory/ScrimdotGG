# Production Deployment Guide - AWS & Google Cloud

## 🌍 Redis in Development vs Production

### Development (Your Current Setup)
```
┌─────────────────────────────────────┐
│  Your Computer                      │
│  ┌────────────┐   ┌──────────────┐  │
│  │  Django    │ → │ Redis (Docker)│  │
│  │  Server    │   │ localhost:6379│  │
│  └────────────┘   └──────────────┘  │
└─────────────────────────────────────┘
```

### Production (AWS/GCloud)
```
┌───────────────────────────────────────────────────┐
│  Cloud Provider (AWS/GCloud)                      │
│                                                   │
│  ┌────────────────┐         ┌─────────────────┐  │
│  │  Django Server │────────▶│  Redis Service  │  │
│  │  (EC2/Compute) │         │  (Managed)      │  │
│  │  Port 8000     │         │  Private IP     │  │
│  └────────────────┘         └─────────────────┘  │
│         │                                         │
│         │ (Public Internet)                       │
└─────────┼─────────────────────────────────────────┘
          │
          ▼
    ┌──────────┐
    │  Users   │
    │  Clients │
    └──────────┘
```

---

## 🎯 Key Concept: Just Change the Connection String!

**The beauty of your code:** It's already production-ready! You just need to update one setting:

### Development:
```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",  # localhost
    }
}
```

### Production:
```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://your-redis-server.amazonaws.com:6379/1",  # Cloud Redis
    }
}
```

**That's it!** Your QueueManager, Matchmaker, and all code stays the same.

---

## ☁️ AWS Deployment

### Option 1: AWS ElastiCache (Recommended)

**What it is:** Managed Redis service (no setup, auto-scaling, backups)

**Setup:**

1. **Create ElastiCache Cluster**
   ```bash
   # AWS Console: ElastiCache → Redis → Create Cluster
   - Engine: Redis
   - Node type: cache.t3.micro (free tier eligible)
   - Number of replicas: 0 (for dev), 1-2 (for production)
   ```

2. **Get Connection Endpoint**
   ```
   Example: scrimgg-redis.abc123.0001.use1.cache.amazonaws.com:6379
   ```

3. **Update Django Settings**
   ```python
   CACHES = {
       "default": {
           "BACKEND": "django_redis.cache.RedisCache",
           "LOCATION": "redis://scrimgg-redis.abc123.0001.use1.cache.amazonaws.com:6379/1",
       }
   }
   
   CELERY_BROKER_URL = 'redis://scrimgg-redis.abc123.0001.use1.cache.amazonaws.com:6379/0'
   ```

4. **Security Groups**
   - Allow inbound traffic on port 6379 from your Django server's security group
   - Keep Redis in private subnet (not public internet)

**Cost:** ~$13/month for cache.t3.micro (or free tier for 12 months)

---

### Option 2: Redis on EC2 (Self-Managed)

**What it is:** Install Redis on a separate EC2 instance

**Setup:**

1. **Launch EC2 Instance**
   ```bash
   # Ubuntu 22.04, t3.micro
   ssh ubuntu@your-ec2-ip
   
   # Install Redis
   sudo apt update
   sudo apt install redis-server -y
   
   # Configure for external connections
   sudo nano /etc/redis/redis.conf
   # Change: bind 127.0.0.1 ::1
   # To: bind 0.0.0.0
   
   # Restart Redis
   sudo systemctl restart redis-server
   ```

2. **Update Django Settings**
   ```python
   LOCATION = "redis://your-redis-ec2-ip:6379/1"
   ```

**Cost:** ~$8/month for t3.micro

---

## ☁️ Google Cloud Deployment

### Option 1: Google Cloud Memorystore (Recommended)

**What it is:** Managed Redis service (equivalent to ElastiCache)

**Setup:**

1. **Create Memorystore Instance**
   ```bash
   # GCloud Console: Memorystore → Redis → Create Instance
   - Instance ID: scrimgg-redis
   - Tier: Basic (for dev), Standard (for production)
   - Capacity: 1 GB
   - Region: Same as your Django server
   ```

2. **Get Connection String**
   ```
   Example: 10.0.0.3:6379 (private IP)
   ```

3. **Update Django Settings**
   ```python
   CACHES = {
       "default": {
           "BACKEND": "django_redis.cache.RedisCache",
           "LOCATION": "redis://10.0.0.3:6379/1",
       }
   }
   ```

**Cost:** ~$35/month for 1GB Basic tier

---

### Option 2: Redis on Compute Engine

Similar to EC2 option above, but on GCP Compute Engine.

---

## 🔐 Production Best Practices

### 1. Use Environment Variables

**Don't hardcode Redis URLs!**

```python
# settings.py
import os

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.environ.get('REDIS_PASSWORD', None),  # Add password in prod
        }
    }
}

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
```

**Set environment variables:**
```bash
# On server
export REDIS_URL="redis://your-production-redis:6379/1"
export REDIS_PASSWORD="your-secure-password"
```

---

### 2. Enable Redis Authentication

**In production, always use passwords!**

**For AWS ElastiCache:**
- Enable "Auth token" when creating cluster
- Update Django settings with password

**For self-managed Redis:**
```bash
# On Redis server
sudo nano /etc/redis/redis.conf

# Uncomment and set:
requirepass your-secure-password-here

# Restart Redis
sudo systemctl restart redis-server
```

**Django settings:**
```python
LOCATION = "redis://:your-password@your-redis-host:6379/1"
#           └─ password goes here (note the colon)
```

---

### 3. Network Security

**AWS:**
```
Django Server (EC2)     Redis (ElastiCache)
Security Group A   →    Security Group B
                        (Allow 6379 from SG-A only)
```

**GCloud:**
```
Django Server (Compute)     Redis (Memorystore)
VPC Network            →    Same VPC
                           (Firewall: Allow 6379 from Django subnet)
```

**Never expose Redis to public internet!**

---

### 4. High Availability Setup (Production)

**For serious production:**

```python
# AWS ElastiCache with read replicas
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": [
            "redis://master.scrimgg.cache.amazonaws.com:6379/1",
            "redis://replica1.scrimgg.cache.amazonaws.com:6379/1",
            "redis://replica2.scrimgg.cache.amazonaws.com:6379/1",
        ],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.environ.get('REDIS_PASSWORD'),
            "MASTER_CACHE": "redis://master.scrimgg.cache.amazonaws.com:6379/1",
        }
    }
}
```

---

## 📋 Deployment Checklist

### For AWS:

1. **Create VPC** (if not exists)
2. **Launch EC2 for Django** (Ubuntu 22.04, t3.small+)
3. **Create ElastiCache Redis** (cache.t3.micro+)
4. **Configure Security Groups**
   - Django SG: Allow 8000 (HTTP), 22 (SSH)
   - Redis SG: Allow 6379 from Django SG only
5. **Set Environment Variables** on EC2
6. **Deploy Django app**
7. **Test connection** from EC2 to Redis

### For Google Cloud:

1. **Create VPC** (if not exists)
2. **Launch Compute Engine** (Ubuntu 22.04, e2-small+)
3. **Create Memorystore Redis**
4. **Configure Firewall Rules**
   - Django: Allow 8000, 22
   - Redis: Allow 6379 from Django subnet only
5. **Set Environment Variables** on Compute
6. **Deploy Django app**
7. **Test connection** from Compute to Memorystore

---

## 💰 Cost Estimates (Monthly)

### AWS:
| Component | Type | Cost |
|-----------|------|------|
| Django Server | t3.small | $15 |
| Redis | cache.t3.micro | $13 |
| Load Balancer (optional) | ALB | $16 |
| **Total** | | **~$45/month** |

### Google Cloud:
| Component | Type | Cost |
|-----------|------|------|
| Django Server | e2-small | $13 |
| Redis | Memorystore Basic 1GB | $35 |
| **Total** | | **~$48/month** |

**Note:** Costs scale with usage. Free tier available for 12 months on both platforms.

---

## 🚀 Quick Start for Production Later

**Don't worry about production now!** Here's what you'll do when ready:

1. **Keep developing locally** with Docker Redis
2. **Code is already production-ready** (no changes needed)
3. **When deploying:**
   - Create managed Redis (ElastiCache/Memorystore)
   - Get connection URL
   - Set environment variable: `REDIS_URL=redis://...`
   - Deploy Django
   - Done!

---

## 🎯 For Now (Development)

**Just do this:**

```powershell
# 1. Install Docker Desktop (if needed)
# Download from: https://www.docker.com/products/docker-desktop/

# 2. Run Redis
docker run -d --name redis-scrimgg -p 6379:6379 --restart unless-stopped redis:alpine

# 3. Test it
docker exec -it redis-scrimgg redis-cli ping

# 4. Test Django connection
cd server
python test_redis.py
```

**Then we continue with Phase 2!** ✅

---

## 💡 Summary

- ✅ **Local Dev:** Docker container on your machine
- ✅ **Production:** Managed Redis service in the cloud
- ✅ **Same Code:** Just change connection URL
- ✅ **Directories:** Don't matter - network connection!
- ✅ **Your Code:** Already production-ready!

---

---

## 🚀 Complete Production Setup (Including Celery)

### Development Setup (Current)

```powershell
# 1. Install Docker Desktop (if needed)
# Download from: https://www.docker.com/products/docker-desktop/

# 2. Run Redis
docker run -d --name redis-scrimgg -p 6379:6379 --restart unless-stopped redis:alpine

# 3. Test Redis connection
docker exec -it redis-scrimgg redis-cli ping

# 4. Start all services
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

### Production Setup (AWS/GCloud)

#### 1. **Deploy Django Server**
```bash
# On your EC2/Compute Engine instance
cd /path/to/your/scrimgg/server

# Install dependencies
pipenv install

# Run migrations
pipenv run python manage.py migrate

# Collect static files
pipenv run python manage.py collectstatic --noinput

# Set environment variables
export REDIS_URL="redis://your-production-redis:6379/1"
export CELERY_BROKER_URL="redis://your-production-redis:6379/0"
export DJANGO_SETTINGS_MODULE="scrimgg.settings"
```

#### 2. **Start Services with Systemd (Production)**

**Django Server Service:**
```bash
# Create /etc/systemd/system/scrimgg-django.service
[Unit]
Description=Scrim.GG Django Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/scrimgg/server
Environment=PATH=/home/ubuntu/.local/share/virtualenvs/server-gol--VEJ/bin
Environment=REDIS_URL=redis://your-production-redis:6379/1
Environment=CELERY_BROKER_URL=redis://your-production-redis:6379/0
ExecStart=/home/ubuntu/.local/share/virtualenvs/server-gol--VEJ/bin/python manage.py runserver 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service:**
```bash
# Create /etc/systemd/system/scrimgg-celery-worker.service
[Unit]
Description=Scrim.GG Celery Worker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/scrimgg/server
Environment=PATH=/home/ubuntu/.local/share/virtualenvs/server-gol--VEJ/bin
Environment=REDIS_URL=redis://your-production-redis:6379/1
Environment=CELERY_BROKER_URL=redis://your-production-redis:6379/0
ExecStart=/home/ubuntu/.local/share/virtualenvs/server-gol--VEJ/bin/celery -A scrimgg worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Beat Service:**
```bash
# Create /etc/systemd/system/scrimgg-celery-beat.service
[Unit]
Description=Scrim.GG Celery Beat Scheduler
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/scrimgg/server
Environment=PATH=/home/ubuntu/.local/share/virtualenvs/server-gol--VEJ/bin
Environment=REDIS_URL=redis://your-production-redis:6379/1
Environment=CELERY_BROKER_URL=redis://your-production-redis:6379/0
ExecStart=/home/ubuntu/.local/share/virtualenvs/server-gol--VEJ/bin/celery -A scrimgg beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start Services:**
```bash
# Enable and start all services
sudo systemctl enable scrimgg-django.service
sudo systemctl enable scrimgg-celery-worker.service
sudo systemctl enable scrimgg-celery-beat.service

sudo systemctl start scrimgg-django.service
sudo systemctl start scrimgg-celery-worker.service
sudo systemctl start scrimgg-celery-beat.service

# Check status
sudo systemctl status scrimgg-django.service
sudo systemctl status scrimgg-celery-worker.service
sudo systemctl status scrimgg-celery-beat.service
```

#### 3. **Production Environment Variables**

Create `/home/ubuntu/scrimgg/server/.env`:
```bash
# Production Environment Variables
REDIS_URL=redis://your-production-redis:6379/1
CELERY_BROKER_URL=redis://your-production-redis:6379/0
REDIS_PASSWORD=your-secure-redis-password

# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,your-server-ip

# Database (if using PostgreSQL in production)
DATABASE_URL=postgresql://user:password@your-db-host:5432/scrimgg_db
```

#### 4. **Production Checklist**

**Before Going Live:**
- [ ] Redis connection tested
- [ ] Celery worker running and processing tasks
- [ ] Celery beat scheduling periodic tasks
- [ ] Django server accessible on port 8000
- [ ] WebSocket connections working
- [ ] Matchmaking queue operational
- [ ] Health check endpoint responding
- [ ] Logs being written correctly
- [ ] SSL certificate configured (if using domain)
- [ ] Firewall rules configured
- [ ] Monitoring/alerting setup

**Service Management Commands:**
```bash
# Check service status
sudo systemctl status scrimgg-django.service
sudo systemctl status scrimgg-celery-worker.service
sudo systemctl status scrimgg-celery-beat.service

# Restart services
sudo systemctl restart scrimgg-django.service
sudo systemctl restart scrimgg-celery-worker.service
sudo systemctl restart scrimgg-celery-beat.service

# View logs
sudo journalctl -u scrimgg-django.service -f
sudo journalctl -u scrimgg-celery-worker.service -f
sudo journalctl -u scrimgg-celery-beat.service -f

# Stop services
sudo systemctl stop scrimgg-django.service
sudo systemctl stop scrimgg-celery-worker.service
sudo systemctl stop scrimgg-celery-beat.service
```

---

## 🎯 For Now (Development)

**Just do this:**

```powershell
# 1. Install Docker Desktop (if needed)
# Download from: https://www.docker.com/products/docker-desktop/

# 2. Run Redis
docker run -d --name redis-scrimgg -p 6379:6379 --restart unless-stopped redis:alpine

# 3. Test it
docker exec -it redis-scrimgg redis-cli ping

# 4. Test Django connection
cd server
python test_redis.py
```

**Then start all services:**

```powershell
cd server

# Terminal 1: Django Server
pipenv run python manage.py runserver

# Terminal 2: Celery Worker  
pipenv run celery -A scrimgg worker --loglevel=info

# Terminal 3: Celery Beat (Periodic Tasks)
pipenv run celery -A scrimgg beat --loglevel=info
```

**Then we continue with Phase 2!** ✅

---

## 💡 Summary

- ✅ **Local Dev:** Docker Redis + 3 terminals for services
- ✅ **Production:** Managed Redis + systemd services
- ✅ **Same Code:** Just change connection URLs
- ✅ **Directories:** Run commands from `/server` directory
- ✅ **Your Code:** Already production-ready!

---

**Ready to install Docker Redis and continue Phase 2?** The commands are above! 🐳
