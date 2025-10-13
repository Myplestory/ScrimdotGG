# Architecture Comparison: Before vs After

Visual comparison of the current monolithic architecture and the proposed modular architecture.

---

## Current Architecture (Monolithic)

### File Structure
```
client/backend/
├── bootstrap.py          # 1360 lines - EVERYTHING
│   ├── WebSocket routing
│   ├── Event handlers (40+)
│   ├── Heartbeat system
│   ├── Connection state
│   ├── Broadcast logic
│   ├── Lifecycle (atexit/signal)
│   └── Utility functions
│
├── clientapi.py          # 663 lines
│   ├── ValorantAPI class
│   ├── Django WS connection
│   ├── Match monitoring
│   └── Callback closures
│
├── pugapi.py             # 354 lines
│   ├── PugSocketClient
│   ├── Event handlers (if/elif)
│   └── Message forwarding
│
└── main.js (Electron)
    ├── Spawns Python with shell=true
    ├── 3-second timeout fallback
    ├── Brittle process cleanup
    └── nodeIntegration: true
```

### Data Flow (Current)
```
┌─────────────┐
│   Electron  │
│   main.js   │
└──────┬──────┘
       │ spawn (shell=true)
       │ 3s timeout
       ▼
┌─────────────────────────────────────────┐
│          bootstrap.py (1360 lines)      │
│  ┌─────────────────────────────────┐   │
│  │  Global State                   │   │
│  │  - active_connections: Set      │   │
│  │  - client_states: Dict          │   │
│  │  - heartbeat_task: Task         │   │
│  │  - last_known_status: dict      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  WebSocket Route                │   │
│  │  @app.websocket('/ws')          │   │
│  │  - Parse JSON manually          │   │
│  │  - Look up handler in dict      │   │
│  │  - Call handler directly        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Event Handlers (40+ functions) │   │
│  │  - All in same file             │   │
│  │  - Direct global state access   │   │
│  │  - Mixed business logic         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Heartbeat Loop                 │   │
│  │  - Checks Valorant status       │   │
│  │  - Polls _pending_* fields      │   │
│  │  - Broadcasts to all clients    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Lifecycle (atexit/signal)      │   │
│  │  - Unreliable cleanup           │   │
│  │  - No Quart hooks               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────┐
│   clientapi.py  │
│   ValorantAPI   │
│   - Callbacks   │
│   - _pending_*  │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│   pugapi.py     │
│ PugSocketClient │
│  - if/elif      │
│  - Django WS    │
└─────────────────┘
```

### Problems
❌ **Monolithic bootstrap.py** - Hard to maintain  
❌ **Global state** - Hard to test  
❌ **No validation** - Raw JSON parsing  
❌ **Tight coupling** - Everything interconnected  
❌ **Unreliable lifecycle** - atexit/signal handlers  
❌ **No health check** - Electron uses 3s timeout  
❌ **Security issues** - nodeIntegration: true  
❌ **Poor process management** - shell=true, taskkill hacks  

---

## New Architecture (Modular)

### File Structure
```
client/backend/
├── app/
│   ├── __init__.py              # App factory (100 lines)
│   │   ├── Create Quart app
│   │   ├── Register blueprints
│   │   ├── Lifecycle hooks
│   │   └── Initialize services
│   │
│   ├── settings.py              # Configuration (30 lines)
│   │   └── Environment variables
│   │
│   ├── models/
│   │   └── messages.py          # Pydantic schemas (50 lines)
│   │       ├── Envelope
│   │       ├── ErrorResponse
│   │       └── Event payloads
│   │
│   ├── services/
│   │   └── valorant.py          # Service wrapper (100 lines)
│   │       ├── Async facade
│   │       ├── Status checks
│   │       └── Clean API
│   │
│   ├── sockets/
│   │   ├── routes.py            # WebSocket route (50 lines)
│   │   │   ├── Parse message
│   │   │   ├── Validate schema
│   │   │   └── Route to handler
│   │   │
│   │   ├── manager.py           # ConnectionManager (150 lines)
│   │   │   ├── Connection state
│   │   │   ├── Send/broadcast
│   │   │   ├── Heartbeat loop
│   │   │   └── Graceful shutdown
│   │   │
│   │   ├── events.py            # Event registry (20 lines)
│   │   │   └── @on() decorator
│   │   │
│   │   └── handlers/
│   │       ├── __init__.py      # Import all handlers
│   │       ├── status.py        # 2 handlers (40 lines)
│   │       ├── auth.py          # 2 handlers (60 lines)
│   │       ├── lobby.py         # 5 handlers (100 lines)
│   │       ├── queue.py         # 2 handlers (80 lines)
│   │       ├── match.py         # 10 handlers (200 lines)
│   │       ├── veto.py          # 4 handlers (80 lines)
│   │       └── chat.py          # 2 handlers (40 lines)
│   │
│   └── routes/
│       └── health.py            # Health endpoint (10 lines)
│
├── run.py                       # Entry point (10 lines)
├── clientapi.py                 # [Keep as-is]
├── pugapi.py                    # [Keep as-is]
└── main.js (Electron)           # Updated
    ├── Health check polling
    ├── tree-kill process cleanup
    ├── Preload script security
    └── No shell=true
```

