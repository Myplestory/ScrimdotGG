# Backend Refactoring Checklist

Quick reference for implementing the modular backend architecture.

## Pre-Flight

- [ ] Create feature branch: `git checkout -b feature/backend-refactor`
- [ ] Backup current working code: `cp bootstrap.py bootstrap.py.backup`
- [ ] Read the full plan: `docs/BACKEND_REFACTOR_PLAN.md`

---

## Phase 1: Foundation (2-3 hours)

### File Structure
- [ ] Create `app/` directory structure
- [ ] Create `app/models/` directory
- [ ] Create `app/services/` directory
- [ ] Create `app/sockets/` directory
- [ ] Create `app/sockets/handlers/` directory
- [ ] Create `app/routes/` directory

### Core Files
- [ ] Implement `app/settings.py`
- [ ] Implement `app/models/messages.py` (Pydantic schemas)
- [ ] Implement `app/sockets/manager.py` (ConnectionManager)
- [ ] Implement `app/sockets/events.py` (Event registry)
- [ ] Implement `app/services/valorant.py` (ValorantService wrapper)
- [ ] Implement `app/routes/health.py` (Health endpoint)

### Test Foundation
- [ ] Start Python backend: `python run.py`
- [ ] Test health endpoint: `curl http://localhost:5888/health`
- [ ] Verify ConnectionManager initializes
- [ ] Verify ValorantService initializes

---

## Phase 2: Handler Migration (2-3 hours)

### Status Handlers
- [ ] Implement `app/sockets/handlers/status.py`
  - [ ] `@on("connected")`
  - [ ] `@on("get_status")`
- [ ] Test status events work

### Auth Handlers
- [ ] Implement `app/sockets/handlers/auth.py`
  - [ ] `@on("authenticate")`
  - [ ] `@on("get_initial_state")`
- [ ] Test authentication flow

### Queue Handlers
- [ ] Implement `app/sockets/handlers/queue.py`
  - [ ] `@on("join_pug_queue")`
  - [ ] `@on("leave_pug_queue")`
- [ ] Test queue join/leave

### Match Handlers
- [ ] Implement `app/sockets/handlers/match.py`
  - [ ] `@on("accept_match")`
  - [ ] `@on("decline_match")`
  - [ ] `@on("match_started")`
  - [ ] `@on("match_ended")`
  - [ ] `@on("match_starting")`
  - [ ] `@on("join_custom_game")`
  - [ ] `@on("match_in_progress")`
  - [ ] `@on("match_score_update")`
  - [ ] `@on("match_completed")`
  - [ ] `@on("pug_match_found")`
  - [ ] `@on("match_found")`
  - [ ] `@on("teams_assigned")`
  - [ ] `@on("map_selected")`
- [ ] Test match lifecycle

### Veto Handlers
- [ ] Implement `app/sockets/handlers/veto.py`
  - [ ] `@on("veto_map")`
  - [ ] `@on("veto_update")`
  - [ ] `@on("veto_complete")`
  - [ ] `@on("veto_acknowledged")`
- [ ] Test veto system

### Chat Handlers
- [ ] Implement `app/sockets/handlers/chat.py`
  - [ ] `@on("lobby_chat")`
  - [ ] `@on("direct_message")`
- [ ] Test chat functionality

### Lobby Handlers
- [ ] Implement `app/sockets/handlers/lobby.py`
  - [ ] `@on("create_lobby")`
  - [ ] `@on("join_lobby")`
  - [ ] `@on("leave_lobby")`
  - [ ] `@on("queue_lobby")`
  - [ ] `@on("dequeue_lobby")`
  - [ ] `@on("get_player_data")`
  - [ ] `@on("get_match_data")`
- [ ] Test lobby operations

### Handler Registry
- [ ] Create `app/sockets/handlers/__init__.py`
- [ ] Import all handler modules to register events
- [ ] Verify all events are registered

### WebSocket Route
- [ ] Implement `app/sockets/routes.py`
- [ ] Test WebSocket connection
- [ ] Test message routing
- [ ] Test error handling

