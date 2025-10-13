# Bot WebSocket Connection - Feasibility Analysis

## Summary
**✅ FEASIBLE** - Bots can use WebSocket connections instead of direct `MatchConfirmationManager` calls.

---

## Current Architecture

### **How User Clients Connect:**
1. **WebSocket URL**: `ws://localhost:8000/ws/matchmaking/{puuid}/` (Daphne server)
2. **Connection Flow**:
   - Client connects with player's PUUID in URL
   - Server adds client to `player_{puuid}` group
   - Server finds player's lobby and adds client to `lobby_{lobby_id}` group
   - Client sends events (e.g., `accept_match`) through WebSocket
   - Server broadcasts responses to appropriate groups

### **How Bots Currently Accept:**
- **Direct Method Call**: `MatchConfirmationManager.accept_match(match_id, puuid)`
- **No WebSocket**: Bots bypass the consumer entirely
- **No Broadcasts**: Only logs to console, doesn't trigger `player_accepted` events

---

## WebSocket Implementation for Bots

### **Required Components:**

1. **WebSocket URL Pattern** (Already exists):
   ```python
   ws://localhost:5888/ws/matchmaking/{bot_puuid}/
   ```

2. **Python WebSocket Client** (Already exists):
   - **Library**: `websockets` (already in codebase)
   - **Reference**: `client/backend/pugapi.py` - `PugSocketClient` class
   - **Features**:
     - Async connection management
     - Event listening
     - Message sending
     - Auto-reconnection

3. **Bot WebSocket Client Implementation**:
   ```python
   import asyncio
   import websockets
   import json
   
   class BotWebSocketClient:
       def __init__(self, bot_puuid, server_url="ws://localhost:5888"):
           self.bot_puuid = bot_puuid
           self.websocket_url = f"{server_url}/ws/matchmaking/{bot_puuid}/"
           self.websocket = None
           self.connected = False
       
       async def connect(self):
           self.websocket = await websockets.connect(self.websocket_url)
           self.connected = True
           asyncio.create_task(self.listen())
       
       async def listen(self):
           async for message in self.websocket:
               data = json.loads(message)
               await self.handle_event(data['event'], data.get('data', {}))
       
       async def handle_event(self, event, data):
           if event == 'match_found':
               match_id = data.get('match_id')
               # Auto-accept after random delay
               await asyncio.sleep(random.uniform(1.0, 15.0))
               await self.accept_match(match_id)
       
       async def accept_match(self, match_id):
           await self.websocket.send(json.dumps({
               'event': 'accept_match',
               'payload': {'match_id': match_id}
           }))
   ```

---

## Pros & Cons

### **✅ Pros:**

1. **Consistent Architecture**:
   - Bots and users use the same code path
   - All acceptances trigger WebSocket broadcasts
   - No special-case logic needed

2. **Automatic Broadcasting**:
   - Every acceptance (bot or user) broadcasts to all lobbies
   - Modal indicators update correctly for all players
   - No need to modify `MatchConfirmationManager`

3. **Easier Debugging**:
   - All traffic goes through WebSocket consumer
   - Can monitor WebSocket messages
   - Centralized logging

4. **Future-Proof**:
   - Any WebSocket improvements apply to bots automatically
   - Easy to add more bot behaviors (decline, chat, etc.)

5. **Real Connection Simulation**:
   - Bots appear as real connected players
   - Can test disconnection scenarios
   - More realistic load testing

### **❌ Cons:**

1. **More Complex Bot Script**:
   - Need to manage WebSocket connections for each bot
   - Async event handling required
   - Connection lifecycle management

2. **Resource Overhead**:
   - 9 WebSocket connections (one per bot)
   - Memory overhead for each connection
   - More network traffic

3. **Connection Management**:
   - Need to handle WebSocket errors
   - Reconnection logic
   - Cleanup on test end

4. **Server Load**:
   - More active WebSocket connections
   - Channel layer broadcasts to more clients
   - Slightly higher CPU/memory usage

5. **Test Setup Complexity**:
   - Need to establish connections before queuing
   - Wait for connections to be ready
   - Coordinate bot lifecycle

---

## Performance Impact

### **Resource Comparison:**

| Method | WebSocket Connections | Redis Calls | Broadcasts |
|--------|----------------------|-------------|------------|
| **Direct Call** | 1 (user only) | 9 (bot accepts) | 1 (user only) |
| **WebSocket** | 10 (all players) | 10 (all accepts) | 10 (all players) |

