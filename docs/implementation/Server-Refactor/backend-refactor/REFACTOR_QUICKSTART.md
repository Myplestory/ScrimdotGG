# Backend Refactor Quick Start Guide

**Ready to begin? Follow this guide step-by-step.**

---

## Prerequisites

- [ ] Read `BACKEND_REFACTOR_PLAN.md`
- [ ] Read `ARCHITECTURE_COMPARISON.md`
- [ ] Understand current code structure
- [ ] Have test environment ready

---

## Step 0: Preparation (5 minutes)

```bash
# 1. Create feature branch
git checkout -b feature/backend-refactor

# 2. Backup current working code
cd client/backend
cp bootstrap.py bootstrap.py.backup

# 3. Create a commit point (safety)
git add .
git commit -m "Pre-refactor checkpoint: backup current working state"

# 4. Install dependencies (if needed)
pip install pydantic  # For message validation
```

---

## Step 1: Create Directory Structure (5 minutes)

```bash
cd client/backend

# Create all directories
mkdir -p app/models app/services app/sockets/handlers app/routes

# Create all files
touch app/__init__.py
touch app/settings.py
touch app/models/__init__.py
touch app/models/messages.py
touch app/services/__init__.py
touch app/services/valorant.py
touch app/sockets/__init__.py
touch app/sockets/routes.py
touch app/sockets/manager.py
touch app/sockets/events.py
touch app/sockets/handlers/__init__.py
touch app/sockets/handlers/status.py
touch app/sockets/handlers/auth.py
touch app/sockets/handlers/lobby.py
touch app/sockets/handlers/queue.py
touch app/sockets/handlers/match.py
touch app/sockets/handlers/veto.py
touch app/sockets/handlers/chat.py
touch app/routes/__init__.py
touch app/routes/health.py
touch run.py

# Verify structure
tree app/  # or ls -R app/ on Windows
```

Your structure should look like:
```
app/
├── __init__.py
├── settings.py
├── models/
│   ├── __init__.py
│   └── messages.py
├── services/
│   ├── __init__.py
│   └── valorant.py
├── sockets/
│   ├── __init__.py
│   ├── routes.py
│   ├── manager.py
│   ├── events.py
│   └── handlers/
│       ├── __init__.py
│       ├── status.py
│       ├── auth.py
│       ├── lobby.py
│       ├── queue.py
│       ├── match.py
│       ├── veto.py
│       └── chat.py
└── routes/
    ├── __init__.py
    └── health.py
```

---

## Step 2: Core Foundation Files (30 minutes)

### 2.1: Settings (`app/settings.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 1.2

### 2.2: Message Schemas (`app/models/messages.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 1.3

### 2.3: Event Registry (`app/sockets/events.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 1.5

### 2.4: ConnectionManager (`app/sockets/manager.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 1.4

### 2.5: ValorantService (`app/services/valorant.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 2.6

### 2.6: Health Route (`app/routes/health.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 2.5

---

## Step 3: Test Foundation (10 minutes)

### 3.1: Create Minimal App (`app/__init__.py`)
```python
"""Minimal app for testing foundation."""
from quart import Quart
from quart_cors import cors
from . import settings
from .routes.health import health_bp

def create_app() -> Quart:
    app = Quart(__name__)
    
    app = cors(
        app,
        allow_origin=settings.CORS_ORIGIN,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True
    )
    
    app.register_blueprint(health_bp)
    
    return app
```

### 3.2: Create Entry Point (`run.py`)
```python
"""Entry point."""
from app import create_app
from app import settings

if __name__ == '__main__':
    app = create_app()
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

### 3.3: Test It
```bash
# Terminal 1: Start backend
python run.py

# Terminal 2: Test health endpoint
curl http://localhost:5888/health
# Should return: {"ok":true,"status":"healthy"}
```

✅ **If health check works, foundation is solid. Proceed to handlers.**

---

## Step 4: Migrate Handlers (2 hours)

### Order of Migration:
1. Status handlers (simple, no dependencies)
2. Auth handlers (moderate complexity)
3. Queue handlers
4. Match handlers (most complex)
5. Veto handlers
6. Chat handlers
7. Lobby handlers

### 4.1: Status Handlers (`app/sockets/handlers/status.py`)

Copy this code:
```python
"""Status and connection event handlers."""
from quart import current_app
from ..events import on

