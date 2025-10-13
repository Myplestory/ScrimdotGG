# Troubleshooting & Debugging

Quick fixes, debugging guides, and solutions for common issues.

---

## Quick Fixes

### **[QUICK_FIX_REFERENCE.md](./QUICK_FIX_REFERENCE.md)** ⭐ **START HERE**
Quick reference guide for common issues and their solutions.

**Covers:**
- Match acceptance issues
- WebSocket connection problems
- Queue stuck issues
- Redis cleanup
- Port conflicts

---

## WebSocket Issues

### Port & Configuration
- **[WEBSOCKET_PORT_REFERENCE.md](./WEBSOCKET_PORT_REFERENCE.md)** - Port configuration
  - Daphne runs on port 8000
  - Bot testing port setup
  - CORS configuration

### Connection Management
- **[WEBSOCKET_CLEANUP_GUIDE.md](./WEBSOCKET_CLEANUP_GUIDE.md)** - Cleanup guide
  - Orphaned connection handling
  - Force-close scripts
  - Connection lifecycle

- **[WEBSOCKET_CLEANUP_COMPLETE.md](./WEBSOCKET_CLEANUP_COMPLETE.md)** - Implementation details
  - Automatic cleanup on script exit
  - Timeout handling
  - Resource management

---

## Deadlock & Performance

### Deadlock Analysis
- **[DEADLOCK_ANALYSIS.md](./DEADLOCK_ANALYSIS.md)** - Root cause analysis
  - Async/sync context issues
  - Event loop problems
  - AsyncToSync errors

- **[DEADLOCK_FIX_COMPLETE.md](./DEADLOCK_FIX_COMPLETE.md)** - Resolution
  - Event loop management
  - Proper async context handling
  - Celery task fixes

---

## Debugging & Logging

### Logging System
- **[LOGGING_ADDED.md](./LOGGING_ADDED.md)** - Enhanced logging
  - Match confirmation logs
  - Queue operation logs
  - WebSocket event logs
  - Cleanup task logs

### Debug Tools
- **[DEBUG_EXPIRATION_ADDED.md](./DEBUG_EXPIRATION_ADDED.md)** - Match expiration debugging
  - Detailed expiration checks
  - Timestamp validation
  - TTL verification

---

## Fix Summaries

- **[FINAL_FIXES_SUMMARY.md](./FINAL_FIXES_SUMMARY.md)** - Comprehensive fix summary
  - All major fixes consolidated
  - Timeline of changes
  - Affected components

---

## Common Problems & Solutions

### Problem: Match not expiring after 30 seconds
**Symptoms:**
- Match stays active past timeout
- Cleanup task reports 0 expired matches

**Solutions:**
1. Check Redis key pattern: should be `match_confirmation:*:data`
2. Verify `initiated_at` field exists (not `created_at`)
3. Review [DEBUG_EXPIRATION_ADDED.md](./DEBUG_EXPIRATION_ADDED.md)

**Commands:**
```bash
redis-cli KEYS "match_confirmation:*"
redis-cli GET "match_confirmation:<match_id>:data"
```

---

### Problem: Bot WebSockets fail to connect (HTTP 400)
**Symptoms:**
- Bots receive HTTP 400 error
- Connection refused messages

**Solutions:**
1. Verify Daphne is running on port 8000 (not 5888)
2. Check `server_url` in bot scripts
3. Review [WEBSOCKET_PORT_REFERENCE.md](./WEBSOCKET_PORT_REFERENCE.md)

**Fix:**
```python
# Correct
server_url = "ws://localhost:8000"

# Wrong
server_url = "ws://localhost:5888"
```

---

### Problem: AsyncToSync error in Celery tasks
**Symptoms:**
- "You cannot use AsyncToSync in the same thread as an async event loop"
- Celery task failures