### **Estimated Impact:**
- **Memory**: ~1-2 MB per WebSocket connection = ~9-18 MB additional
- **CPU**: Minimal (async I/O bound)
- **Network**: ~1 KB per message × 10 connections = ~10 KB per acceptance
- **Latency**: <5ms additional per WebSocket hop

**Verdict**: Negligible impact for testing purposes (9 bots).

---

## Alternative Approaches

### **Option 1: Broadcast from MatchConfirmationManager** (Simpler)
**Pros**:
- Minimal changes to bot script
- No connection management
- Lower resource usage

**Cons**:
- Two code paths for acceptance
- Need to handle async broadcast in sync method
- Less realistic testing

**Implementation**:
```python
# In MatchConfirmationManager.accept_match():
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()
for lobby_id in match_lobbies:
    await channel_layer.group_send(
        f"lobby_{lobby_id}",
        {
            'type': 'player_accepted',
            'accepted_count': accepted_count,
            'total_players': total_players,
            'timeout_seconds': timeout_seconds
        }
    )
```

### **Option 2: WebSocket for Bots** (More Realistic)
**Pros**:
- Single code path
- More realistic testing
- Future-proof

**Cons**:
- More complex bot script
- Higher resource usage
- More setup required

**Implementation**: (As described in "WebSocket Implementation for Bots" section)

---

## Recommendation

### **For Current Testing**: Option 1 (Broadcast from MatchConfirmationManager)
- **Why**: Faster to implement, minimal changes
- **Use Case**: Quick testing of modal indicator updates
- **Time to Implement**: 15 minutes

### **For Production/Long-term**: Option 2 (WebSocket for Bots)
- **Why**: More maintainable, realistic, single code path
- **Use Case**: Comprehensive integration testing, load testing
- **Time to Implement**: 1-2 hours

---

## Implementation Steps (Option 2)

### **Phase 1: Create Bot WebSocket Client**
1. Create `server/testing/bot_websocket_client.py`
2. Implement connection, listening, and event handling
3. Add auto-acceptance logic with random delays

### **Phase 2: Modify Bot Test Script**
1. Update `server/testing/test_queue_with_bots_v2.py`
2. Establish WebSocket connections for all bots
3. Wait for connections before queuing
4. Remove direct `MatchConfirmationManager.accept_match()` calls

### **Phase 3: Update Bot Auto-Acceptor**
1. Modify `server/testing/bot_auto_acceptor.py`
2. Use WebSocket to send accept events
3. Listen for `match_found` events via WebSocket

### **Phase 4: Testing**
1. Run test with user + 9 bots
2. Verify all 10 indicators update correctly
3. Test timeout and requeue behavior
4. Verify performance under load

---

## Code Example: Modified Bot Auto-Acceptor

```python
import asyncio
import websockets
import json
import logging

logger = logging.getLogger(__name__)

class BotWebSocketClient:
    def __init__(self, bot_puuid, server_url="ws://localhost:5888"):
        self.bot_puuid = bot_puuid
        self.websocket_url = f"{server_url}/ws/matchmaking/{bot_puuid}/"
        self.websocket = None
        self.connected = False
        self.match_found_callback = None
    
    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.connected = True
            logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} connected")
            asyncio.create_task(self.listen())
        except Exception as e:
            logger.error(f"[BOT WS] Failed to connect bot {self.bot_puuid[:12]}: {e}")
    
    async def listen(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_event(data['event'], data.get('data', {}))
        except websockets.ConnectionClosed:
            logger.warning(f"[BOT WS] Bot {self.bot_puuid[:12]} disconnected")
            self.connected = False
    
    async def handle_event(self, event, data):
        if event == 'match_found':
            if self.match_found_callback:
                await self.match_found_callback(data)
    
    async def accept_match(self, match_id):
        if not self.connected:
            logger.error(f"[BOT WS] Bot {self.bot_puuid[:12]} not connected")
            return
        
        await self.websocket.send(json.dumps({
            'event': 'accept_match',
            'payload': {'match_id': match_id}
        }))
        logger.info(f"[BOT WS] Bot {self.bot_puuid[:12]} sent accept for match {match_id[:8]}")
    
    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.connected = False
```

---

## Conclusion

**Both approaches are feasible**, but:
- **Option 1** (Broadcast from MatchConfirmationManager) is **faster and simpler** for immediate testing
- **Option 2** (WebSocket for Bots) is **better for long-term** maintainability and realistic testing

**Recommendation**: Start with **Option 1** to quickly fix the modal indicator issue, then migrate to **Option 2** when time permits for a more robust testing infrastructure.