@on("connected")
async def handle_connected(payload: dict, client_id: int, ws, mgr):
    """Handle client connection."""
    print(f"[CONNECT] Client {client_id} connected")
    
    valorant_service = current_app.ctx.valorant
    status = await valorant_service.check_status()
    
    await mgr.send(ws, 'status_update', {
        'backend_connected': True,
        'valorant': status,
        'authenticated': mgr.state[client_id].get('authenticated', False)
    })

@on("get_status")
async def handle_get_status(payload: dict, client_id: int, ws, mgr):
    """Get current system status."""
    valorant_service = current_app.ctx.valorant
    status = await valorant_service.check_status()
    
    await mgr.send(ws, 'status_update', {
        'backend_connected': True,
        'valorant': status,
        'authenticated': mgr.state[client_id].get('authenticated', False)
    })
```

### 4.2: Import Pattern for Remaining Handlers

For each handler file:
1. Open corresponding section in `BACKEND_REFACTOR_PLAN.md`
2. Find the handler code (Step 2.1 - 2.3)
3. Copy implementation
4. Import in `app/sockets/handlers/__init__.py`:

```python
# app/sockets/handlers/__init__.py
"""Import all handlers to register them."""
from . import status
from . import auth
from . import queue
from . import match
from . import veto
from . import chat
from . import lobby
```

### 4.3: Handler Checklist

Copy each handler from the plan:
- [ ] `app/sockets/handlers/status.py` → 2 handlers
- [ ] `app/sockets/handlers/auth.py` → 2 handlers
- [ ] `app/sockets/handlers/queue.py` → 2 handlers
- [ ] `app/sockets/handlers/match.py` → 10+ handlers
- [ ] `app/sockets/handlers/veto.py` → 4 handlers
- [ ] `app/sockets/handlers/chat.py` → 2 handlers
- [ ] `app/sockets/handlers/lobby.py` → 7 handlers

**Note:** For match.py, lobby.py - these are longer. Reference the full plan or extract from `bootstrap.py` and adapt to the new pattern.

---

## Step 5: WebSocket Route & App Factory (30 minutes)

### 5.1: WebSocket Route (`app/sockets/routes.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 2.4

### 5.2: Complete App Factory (`app/__init__.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 2.7

### 5.3: Update Entry Point (`run.py`)
Copy from `BACKEND_REFACTOR_PLAN.md` → Step 2.8

---

## Step 6: Test New Backend (30 minutes)

```bash
# Start new backend
python run.py

# Should see:
# ============================================================
# Starting Scrim.GG Client Service
# ============================================================
# WebSocket server: ws://127.0.0.1:5888/ws
# Health check: http://127.0.0.1:5888/health
# Ready to connect to Valorant
# ============================================================
```

### Manual Test Checklist:
- [ ] Health endpoint works
- [ ] WebSocket connects
- [ ] Status event works
- [ ] Auth works (if Valorant running)
- [ ] Queue works
- [ ] All events from frontend work

**If tests pass, backend is working!**

---

## Step 7: Update Electron (1 hour)

### 7.1: Install tree-kill
```bash
cd client/frontend
npm install tree-kill
```

### 7.2: Update main.js

Add at top:
```javascript
const http = require('http');
const kill = require('tree-kill');
const DEFAULT_PORT = 5888;
```

Replace `startPythonBackend()` function with version from `BACKEND_REFACTOR_PLAN.md` → Step 3.1

Add `waitForHealth()` function from `BACKEND_REFACTOR_PLAN.md` → Step 3.1

Update `app.whenReady()` with version from `BACKEND_REFACTOR_PLAN.md` → Step 3.1

Update `killPythonBackend()` with version from `BACKEND_REFACTOR_PLAN.md` → Step 3.2

### 7.3: Test Electron
```bash
# Start React dev server (if not running)
npm start

# Start Electron
npm run electron
```

**Verify:**
- [ ] Electron waits for backend health check
- [ ] Window appears after backend ready
- [ ] Frontend connects to WebSocket
- [ ] All functionality works
- [ ] Clean shutdown (no orphaned processes)

---

## Step 8: Security (Optional, 30 minutes)

### 8.1: Create Preload Script
```bash
cd client/frontend
touch preload.js
```

Copy content from `BACKEND_REFACTOR_PLAN.md` → Step 3.3

### 8.2: Update main.js
Update `BrowserWindow` config with version from plan → Step 3.3

### 8.3: Update Frontend
In your React app, use `window.electronAPI` instead of direct Node.js

---