### Data Flow (New)
```
┌─────────────────────────────┐
│        Electron main.js      │
│  ┌──────────────────────┐   │
│  │ startPythonBackend() │   │
│  │ - spawn run.py       │   │
│  │ - no shell           │   │
│  │ - capture PID        │   │
│  └──────────────────────┘   │
│            │                 │
│            ▼                 │
│  ┌──────────────────────┐   │
│  │  waitForHealth()     │   │
│  │  - Poll /health      │   │
│  │  - 15s timeout       │   │
│  │  - Reliable          │   │
│  └──────────────────────┘   │
│            │                 │
│            ▼                 │
│  ┌──────────────────────┐   │
│  │  createWindow()      │   │
│  │  - After health OK   │   │
│  └──────────────────────┘   │
│                              │
│  ┌──────────────────────┐   │
│  │  preload.js          │   │
│  │  - contextBridge     │   │
│  │  - No node access    │   │
│  └──────────────────────┘   │
└──────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│               Python Backend                     │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │         run.py (entry point)           │    │
│  │  - Create app from factory             │    │
│  │  - Read PORT from env                  │    │
│  │  - Run server                          │    │
│  └────────────────────────────────────────┘    │
│                     │                           │
│                     ▼                           │
│  ┌────────────────────────────────────────┐    │
│  │      app/__init__.py (factory)         │    │
│  │                                         │    │
│  │  @app.before_serving:                  │    │
│  │    - Start heartbeat task              │    │
│  │                                         │    │
│  │  @app.after_serving:                   │    │
│  │    - Stop heartbeat                    │    │
│  │    - Close all connections             │    │
│  │                                         │    │
│  │  Initialize:                           │    │
│  │    - ConnectionManager                 │    │
│  │    - ValorantService                   │    │
│  │                                         │    │
│  │  Register:                             │    │
│  │    - WebSocket blueprint               │    │
│  │    - Health blueprint                  │    │
│  └────────────────────────────────────────┘    │
│                     │                           │
│        ┌────────────┴────────────┐             │
│        ▼                         ▼             │
│  ┌──────────────┐         ┌──────────────┐    │
│  │  /health     │         │     /ws      │    │
│  │  endpoint    │         │   endpoint   │    │
│  │              │         │              │    │
│  │  Return:     │         │  1. Parse    │    │
│  │  {"ok":true} │         │  2. Validate │    │
│  └──────────────┘         │  3. Route    │    │
│                           └──────┬───────┘    │
│                                  ▼             │
│                    ┌──────────────────────┐   │
│                    │   Event Registry     │   │
│                    │   get_handler(event) │   │
│                    └──────────┬───────────┘   │
│                               ▼               │
│              ┌────────────────────────────┐   │
│              │  Handler (by domain)       │   │
│              │  - status.py               │   │
│              │  - auth.py                 │   │
│              │  - queue.py                │   │
│              │  - match.py                │   │
│              │  - veto.py                 │   │
│              │  - chat.py                 │   │
│              │  - lobby.py                │   │
│              └────────────────────────────┘   │
│                               │                │
│                               ▼                │
│              ┌────────────────────────────┐   │
│              │   ConnectionManager        │   │
│              │   - state: Dict[int, dict] │   │
│              │   - active: Set[WS]        │   │
│              │   - send()                 │   │
│              │   - broadcast()            │   │
│              │   - start_heartbeat()      │   │
│              └────────────────────────────┘   │
│                               │                │
│                               ▼                │
│              ┌────────────────────────────┐   │
│              │   ValorantService          │   │
│              │   - check_status()         │   │
│              │   - login()                │   │
│              │   - create_lobby()         │   │
│              │   (wraps ValorantAPI)      │   │
│              └────────────────────────────┘   │
└──────────────────────────────────────────────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │    clientapi.py        │
                  │    ValorantAPI         │
                  │    - Valorant client   │
                  │    - Django WS client  │
                  └────────────────────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │    pugapi.py           │
                  │    PugSocketClient     │
                  │    - Django WS         │
                  │    - Event callbacks   │
                  └────────────────────────┘
```

