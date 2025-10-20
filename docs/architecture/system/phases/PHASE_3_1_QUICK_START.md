# Phase 3.1: Quick Start Guide

## 🚀 Get Started in 3 Steps

### **Step 1: Run Migrations** (2 minutes)

```powershell
cd server
pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
```

### **Step 2: Verify Installation** (1 minute)

```powershell
cd server
pipenv run python manage.py shell
```

```python
from scrimgg.models import Match, MatchStatistics, MatchRejoinToken
print("✅ Match model:", Match._meta.get_field('status'))
print("✅ MatchStatistics exists:", MatchStatistics.objects.count() >= 0)
print("✅ MatchRejoinToken exists:", MatchRejoinToken.objects.count() >= 0)
exit()
```

### **Step 3: Start Services** (Normal operation)

```powershell
# Terminal 1: Redis
docker ps | findstr redis-scrimgg  # Should be running from Phase 2

# Terminal 2: Django Server
cd server
pipenv run python manage.py runserver

# Terminal 3: Celery Worker
cd server
pipenv run celery -A scrimgg worker --loglevel=info

# Terminal 4: Celery Beat
cd server
pipenv run celery -A scrimgg beat --loglevel=info
```

---

## ✅ **That's It!**

Your match execution system is now ready! The complete match flow will work automatically when players accept matches.

### **What Happens Next:**

1. **Players accept match** → Automatic transition to "starting"
2. **Constructor creates custom game** → Other players join automatically  
3. **Match goes live** → Real-time score updates
4. **Match completes** → Results processed automatically

### **Monitor It Working:**

Watch your Django server logs for:
```
[MATCH START] Match {id} starting - Constructor: True/False
[CONSTRUCTOR] Creating custom game...
[JOIN] Joining custom game: {pregame_id}
[MATCH LIVE] Match {id} is now in progress
Match {id} score update: 5-3 (Round 8)
[MATCH COMPLETE] Match completed
```

---

## 📚 **Full Documentation**

- **Complete Guide**: `docs/PHASE_3_1_SETUP_AND_TESTING.md`
- **Implementation Details**: `docs/PHASE_3_1_COMPLETION_SUMMARY.md`
- **Phase 3 Plan**: `docs/PHASE_3_IMPLEMENTATION_PLAN.md`

---

**Phase 3.1 Complete - Happy Matching! 🎮**