**Solutions:**
1. Use `asyncio.new_event_loop()` in Celery tasks
2. Run async code with `loop.run_until_complete()`
3. Review [DEADLOCK_FIX_COMPLETE.md](./DEADLOCK_FIX_COMPLETE.md)

**Example:**
```python
import asyncio

@shared_task
def my_celery_task():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(my_async_function())
        return result
    finally:
        loop.close()
```

---

### Problem: Orphaned WebSocket connections
**Symptoms:**
- Bot script crashed but connections still active
- Multiple connections for same bot

**Solutions:**
1. Restart Daphne server (connections timeout automatically)
2. Use cleanup script (if available)
3. Wait 30-60 seconds for natural timeout
4. Review [WEBSOCKET_CLEANUP_GUIDE.md](./WEBSOCKET_CLEANUP_GUIDE.md)

**Commands:**
```bash
# Restart Daphne
# Stop current process (Ctrl+C)
# Start again
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application
```

---

### Problem: Redis keys not expiring
**Symptoms:**
- Old match data persists
- Queue has stale lobbies

**Solutions:**
1. Check TTL is set correctly
2. Verify `SETEX` is used (not `SET` + `EXPIRE`)
3. Manual cleanup if needed

**Commands:**
```bash
# Check TTL
redis-cli TTL "match_confirmation:<match_id>:data"

# Manual cleanup
redis-cli DEL "match_confirmation:*"
redis-cli DEL "matchmaking:queue:pug"
```

---

### Problem: Frontend timer stops after accepting
**Symptoms:**
- Timer freezes after clicking accept
- User removed from queue prematurely

**Solutions:**
1. Check `userAccepted` state is tracked correctly
2. Verify timer expiration only acts if user didn't accept
3. Review match timeout handler in frontend

**Code Check:**
```javascript
// Frontend should check userAccepted before removing from queue
if (matchFound && timeLeft === 0 && !userAccepted) {
  // Only leave queue if user didn't accept
  await api.leavePugQueue();
}
```

---

## Debugging Checklist

### When matches don't work:
- [ ] Daphne running on port 8000?
- [ ] Celery worker running?
- [ ] Celery beat running?
- [ ] Redis server running?
- [ ] Check Daphne console for WebSocket events
- [ ] Check Celery console for task execution
- [ ] Check Redis for match confirmation keys

### When requeueing fails:
- [ ] Check if `match_lobbies` data exists
- [ ] Verify `queued_at` timestamp preserved
- [ ] Review cleanup task logs
- [ ] Check per-lobby acceptance tracking
- [ ] Verify lobbies with 100% acceptance are requeued

### When bots don't work:
- [ ] Bot script using correct WebSocket port (8000)
- [ ] Bot WebSocket connections established
- [ ] BotAutoAcceptorWS properly initialized
- [ ] Bot PUUIDs match database
- [ ] Check bot script console for errors

---

## Useful Commands

### Redis Inspection
```bash
# List all queues
redis-cli KEYS "matchmaking:queue:*"

# Check specific lobby
redis-cli GET "matchmaking:lobby_data:<lobby_id>"

# List active matches
redis-cli KEYS "match_confirmation:*:data"

# Clear everything (DANGEROUS)
redis-cli FLUSHALL
```

### Process Management
```bash
# Check if services running
Get-Process | Where-Object {$_.Name -like "*python*"}
Get-Process | Where-Object {$_.Name -like "*redis*"}

# Kill stuck processes (Windows)
Stop-Process -Name "python" -Force
```

---

## When All Else Fails

1. **Check the logs** - Daphne, Celery Worker, Celery Beat
2. **Review [QUICK_FIX_REFERENCE.md](./QUICK_FIX_REFERENCE.md)**
3. **Clear Redis and restart all services**
4. **Check [../matchmaking/](../matchmaking/) for system-specific issues**
5. **Review recent changes in [FINAL_FIXES_SUMMARY.md](./FINAL_FIXES_SUMMARY.md)**

---

**Last Updated**: October 2025