### Benefits
✅ **Modular** - Each file has one responsibility  
✅ **Testable** - Easy to unit test handlers  
✅ **Type-safe** - Pydantic validation  
✅ **Decoupled** - Clear interfaces  
✅ **Reliable lifecycle** - Quart hooks  
✅ **Health checks** - Electron knows when ready  
✅ **Secure** - contextIsolation, no nodeIntegration  
✅ **Clean process management** - tree-kill, no shell  

---

## Message Flow Comparison

### Current Flow (Monolithic)
```
Frontend
   │
   │ ws.send({"event": "get_status", "payload": {}})
   ▼
┌────────────────────────────────────────────┐
│ bootstrap.py @app.websocket('/ws')         │
│                                            │
│  1. await ws.receive()                     │
│  2. data = json.loads(message)  ❌ No validation
│  3. event = data.get('event')              │
│  4. payload = data.get('payload', {})      │
│  5. await route_event(event, payload, ...)│
│                                            │
│  route_event():                            │
│    handlers = {                            │
│      'get_status': handle_get_status,      │
│      ...                                   │
│    }                                       │
│    handler = handlers.get(event)           │
│    await handler(payload, client_id, ws)   │
│                                            │
│  handle_get_status():                      │
│    # 40+ lines of logic here               │
│    # Direct global state access ❌         │
│    status = await check_valorant_status()  │
│    await send_message(ws, 'status_update',{│
│      'backend_connected': True,            │
│      'valorant': status,                   │
│      'authenticated': client_states[...]   │
│    })                                      │
└────────────────────────────────────────────┘
   │
   ▼
Frontend receives message
```

### New Flow (Modular)
```
Frontend
   │
   │ ws.send({"event": "get_status", "payload": {}})
   ▼
┌──────────────────────────────────────────────┐
│ app/sockets/routes.py                        │
│                                              │
│  @ws_bp.websocket('/ws')                     │
│  async def ws_endpoint():                    │
│                                              │
│    1. await ws.receive()                     │
│    2. envelope = Envelope.model_validate_json│
│       (message)  ✅ Pydantic validation      │
│    3. handler = get_handler(envelope.event)  │
│    4. await handler(envelope.payload, ...)   │
└──────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────┐
│ app/sockets/events.py                        │
│                                              │
│  registry = {                                │
│    "get_status": handle_get_status,          │
│    ...                                       │
│  }                                           │
│                                              │
│  def get_handler(event):                     │
│    return registry.get(event)                │
└──────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────┐
│ app/sockets/handlers/status.py               │
│                                              │
│  @on("get_status")  ✅ Decorator registration│
│  async def handle_get_status(payload,        │
│                               client_id,     │
│                               ws, mgr):      │
│                                              │
│    valorant_service = current_app.ctx.       │
│                       valorant               │
│    status = await valorant_service.          │
│             check_status()                   │
│                                              │
│    await mgr.send(ws, 'status_update', {     │
│      'backend_connected': True,              │
│      'valorant': status,                     │
│      'authenticated': mgr.state[client_id]   │
│                       .get('authenticated')  │
│    })                                        │
└──────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────┐
│ app/sockets/manager.py                       │
│                                              │
│  class ConnectionManager:                    │
│    async def send(self, ws, event, payload): │
│      await ws.send_json({                    │
│        "event": event,                       │
│        "payload": payload                    │
│      })                                      │
└──────────────────────────────────────────────┘
   │
   ▼
Frontend receives message
```

