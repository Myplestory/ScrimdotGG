# Phase 1 Lobby Operations - Testing Guide

Complete guide for testing the lobby system implementation.

---

## 🎯 Testing Methods

There are 4 ways to test the lobby operations:

1. **Automated Python Tests** - Direct LobbyManager testing
2. **WebSocket Tests** - Test consumer through WebSocket
3. **Browser DevTools** - Manual WebSocket testing
4. **Client Application** - Full integration testing

---

## Method 1: Automated Python Tests ⭐ RECOMMENDED

### Quick Start

```bash
cd server
python test_lobby_operations.py
```

### What It Tests
- ✅ Create lobby
- ✅ Add player to lobby
- ✅ Update preferences (maps/servers)
- ✅ Validate queue eligibility
- ✅ Kick player from lobby
- ✅ Player leaves lobby
- ✅ Get lobby by player
- ✅ Auto-cleanup test data

### Expected Output
```
============================================================
PHASE 1 LOBBY OPERATIONS TEST SUITE
============================================================

============================================================
TEST 1: Create Lobby
============================================================
✓ Test player: TestPlayer1 (ELO: 1500)
✅ PASSED: Lobby created successfully
   - Lobby ID: abc123-...
   - Leader: TestPlayer1
   - Size: 1/5
   - Average ELO: 1500.0

... (more tests)

============================================================
✅ ALL TESTS COMPLETED
============================================================
```

### Customize Tests

Edit `server/test_lobby_operations.py` to:
- Change player ELO values
- Test different scenarios
- Add more test cases

---

## Method 2: WebSocket Tests

### Prerequisites

1. **Start Django Server**
```bash
cd server
python manage.py runserver
```

2. **Create Test Players**
```bash
python manage.py shell
```

```python
from scrimgg.models import Player

# Create test players
Player.objects.get_or_create(
    puuid='test-ws-player-1',
    defaults={
        'username': 'WSTest#001',
        'alias': 'WSTestPlayer1',
        'region': 'na',
        'elo': 1500
    }
)

Player.objects.get_or_create(
    puuid='test-ws-player-2',
    defaults={
        'username': 'WSTest#002',
        'alias': 'WSTestPlayer2',
        'region': 'na',
        'elo': 1550
    }
)

exit()
```

### Run WebSocket Tests

3. **Update PUUIDs in test script**
Edit `server/test_websocket_lobby.py` and update the PUUIDs to match your test players.

4. **Run tests**
```bash
# Install websockets if not already installed
pip install websockets

# Run test
python test_websocket_lobby.py
```

Choose:
- `1` for single player test
- `2` for multi-player test

### Expected Output
```
WEBSOCKET TEST: Single Player Flow
============================================================
[test-ws-player-1] Connecting to ws://localhost:8000/...
[test-ws-player-1] ✓ Connected

TEST: Create Lobby (test-ws-player-1)
============================================================
[test-ws-player-1] → Sent: create_lobby
[test-ws-player-1] ← Received: lobby_created
✅ Lobby created: abc123-...
```

---

## Method 3: Browser DevTools (Manual Testing)

Perfect for debugging and understanding WebSocket messages.

### Steps

1. **Start Django Server**
```bash
cd server
python manage.py runserver
```

2. **Open Browser Console** (F12 in Chrome/Firefox)

3. **Create WebSocket Connection**
```javascript
// Replace with actual player PUUID
const puuid = 'your-player-puuid-here';
const ws = new WebSocket(`ws://localhost:8000/ws/matchmaking/${puuid}/`);

ws.onopen = () => console.log('✅ Connected');
ws.onmessage = (e) => console.log('📥', JSON.parse(e.data));
ws.onerror = (e) => console.error('❌', e);
```

4. **Test: Create Lobby**
```javascript
ws.send(JSON.stringify({
    event: 'create_lobby',
    payload: { puuid: 'your-player-puuid-here' }
}));
```

5. **Test: Update Preferences**
```javascript
// Use lobby_id from previous response
ws.send(JSON.stringify({
    event: 'update_lobby_preferences',
    payload: {
        lobby_id: 'lobby-id-from-creation',
        requester_puuid: 'your-player-puuid-here',
        map_preferences: ['Ascent', 'Bind', 'Haven', 'Pearl', 'Split'],
        server_preferences: ['Virginia', 'Illinois']
    }
}));
```

6. **Test: Send Chat Message**
```javascript
ws.send(JSON.stringify({
    event: 'lobby_message',
    payload: {
        message: 'Hello from browser!',
        lobby_id: 'lobby-id-from-creation',
        userAlias: 'BrowserTester',
        timestamp: new Date().toISOString()
    }
}));
```

7. **Test: Leave Lobby**
```javascript
ws.send(JSON.stringify({
    event: 'leave_lobby',
    payload: {
        lobby_id: 'lobby-id-from-creation',
        player_puuid: 'your-player-puuid-here'
    }
}));
```

### Pro Tips
- Keep console open to see all messages
- Copy responses to a text editor for analysis
- Use `JSON.stringify(obj, null, 2)` for pretty printing

---

## Method 4: Client Application Testing

Test through your actual Electron client.

### Prerequisites

1. **Start Django Server**
```bash
cd server
python manage.py runserver
```

2. **Start Client Backend**
```bash
cd client/backend
pipenv shell
python bootstrap.py
```

3. **Start Client Frontend**
```bash
cd client/frontend
npm start
```

### Testing Flow

1. **Login** to Valorant through client
2. **Create Lobby** - Should auto-create when logged in
3. **Open DevTools** in Electron (Ctrl+Shift+I)
4. **Check Network Tab** → WS → See WebSocket messages
5. **Check Console** → See event logs

### What to Verify
- ✅ Lobby created automatically
- ✅ Player info displayed correctly
- ✅ Map selection updates preferences
- ✅ Chat messages sent/received
- ✅ Leave lobby works

---

## 🐛 Troubleshooting

### Issue: "Connection refused"

**Solution:**
```bash
# Check Django is running
curl http://localhost:8000/admin/

