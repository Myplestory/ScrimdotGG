# WebSocket Port Reference

## Server Configuration

### **Daphne Server (Django WebSockets)**
- **Port**: `8000`
- **URL**: `http://localhost:8000` or `ws://localhost:8000`
- **Command**: `pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application`
- **Used for**: Django Channels WebSocket connections (matchmaking, lobbies, chat)

### **Client Backend (Electron)**
- **Port**: `5888`
- **URL**: `http://localhost:5888` or `ws://localhost:5888`
- **Used for**: Electron app ↔ Python backend communication (Quart server)

---

## WebSocket Endpoints

### **Matchmaking WebSocket**
- **Endpoint**: `/ws/matchmaking/{puuid}/`
- **Full URL**: `ws://localhost:8000/ws/matchmaking/{puuid}/`
- **Server**: Daphne (port 8000)
- **Consumer**: `PugSocketConsumer`
- **Used by**: 
  - User clients (Electron app → Daphne)
  - Bot clients (Test scripts → Daphne)

---

## Connection Examples

### **User Client (via Electron)**
```javascript
// Frontend connects to Electron backend
const ws = new WebSocket('ws://localhost:5888/ws');

// Electron backend connects to Django
websocket_url = 'ws://localhost:8000/ws/matchmaking/{puuid}/'
```

### **Bot Client (Test Scripts)**
```python
# Bot WebSocket client
client = BotWebSocketClient(
    bot_puuid='queuebot-0',
    server_url='ws://localhost:8000'  # ← Daphne port!
)
await client.connect()
# Connects to: ws://localhost:8000/ws/matchmaking/queuebot-0/
```

---

## Common Issues

### **HTTP 400 - Server Rejected Connection**

**Cause**: Wrong port number

**Error Example:**
```
ERROR: Failed to connect bot queuebot-0: server rejected WebSocket connection: HTTP 400
```

**Solution**: Check Daphne port
```python
# ❌ WRONG - Port 5888 is Electron backend
server_url = "ws://localhost:5888"

# ✅ CORRECT - Port 8000 is Daphne
server_url = "ws://localhost:8000"
```

---

### **Connection Refused**

**Cause**: Daphne not running

**Solution**: Start Daphne server
```bash
cd server
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application
```

---

## Port Summary

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| **Daphne** | 8000 | HTTP/WS | Django Channels |
| **Electron Backend** | 5888 | HTTP/WS | Electron ↔ Python |
| **Redis** | 6379 | TCP | Cache/Queue |
| **PostgreSQL** | 5432 | TCP | Database |

---

## Updated Configuration

All bot WebSocket clients now default to **port 8000**:
- ✅ `bot_websocket_client.py`: `server_url = "ws://localhost:8000"`
- ✅ `bot_auto_acceptor_ws.py`: `server_url = "ws://localhost:8000"`

**This matches the Daphne server port!**