---

## Electron Integration Comparison

### Current (Brittle)
```javascript
// main.js
function startPythonBackend() {
  pythonProcess = spawn('pipenv', ['run', 'python', 'bootstrap.py'], {
    cwd: backendDir,
    shell: true,  // ❌ Makes PID tracking hard
    ...
  });
}

app.whenReady().then(() => {
  startPythonBackend();
  
  // ❌ Just wait 3 seconds and hope it's ready
  setTimeout(() => {
    createWindow();
  }, 3000);
});

// ❌ Unreliable cleanup
function forceKillBackendProcesses() {
  exec(`taskkill /f /fi "WINDOWTITLE eq bootstrap*"`, ...);
  exec(`wmic process where "commandline like '%bootstrap.py%'" delete`, ...);
}
```

### New (Robust)
```javascript
// main.js
const DEFAULT_PORT = 5888;

function startPythonBackend() {
  pythonProcess = spawn(pythonCommand, ['run.py'], {
    cwd: backendDir,
    shell: false,  // ✅ Direct spawn
    env: { ...process.env, PORT: String(DEFAULT_PORT) }
  });
  pythonProcessPid = pythonProcess.pid;
}

function waitForHealth(port, timeoutMs = 15000) {
  // ✅ Actually check if backend is ready
  return new Promise((resolve, reject) => {
    (function ping() {
      http.get(`http://127.0.0.1:${port}/health`, res => {
        if (res.statusCode === 200) return resolve();
        retry();
      }).on('error', retry);
      
      function retry() {
        if (Date.now() > deadline) {
          return reject(new Error('Backend timeout'));
        }
        setTimeout(ping, 300);
      }
    })();
  });
}

app.whenReady().then(async () => {
  startPythonBackend();
  
  try {
    await waitForHealth(DEFAULT_PORT);  // ✅ Wait for ready
    console.log('✅ Backend ready');
  } catch (e) {
    console.error('❌ Backend not ready');
  }
  
  createWindow();
});

// ✅ Clean, reliable cleanup
const kill = require('tree-kill');

function killPythonBackend() {
  if (pythonProcessPid) {
    kill(pythonProcessPid, 'SIGKILL');
  }
}
```

---

## Code Organization Comparison

### Current: One Giant File
```
bootstrap.py (1360 lines)
├── Imports (30 lines)
├── Globals (50 lines)
├── Cleanup functions (20 lines)
├── Signal handlers (10 lines)
├── ValorantAPI init (10 lines)
├── Heartbeat globals (10 lines)
├── WebSocket route (60 lines)
├── Event router (70 lines)
├── Heartbeat system (168 lines)
├── Event handlers (700 lines)  ❌ All mixed together
├── Utility functions (100 lines)
└── Main entry (10 lines)
```

### New: Many Small Files
```
app/
├── __init__.py (100 lines)
│   └── App factory, lifecycle
│
├── settings.py (30 lines)
│   └── Configuration
│
├── models/messages.py (50 lines)
│   └── Pydantic schemas
│
├── services/valorant.py (100 lines)
│   └── Valorant service wrapper
│
├── sockets/
│   ├── routes.py (50 lines)
│   │   └── WebSocket endpoint
│   │
│   ├── manager.py (150 lines)
│   │   └── Connection manager
│   │
│   ├── events.py (20 lines)
│   │   └── Event registry
│   │
│   └── handlers/
│       ├── status.py (40 lines)    ✅ Focused
│       ├── auth.py (60 lines)      ✅ Focused
│       ├── lobby.py (100 lines)    ✅ Focused
│       ├── queue.py (80 lines)     ✅ Focused
│       ├── match.py (200 lines)    ✅ Focused
│       ├── veto.py (80 lines)      ✅ Focused
│       └── chat.py (40 lines)      ✅ Focused
│
└── routes/health.py (10 lines)
    └── Health check