### App Factory
- [ ] Implement `app/__init__.py`
- [ ] Register blueprints
- [ ] Add startup hooks
- [ ] Add shutdown hooks
- [ ] Test lifecycle

### Entry Point
- [ ] Implement `run.py`
- [ ] Test server starts
- [ ] Test graceful shutdown

---

## Phase 3: Electron Integration (2-3 hours)

### Health Check
- [ ] Install `tree-kill`: `npm install tree-kill`
- [ ] Implement `waitForHealth()` function in main.js
- [ ] Update `startPythonBackend()` to use `run.py`
- [ ] Update `app.whenReady()` to wait for health
- [ ] Test Electron waits for backend

### Process Management
- [ ] Implement improved `killPythonBackend()`
- [ ] Use `tree-kill` for cross-platform cleanup
- [ ] Remove `shell: true` from spawn
- [ ] Test process cleanup on Windows
- [ ] Test process cleanup on macOS/Linux

### Security Hardening
- [ ] Create `client/frontend/preload.js`
- [ ] Update BrowserWindow to use preload
- [ ] Set `nodeIntegration: false`
- [ ] Set `contextIsolation: true`
- [ ] Expose safe API via contextBridge
- [ ] Test renderer can still call closeApp/fadeInWindow

### Port Configuration
- [ ] Set DEFAULT_PORT in main.js
- [ ] Pass PORT via environment to Python
- [ ] Read PORT in Python settings.py
- [ ] Test port configuration works

---

## Phase 4: Testing (2-3 hours)

### Unit Tests
- [ ] Write tests for ConnectionManager
- [ ] Write tests for event handlers
- [ ] Write tests for ValorantService
- [ ] Run all unit tests

### Integration Tests
- [ ] Test WebSocket connection
- [ ] Test authentication flow
- [ ] Test queue operations
- [ ] Test match lifecycle
- [ ] Test veto system
- [ ] Test chat system

### Manual Testing
- [ ] Start Electron app
- [ ] Verify window appears after backend ready
- [ ] Connect to WebSocket
- [ ] Authenticate with Valorant
- [ ] Join PUG queue
- [ ] Accept match (if found)
- [ ] Test veto system
- [ ] Test chat
- [ ] Test graceful shutdown
- [ ] Verify no orphaned processes

### Performance Testing
- [ ] Monitor memory usage
- [ ] Check heartbeat CPU usage
- [ ] Verify no memory leaks
- [ ] Test with multiple reconnections

---

## Phase 5: Cleanup & Documentation (1-2 hours)

### Code Cleanup
- [ ] Remove old `bootstrap.py` (after backup)
- [ ] Remove unused imports
- [ ] Add docstrings to all functions
- [ ] Add type hints
- [ ] Format code (black/autopep8)
- [ ] Run linter

### Documentation
- [ ] Update README.md
- [ ] Document new architecture
- [ ] Document how to add new event handlers
- [ ] Document testing procedures
- [ ] Update development setup guide

### Git
- [ ] Commit changes with clear messages
- [ ] Push feature branch
- [ ] Create pull request
- [ ] Request code review

---

## Rollback (if needed)

- [ ] Switch main.js entry point back to bootstrap.py
- [ ] Restore bootstrap.py.backup
- [ ] Remove app/ directory
- [ ] Restart application

---

## Success Metrics

✅ **Checklist is complete when:**

- [ ] All WebSocket events work as before
- [ ] Electron reliably starts backend
- [ ] Health check works on all platforms
- [ ] Process cleanup is clean
- [ ] No orphaned processes
- [ ] Code is modular and testable
- [ ] Documentation is updated
- [ ] Tests pass
- [ ] Team approves

---

## Quick Commands

```bash
# Start backend (old way)
cd client/backend
python bootstrap.py

# Start backend (new way)
cd client/backend
python run.py

# Test health endpoint
curl http://localhost:5888/health

# Start Electron
cd client/frontend
npm start

# Run tests
cd client/backend
pytest tests/

# Format code
cd client/backend
black app/

# Run linter
cd client/backend
flake8 app/
```

---

**Estimated Total Time:** 8-12 hours  
**Recommended Approach:** One phase per day, with thorough testing after each phase.