# Check Redis is running
redis-cli ping
# Should return: PONG
```

### Issue: "Player does not exist"

**Solution:**
```bash
python manage.py shell
```
```python
from scrimgg.models import Player

# List all players
for p in Player.objects.all():
    print(f"{p.alias} - {p.puuid}")

# Create player if needed
Player.objects.create(
    puuid='your-puuid',
    username='Username#TAG',
    alias='DisplayName',
    region='na',
    elo=1500
)
```

### Issue: "Import errors" in test scripts

**Solution:**
```bash
# Make sure you're in the server directory
cd server

# Run with proper Django setup
python test_lobby_operations.py
```

### Issue: WebSocket test shows "timeout"

**Possible causes:**
1. Django server not running
2. Redis not running
3. Wrong PUUID in test script
4. Consumer has an error (check Django console)

**Check Django logs:**
```bash
# Django will show errors in the terminal where you ran runserver
# Look for errors in the consumer
```

---

## ✅ Success Indicators

You'll know testing is successful when you see:

### Automated Tests
- All tests show `✅ PASSED`
- No `❌ FAILED` messages
- Cleanup completes successfully

### WebSocket Tests
- Connection establishes
- Events send/receive without timeout
- Proper event names in responses

### Browser DevTools
- WebSocket shows "open" status (green)
- Messages appear in console
- No error messages

### Client Application
- Lobby UI updates in real-time
- No console errors
- All operations work smoothly

---

## 📊 Test Coverage

| Feature | Python Test | WebSocket Test | Browser Test | Client Test |
|---------|------------|----------------|--------------|-------------|
| Create Lobby | ✅ | ✅ | ✅ | ✅ |
| Add Player | ✅ | ✅ | ⚠️ | ✅ |
| Kick Player | ✅ | ⚠️ | ⚠️ | ✅ |
| Leave Lobby | ✅ | ✅ | ✅ | ✅ |
| Update Prefs | ✅ | ✅ | ✅ | ✅ |
| Chat Message | ⚠️ | ✅ | ✅ | ✅ |
| Queue Check | ✅ | ⚠️ | ⚠️ | ⚠️ |

**Legend:**
- ✅ Covered
- ⚠️ Partial/Manual
- ❌ Not covered

---

## 🔍 Debugging Tips

### View Database State
```bash
python manage.py shell
```

```python
from scrimgg.models import Lobby, Player

# See all active lobbies
for lobby in Lobby.objects.filter(is_active=True):
    print(f"Lobby {lobby.id}: {lobby.size} players, Leader: {lobby.lobby_leader.alias}")
    for player in lobby.players.all():
        print(f"  - {player.alias} (ELO: {player.elo})")
```

### Check Redis State
```bash
redis-cli

# See all keys
KEYS *

# Check specific lobby queue
ZRANGE matchmaking:queue:pug 0 -1 WITHSCORES
```

### Enable Debug Logging
Edit `server/scrimgg/settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

---

## 📝 Next Steps After Testing

Once all tests pass:

1. ✅ **Phase 1 Complete** - Lobby system working
2. 🔜 **Phase 2** - Implement queue system
3. 🔜 **Phase 3** - Match confirmation
4. 🔜 **Phase 4** - Matchmaking algorithm

---

## 💡 Pro Testing Tips

1. **Test in Order**
   - Start with Python tests (fastest)
   - Then WebSocket tests (realistic)
   - Finally client tests (full integration)

2. **Keep Django Logs Open**
   - See real-time errors
   - Debug WebSocket messages
   - Track performance

3. **Use Multiple Terminals**
   - Terminal 1: Django server
   - Terminal 2: Redis
   - Terminal 3: Test scripts
   - Terminal 4: Client backend

4. **Save Test Data**
   - Keep test player PUUIDs
   - Document lobby IDs
   - Save successful payloads

5. **Automate Regression**
   - Run Python tests after any changes
   - Ensures no breaking changes
   - Fast feedback loop

---

## 🆘 Need Help?

If tests fail:
1. Check prerequisites (Django, Redis running)
2. Review Django console logs
3. Verify player exists in database
4. Check network tab in DevTools
5. Review code review document for known issues

**Common Solutions:**
- Restart Django server
- Restart Redis
- Clear test data: `python manage.py shell` → `Lobby.objects.all().delete()`
- Check migrations: `python manage.py migrate`

---

**Ready to test?** Start with Method 1 (Automated Tests) - it's the fastest and most reliable!