run.py (10 lines)
└── Entry point
```

---

## Testing Comparison

### Current (Hard to Test)
```python
# ❌ Can't test handlers in isolation
# ❌ Need to mock global state
# ❌ Need to mock WebSocket
# ❌ Need to simulate entire app context

def test_handle_get_status():
    # How do we test this? 
    # - Global active_connections
    # - Global client_states
    # - Global valorant_api
    # - Need real WebSocket?
    pass
```

### New (Easy to Test)
```python
# ✅ Easy unit tests
@pytest.mark.asyncio
async def test_get_status_handler():
    # Mock dependencies
    mock_ws = AsyncMock()
    mock_mgr = Mock()
    mock_mgr.state = {123: {'authenticated': True}}
    
    # Mock app context
    with patch('quart.current_app') as mock_app:
        mock_app.ctx.valorant.check_status = AsyncMock(
            return_value={'status': 'running'}
        )
        
        # Test handler
        await handle_get_status({}, 123, mock_ws, mock_mgr)
        
        # Verify
        mock_mgr.send.assert_called_once()

# ✅ Integration tests
@pytest.mark.asyncio
async def test_websocket_flow():
    app = create_app()
    client = app.test_client()
    
    async with client.websocket('/ws') as ws:
        msg = await ws.receive_json()
        assert msg['event'] == 'connected'
        
        await ws.send_json({
            'event': 'get_status',
            'payload': {}
        })
        
        response = await ws.receive_json()
        assert response['event'] == 'status_update'
```

---

## Adding a New Event Handler

### Current (Modify 3 Places)
```python
# 1. Add to handlers dict in bootstrap.py
handlers = {
    'existing_event': handle_existing,
    'new_event': handle_new_event,  # Add here
    ...
}

# 2. Implement handler in bootstrap.py (grows even larger)
async def handle_new_event(payload, client_id, ws):
    # Implementation
    # 40+ lines of code
    # Added to already huge file
    pass

# 3. Import any new dependencies at top of bootstrap.py
```

### New (One File, Auto-registered)
```python
# Create: app/sockets/handlers/my_feature.py

from ..events import on

@on("new_event")  # ✅ Auto-registered
async def handle_new_event(payload, client_id, ws, mgr):
    # Implementation
    # Isolated in its own file
    # Easy to find
    # Easy to test
    pass

# Import in app/sockets/handlers/__init__.py
from . import my_feature  # ✅ That's it!
```

---

## Summary Table

| Aspect | Current | New |
|--------|---------|-----|
| **Main file size** | 1360 lines | 100 lines |
| **Largest handler file** | 1360 lines (all in one) | 200 lines (match.py) |
| **Message validation** | None | Pydantic schemas |
| **State management** | Global variables | ConnectionManager |
| **Lifecycle** | atexit/signal | Quart hooks |
| **Health check** | None | /health endpoint |
| **Electron readiness** | 3s timeout | Health polling |
| **Process cleanup** | taskkill hacks | tree-kill |
| **Security** | nodeIntegration: true | contextIsolation |
| **Testability** | Hard | Easy |
| **Add new event** | Modify 3 places | Create 1 file |
| **Code duplication** | Moderate | Minimal |
| **Type safety** | None | Pydantic |
| **Error handling** | Ad-hoc | Structured |

---

## Migration Path

```
Current State           Phase 1              Phase 2              Phase 3              Final State
─────────────          ────────             ────────             ────────             ───────────

bootstrap.py    →   Create structure  →   Migrate handlers  →   Update Electron   →   Modular app
(1360 lines)        - app/                - status.py           - Health check        - Multiple files
                    - models/             - auth.py             - tree-kill           - Clean separation
clientapi.py        - services/           - queue.py            - preload.js          - Easy to maintain
(unchanged)         - sockets/            - match.py            - No shell
                    - routes/             - veto.py
pugapi.py                                 - chat.py
(unchanged)         Keep old code         - lobby.py
                    working
                                         Test each
                                         domain

                    2-3 hours            2-3 hours            2-3 hours             DONE!
```

---

**This refactor transforms a 1360-line monolith into a clean, modular, testable architecture while maintaining 100% backward compatibility during migration.**