## Step 9: Cleanup (30 minutes)

### 9.1: Remove Old Code
```bash
# Only after everything works!
cd client/backend
rm bootstrap.py
# Keep bootstrap.py.backup for now
```

### 9.2: Update Documentation
- [ ] Update README.md
- [ ] Document new structure
- [ ] Update development guide

### 9.3: Commit
```bash
git add .
git commit -m "feat: Refactor backend to modular architecture

- Split monolithic bootstrap.py into focused modules
- Add Pydantic message validation
- Implement ConnectionManager for state management
- Add health check endpoint for Electron
- Improve process lifecycle management
- Update Electron integration with health polling
- Add security hardening (preload script)"
```

---

## Step 10: Review & Merge (1 hour)

### 10.1: Final Tests
- [ ] Run full manual test suite
- [ ] Test on different platforms (Windows/Mac/Linux)
- [ ] Performance test (memory, CPU)
- [ ] Load test (multiple connections)

### 10.2: Code Review
- [ ] Review code quality
- [ ] Check for TODOs
- [ ] Verify documentation
- [ ] Run linter

### 10.3: Merge
```bash
git push origin feature/backend-refactor
# Create pull request
# Get team review
# Merge to main
```

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install pydantic quart quart-cors websockets

# Check imports
python -c "from app import create_app; app = create_app()"
```

### Health check fails
```bash
# Check if server is running
curl http://localhost:5888/health

# Check logs
python run.py  # Look for errors

# Check port
netstat -an | grep 5888  # Is it bound?
```

### Electron doesn't connect
```javascript
// In main.js, add debug logging
console.log('Waiting for health check...');
await waitForHealth(DEFAULT_PORT);
console.log('Health check passed!');
```

### WebSocket events not working
```python
# In app/sockets/handlers/__init__.py
# Make sure all handlers are imported

# Check event registry
# Add debug in routes.py:
print(f"Available events: {list(registry.keys())}")
```

---

## Quick Reference: File Locations

| What | Where | Lines |
|------|-------|-------|
| Settings | `app/settings.py` | 30 |
| Schemas | `app/models/messages.py` | 50 |
| Manager | `app/sockets/manager.py` | 150 |
| Events | `app/sockets/events.py` | 20 |
| Routes | `app/sockets/routes.py` | 50 |
| Health | `app/routes/health.py` | 10 |
| App Factory | `app/__init__.py` | 100 |
| Service | `app/services/valorant.py` | 100 |
| Handlers | `app/sockets/handlers/*.py` | 40-200 each |
| Entry | `run.py` | 10 |

---

## Time Estimates

| Phase | Task | Time |
|-------|------|------|
| 0 | Preparation | 5 min |
| 1 | Directory structure | 5 min |
| 2 | Core foundation | 30 min |
| 3 | Test foundation | 10 min |
| 4 | Migrate handlers | 2 hours |
| 5 | WebSocket route | 30 min |
| 6 | Test backend | 30 min |
| 7 | Update Electron | 1 hour |
| 8 | Security (optional) | 30 min |
| 9 | Cleanup | 30 min |
| 10 | Review & merge | 1 hour |
| **Total** | | **6-8 hours** |

---

## Success Checklist

✅ **Refactor is complete when:**

- [ ] All handlers migrated from bootstrap.py
- [ ] WebSocket events work identically
- [ ] Health check endpoint works
- [ ] Electron waits for backend readiness
- [ ] Process cleanup is clean
- [ ] No orphaned processes
- [ ] Security hardened (preload script)
- [ ] Code is modular (max 200 lines per file)
- [ ] Documentation updated
- [ ] Tests pass
- [ ] Team approves
- [ ] Merged to main

---

## Next Steps After Refactor

With the modular architecture in place, you can now easily:

1. **Add new events:** Just create a handler file with `@on()` decorator
2. **Write tests:** Each handler is easily testable in isolation
3. **Scale:** Add more services, more routes, more features
4. **Monitor:** Add metrics, logging, tracing
5. **Optimize:** Profile individual handlers, optimize bottlenecks
6. **Document:** Auto-generate API docs from Pydantic schemas

---

**Ready? Start with Step 0! Good luck! 🚀**

If you get stuck, refer back to:
- `BACKEND_REFACTOR_PLAN.md` for detailed code
- `ARCHITECTURE_COMPARISON.md` for understanding the changes
- `REFACTOR_CHECKLIST.md` for the full checklist

