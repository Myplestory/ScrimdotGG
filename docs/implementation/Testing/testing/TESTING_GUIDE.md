# Phase 1 Lobby Operations - Testing Guide

Complete guide for testing the lobby system implementation.

---

## 🎯 **Testing Overview**

### **What We're Testing**
- ✅ Lobby creation and management
- ✅ Player join/leave operations
- ✅ Queue system integration
- ✅ WebSocket communication
- ✅ Match flow progression

### **Test Environment**
- **Backend**: Django + Channels
- **Frontend**: React + Electron
- **Database**: PostgreSQL
- **Queue**: Redis + Celery

---

## 🚀 **Setup & Prerequisites**

### **1. Start All Services**
```bash
# Terminal 1: Django Server
cd server
pipenv run python manage.py runserver

# Terminal 2: Celery Worker
cd server
pipenv run celery -A scrimgg worker --loglevel=info

# Terminal 3: Frontend
cd client/frontend
npm start
```

### **2. Verify Services**
- [ ] Django server running on http://localhost:8000
- [ ] Celery worker connected
- [ ] Frontend accessible
- [ ] Redis running
- [ ] Database connected

---

## 📋 **Test Cases**

### **Test 1: Lobby Creation**
1. **Open Electron app**
2. **Click "Create Lobby"**
3. **Verify lobby created**
4. **Check lobby ID generated**
5. **Confirm player is lobby leader**

**Expected Results:**
- ✅ Lobby appears in lobby list
- ✅ Player shown as leader
- ✅ Lobby ID is unique
- ✅ Status shows "Waiting for players"

### **Test 2: Player Join**
1. **Create lobby from Test 1**
2. **Open second Electron instance**
3. **Click "Join Lobby"**
4. **Enter lobby ID**
5. **Verify join success**

**Expected Results:**
- ✅ Player appears in lobby
- ✅ Player count updates
- ✅ All players see new member
- ✅ Lobby status updates

### **Test 3: Queue Integration**
1. **Have 2+ players in lobby**
2. **Leader clicks "Queue Up"**
3. **Verify queue entry**
4. **Check queue status**

**Expected Results:**
- ✅ Lobby enters queue
- ✅ Queue status shows "Searching"
- ✅ Players can't leave lobby
- ✅ Matchmaking begins

### **Test 4: Match Flow**
1. **Complete Test 3**
2. **Wait for match found**
3. **Accept match**
4. **Verify match progression**

**Expected Results:**
- ✅ Match found notification
- ✅ Accept/decline options
- ✅ Match progression works
- ✅ Teams assigned correctly

---

## 🔍 **Detailed Testing**

### **WebSocket Communication**
1. **Open browser dev tools**
2. **Go to Network → WS tab**
3. **Monitor WebSocket messages**
4. **Verify message flow**

**Expected Messages:**
```json
// Lobby created
{"event": "lobby_created", "payload": {"lobby_id": "abc123"}}

// Player joined
{"event": "player_joined", "payload": {"player": {...}}}

// Queue entered
{"event": "queue_entered", "payload": {"queue_id": "xyz789"}}

// Match found
{"event": "match_found", "payload": {"match_id": "def456"}}
```

### **Database Verification**
```sql
-- Check lobby creation
SELECT * FROM matchmaking_lobby WHERE id = 'abc123';

-- Check player associations
SELECT * FROM matchmaking_lobbyplayer WHERE lobby_id = 'abc123';

-- Check queue entries
SELECT * FROM matchmaking_queueentry WHERE lobby_id = 'abc123';
```

### **Celery Task Monitoring**
```bash
# Monitor Celery logs
tail -f celery.log

# Check task status
pipenv run python manage.py shell
>>> from celery.result import AsyncResult
>>> result = AsyncResult('task-id')
>>> result.status
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Lobby Creation Fails**
- **Check**: Django server running
- **Check**: Database connection
- **Check**: WebSocket connection
- **Fix**: Restart Django server

#### **Player Join Fails**
- **Check**: Lobby ID correct
- **Check**: Player not already in lobby
- **Check**: WebSocket connection
- **Fix**: Refresh frontend

#### **Queue Entry Fails**
- **Check**: Celery worker running
- **Check**: Redis connection
- **Check**: Lobby has enough players
- **Fix**: Restart Celery worker

#### **Match Flow Fails**
- **Check**: Matchmaker running
- **Check**: Queue entries exist
- **Check**: Team balance algorithm
- **Fix**: Check Celery logs

### **Debug Commands**
```bash
# Check Django logs
tail -f server.log

# Check Celery logs
tail -f celery.log

# Check Redis
redis-cli ping

# Check database
pipenv run python manage.py dbshell
```

---

## 📊 **Performance Testing**

### **Load Testing**
1. **Create multiple lobbies**
2. **Add players to each lobby**
3. **Queue all lobbies**
4. **Monitor system performance**

**Metrics to Watch:**
- Response times
- Memory usage
- CPU usage
- Database queries
- WebSocket connections

### **Stress Testing**
1. **Create 100+ lobbies**
2. **Add players rapidly**
3. **Queue simultaneously**
4. **Monitor for failures**

**Success Criteria:**
- No crashes
- Response times < 2s
- Memory usage stable
- No data corruption

---

## ✅ **Test Checklist**

### **Basic Functionality**
- [ ] Lobby creation works
- [ ] Player join works
- [ ] Player leave works
- [ ] Queue entry works
- [ ] Match flow works

### **Edge Cases**
- [ ] Empty lobby handling
- [ ] Maximum player limit
- [ ] Duplicate player join
- [ ] Network disconnection
- [ ] Server restart

### **Performance**
- [ ] Response times acceptable
- [ ] Memory usage stable
- [ ] No memory leaks
- [ ] Database queries optimized
- [ ] WebSocket connections stable

### **Integration**
- [ ] Frontend-backend communication
- [ ] Database operations
- [ ] Celery task execution
- [ ] Redis queue operations
- [ ] WebSocket message flow

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- ✅ All test cases pass
- ✅ No critical bugs
- ✅ Edge cases handled
- ✅ Error messages clear

### **Performance Requirements**
- ✅ Response times < 2s
- ✅ Memory usage stable
- ✅ No crashes under load
- ✅ Database queries optimized

### **User Experience**
- ✅ Intuitive interface
- ✅ Clear feedback
- ✅ Smooth interactions
- ✅ Error recovery

---

## 📝 **Test Report Template**

### **Test Summary**
- **Date**: [Date]
- **Tester**: [Name]
- **Version**: [Version]
- **Environment**: [Environment]

### **Results**
- **Total Tests**: [Number]
- **Passed**: [Number]
- **Failed**: [Number]
- **Skipped**: [Number]

### **Issues Found**
- **Critical**: [Number]
- **High**: [Number]
- **Medium**: [Number]
- **Low**: [Number]

### **Recommendations**
- [Recommendation 1]
- [Recommendation 2]
- [Recommendation 3]

---

**Ready to test! Follow this guide step by step and report any issues found.** 🚀
