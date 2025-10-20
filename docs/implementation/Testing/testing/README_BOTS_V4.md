# Bot Testing System V4 - Real User Simulation

## Overview

The V4 bot system creates bots that behave **identically** to real users by:
- Using proper UUID format for PUUIDs (like real users)
- Connecting via WebSocket consumers (same path as real users)
- Going through identical validation and queue flows
- Auto-accepting matches for seamless testing

## Key Improvements Over V3

### V3 Issues (Fixed):
- ❌ Used non-standard PUUID format (`queuebot-0`, `queuebot-1`)
- ❌ Called Django methods directly (bypassed user flow)
- ❌ Different validation path than real users
- ❌ Database compatibility issues with SQLite

### V4 Solutions:
- ✅ Proper UUID format (`52f0666e-4d7a-5b84-9e1a-a35286de3d27`)
- ✅ WebSocket consumer connection (identical to real users)
- ✅ Same validation path as real users
- ✅ No database compatibility issues

## Usage

### Run the V4 Bot Test:
```bash
cd server/testing
python test_queue_with_bots_v4.py
```

### Clean Up After Testing:
```bash
cd server/testing
python cleanup_bots_simple.py
```

## How It Works

### 1. Bot Creation
```python
# Generate proper UUID (like real users)
bot_puuid = str(uuid.uuid4())

# Create player in database
Player.objects.get_or_create(puuid=bot_puuid, ...)
```

### 2. WebSocket Connection
```python
# Connect to same consumer as real users
ws_url = f"ws://localhost:8000/ws/matchmaking/{bot_puuid}/"
websocket = await websockets.connect(ws_url)
```

### 3. Queue Flow (Identical to Real Users)
```python
# 1. Create lobby via WebSocket
await websocket.send({"event": "create_lobby", ...})

# 2. Set preferences via WebSocket  
await websocket.send({"event": "update_lobby_preferences", ...})

# 3. Join queue via WebSocket
await websocket.send({"event": "add_lobby_to_queue", ...})
```

### 4. Auto-Accept Matches
```python
# Listen for match found events
if event == 'match_found':
    # Auto-accept immediately
    await websocket.send({"event": "accept_match", ...})
```

## Benefits

### 1. **Identical Validation Path**
Both you and bots go through the exact same code:
- WebSocket Consumer → `add_lobby_to_queue()` → validation
- No more validation discrepancies!

### 2. **Real User Simulation** 
Bots are indistinguishable from real users:
- Same PUUID format
- Same connection method
- Same message flow
- Same error handling

### 3. **Future-Proof Testing**
Any new features added to the user flow automatically work with bots.

### 4. **Complete Flow Testing**
Tests the entire stack:
- WebSocket consumer code
- Validation logic
- Queue management
- Match confirmation
- Auto-acceptance

## Configuration

Edit `test_queue_with_bots_v4.py` to customize:

```python
# Number of bots (default: 9 for 10-player matches)
NUM_BOTS = 9

# ELO/MMR ranges
BASE_ELO = 6000
BASE_MMR = 6000

# Region
REGION = 'na'

# Timeout for match finding
TIMEOUT_SECONDS = 300
```

## Troubleshooting

### Bot Connection Issues:
- Ensure Daphne is running: `pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application`
- Check WebSocket URL format: `ws://localhost:8000/ws/matchmaking/{puuid}/`

### Validation Errors:
- V4 bots use the same validation as real users
- If bots fail validation, real users would too
- Check `MatchStateValidator` logs for details

### Match Not Found:
- Ensure Celery worker is running: `pipenv run celery -A scrimgg worker -l info`
- Check that periodic matchmaking task is enabled
- Verify 10+ players total (9 bots + you)

### Cleanup Issues:
- Run `cleanup_bots_simple.py` to remove bot data
- Restart Daphne if WebSocket connections persist
- Check Redis for orphaned queue entries

## Testing Workflow

1. **Start Services:**
   ```bash
   # Terminal 1: Django + WebSocket
   pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application
   
   # Terminal 2: Celery worker  
   pipenv run celery -A scrimgg worker -l info
   
   # Terminal 3: Celery beat (for periodic matchmaking)
   pipenv run celery -A scrimgg beat -l info
   ```

2. **Run Bot Test:**
   ```bash
   # Terminal 4: Bot test
   cd server/testing
   python test_queue_with_bots_v4.py
   ```

3. **Join Queue with Client:**
   - Open your client application
   - Join the PUG queue
   - Bots will auto-accept when match is found

4. **Clean Up:**
   ```bash
   python cleanup_bots_simple.py
   ```

## Success Indicators

✅ **Bot Creation:** "Successfully created X/9 bots"  
✅ **WebSocket Connection:** "Bot QueueBotX connected to WebSocket"  
✅ **Queue Join:** "Bot QueueBotX joined queue successfully"  
✅ **Match Found:** "Match found! Bot QueueBotX detected match"  
✅ **Auto-Accept:** "Bot QueueBotX match confirmed!"  

The V4 system eliminates all validation issues by making bots behave exactly like real users! 🎉
