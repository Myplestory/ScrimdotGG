# Backend Refactoring Plan
## From Monolithic to Modular Quart Architecture

**Status:** Draft - Ready for Review  
**Author:** Architecture Improvement Recommendations  
**Date:** October 13, 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Target Architecture](#target-architecture)
4. [Migration Strategy](#migration-strategy)
5. [Step-by-Step Implementation](#step-by-step-implementation)
6. [Testing & Validation](#testing--validation)
7. [Rollback Plan](#rollback-plan)
8. [Electron Integration Updates](#electron-integration-updates)

---

## Executive Summary

### Goals
- **Modularity:** Split monolithic `bootstrap.py` (1360 lines) into focused, testable modules
- **Maintainability:** Separate concerns (routing, state, business logic, lifecycle)
- **Robustness:** Add health checks, graceful shutdown, message validation
- **Electron Integration:** Improve process management, readiness detection, and security

### Key Benefits
- ✅ Easier to test individual components
- ✅ Clearer separation of concerns
- ✅ Better error handling and logging
- ✅ Safer Electron process lifecycle
- ✅ Foundation for future scaling

### Estimated Effort
- **Phase 1 (Core Refactor):** 4-6 hours
- **Phase 2 (Electron Updates):** 2-3 hours
- **Phase 3 (Testing & Polish):** 2-3 hours
- **Total:** 8-12 hours

---

## Current State Analysis

### Existing Structure
```
client/backend/
├── bootstrap.py          # 1360 lines - EVERYTHING
├── clientapi.py          # 663 lines - ValorantAPI + Django WS client
├── pugapi.py             # 354 lines - PugSocketClient
├── auth.py               # Auth utilities
├── data/                 # Static data (maps, servers)
└── valclient/            # Valorant client library
```

### Current Issues

#### 1. **bootstrap.py is doing too much:**
- WebSocket routing (87 lines)
- Heartbeat system (168 lines)
- 40+ event handlers (700+ lines)
- Connection state management
- Lifecycle management (atexit/signal)
- Utility functions

#### 2. **Tight coupling:**
- Handlers directly access global state (`active_connections`, `client_states`)
- Business logic mixed with routing
- Django WS callbacks use closures and `_pending_*` fields

#### 3. **No validation:**
- Raw JSON parsing without schema validation
- No type safety on messages

#### 4. **Lifecycle management:**
- Uses `atexit` and `signal` handlers (unreliable)
- No Quart lifecycle hooks
- Electron manages process poorly (shell=true, no health checks)

#### 5. **Testing challenges:**
- Hard to test individual handlers
- Global state makes unit tests difficult
- No separation of concerns

---

## Target Architecture

### New Structure
```
client/backend/
├── app/
│   ├── __init__.py              # Quart app factory + lifecycle hooks
│   ├── settings.py              # Configuration/environment
│   │
│   ├── models/
│   │   └── messages.py          # Pydantic message schemas
│   │
│   ├── services/
│   │   └── valorant.py          # Async facade over ValorantAPI
│   │
│   ├── sockets/
│   │   ├── routes.py            # Tiny /ws endpoint
│   │   ├── manager.py           # ConnectionManager (state + send/broadcast)
│   │   ├── events.py            # Event registry (decorator pattern)
│   │   │
│   │   └── handlers/
│   │       ├── __init__.py
│   │       ├── status.py        # Status/connection handlers
│   │       ├── auth.py          # Authentication handlers
│   │       ├── lobby.py         # Lobby operations
│   │       ├── queue.py         # Queue/matchmaking
│   │       ├── match.py         # Match lifecycle
│   │       ├── veto.py          # Veto system
│   │       └── chat.py          # Chat/messaging
│   │
│   └── routes/
│       └── health.py            # Health check endpoint for Electron
│
├── run.py                       # Entry point (replaces bootstrap.py)
├── clientapi.py                 # [Keep as-is for now]
├── pugapi.py                    # [Keep as-is for now]
├── auth.py                      # [Keep as-is]
├── data/                        # [Keep as-is]
└── Pipfile                      # [Keep as-is]
```

### Key Components

#### 1. **App Factory** (`app/__init__.py`)
- Creates Quart app
- Registers blueprints
- Sets up lifecycle hooks (startup/shutdown)
- Initializes ConnectionManager and ValorantAPI

#### 2. **ConnectionManager** (`app/sockets/manager.py`)
- Manages active connections (`Set[Websocket]`)
- Stores client state (`Dict[int, dict]`)
- Provides `send()` and `broadcast()` APIs
- Runs heartbeat loop
- Handles graceful shutdown

#### 3. **Event Registry** (`app/sockets/events.py`)
- Decorator-based event registration
- Maps event names to handler functions
- Clean, declarative API

#### 4. **Message Validation** (`app/models/messages.py`)
- Pydantic schemas for incoming/outgoing messages
- Early validation of payloads
- Type safety

#### 5. **Small Handlers** (`app/sockets/handlers/`)
- Each handler is 10-50 lines
- Domain-grouped (auth, lobby, match, etc.)
- Easy to test and maintain

#### 6. **Health Endpoint** (`app/routes/health.py`)
- Simple `/health` route
- Returns `{"ok": true}` when ready
- Used by Electron for readiness detection

---

## Migration Strategy

### Principles
1. **Incremental:** Migrate one module at a time
2. **Backward Compatible:** Keep old code working during migration
3. **Testable:** Write tests as we refactor
4. **Reversible:** Easy to rollback if issues arise

### Migration Order
1. ✅ Create new structure (folders, files)
2. ✅ Extract message schemas
3. ✅ Build ConnectionManager
4. ✅ Create event registry
5. ✅ Migrate handlers (one domain at a time)
6. ✅ Replace WebSocket route
7. ✅ Add lifecycle hooks
8. ✅ Add health endpoint
9. ✅ Update Electron integration
10. ✅ Remove old code

---

## Step-by-Step Implementation

### Phase 1: Foundation (2-3 hours)

#### Step 1.1: Create Directory Structure
```bash
cd client/backend
mkdir -p app/models app/services app/sockets/handlers app/routes
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
```

#### Step 1.2: Settings Module (`app/settings.py`)
```python
"""
Application settings and configuration.
"""
import os

# Server settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5888"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# CORS settings
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:3000")

# Django backend settings
DJANGO_WS_URL = os.getenv("DJANGO_WS_URL", "ws://localhost:8000/ws/matchmaking/")
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://127.0.0.1:8000")

# Heartbeat settings
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "3"))

# Timeouts
PLAYER_MODEL_TIMEOUT = int(os.getenv("PLAYER_MODEL_TIMEOUT", "5"))
LOBBY_CREATION_TIMEOUT = int(os.getenv("LOBBY_CREATION_TIMEOUT", "5"))
```

#### Step 1.3: Message Schemas (`app/models/messages.py`)
```python
"""
Pydantic models for WebSocket message validation.
"""
from pydantic import BaseModel, Field
from typing import Any, Optional

class Envelope(BaseModel):
    """Standard message envelope for all WebSocket communication."""
    event: str = Field(..., description="Event type/name")
    payload: Optional[Any] = Field(default=None, description="Event payload")

class ErrorResponse(BaseModel):
    """Standard error response."""
    message: str
    code: Optional[str] = None

class StatusUpdate(BaseModel):
    """Status update payload."""
    backend_connected: bool
    valorant: dict
    authenticated: bool

class MatchFoundPayload(BaseModel):
    """Match found notification."""
    match_id: str
    match_confirmation_id: str
    timeout_seconds: int = 30
    message: str = "Match found! Please accept to continue."
```

#### Step 1.4: ConnectionManager (`app/sockets/manager.py`)
```python
"""
WebSocket connection manager.
Handles connection lifecycle, state, and broadcasting.
"""
from __future__ import annotations
import asyncio
import contextlib
from typing import Dict, Set, Any
from quart import Websocket

class ConnectionManager:
    def __init__(self):
        self.active: Set[Websocket] = set()
        self.state: Dict[int, dict] = {}
        self._last_status: dict | None = None
        self._heartbeat_task: asyncio.Task | None = None
    
    def add(self, ws: Websocket) -> int:
        """Add a new WebSocket connection."""
        cid = id(ws)
        self.active.add(ws)
        self.state[cid] = {
            'puuid': None,
            'authenticated': False,
            'in_game': False,
            'in_queue': False,
            'lobby_id': None,
            'match_id': None,
            'connected': True,
            'websocket': ws,
        }
        print(f"[CONN] Added client {cid}. Total: {len(self.active)}")
        return cid
    
    async def remove(self, ws: Websocket):
        """Remove a WebSocket connection."""
        cid = id(ws)
        self.active.discard(ws)
        removed_state = self.state.pop(cid, None)
        print(f"[CONN] Removed client {cid}. Total: {len(self.active)}")
        return removed_state
    
    async def send(self, ws: Websocket, event: str, payload: Any = None):
        """Send a message to a specific WebSocket."""
        try:
            await ws.send_json({"event": event, "payload": payload})
        except Exception as e:
            print(f"[SEND] Error sending to client: {e}")
            await self.remove(ws)
    
    async def broadcast(self, event: str, payload: Any = None):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for ws in list(self.active):
            try:
                await self.send(ws, event, payload)
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            await self.remove(ws)
    
    async def broadcast_with_client_context(self, event: str, base_payload: dict):
        """
        Broadcast with per-client customization.
        Used for status updates that include client-specific auth state.
        """
        disconnected = []
        for ws in list(self.active):
            try:
                cid = id(ws)
                client_payload = base_payload.copy()
                
                # Add client-specific fields
                if 'authenticated' in client_payload and client_payload['authenticated'] is None:
                    client_payload['authenticated'] = self.state[cid].get('authenticated', False)
                
                await self.send(ws, event, client_payload)
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            await self.remove(ws)
    
    async def start_heartbeat(self, valorant_service):
        """Start the heartbeat monitoring loop."""
        print("[HEARTBEAT] Starting...")
        
        try:
            while True:
                # Check if any clients are connected
                if not self.active:
                    await asyncio.sleep(3)
                    continue
                
                try:
                    # Get Valorant status
                    current_status = await valorant_service.check_status()
                    
                    # Only broadcast if status changed
                    if current_status != self._last_status:
                        print(f"[HEARTBEAT] Status changed: {self._last_status} -> {current_status}")
                        self._last_status = current_status
                        
                        await self.broadcast_with_client_context('status_update', {
                            'backend_connected': True,
                            'valorant': current_status,
                            'authenticated': None  # Will be set per client
                        })
                    
                    # Drain pending events from Django WS
                    await self._drain_pending_events(valorant_service)
                    
                except Exception as e:
                    print(f"[HEARTBEAT] Error: {e}")
                
                await asyncio.sleep(3)
                
        except asyncio.CancelledError:
            print("[HEARTBEAT] Stopped")
            raise
    
    async def _drain_pending_events(self, valorant_service):
        """Forward pending events from ValorantAPI to frontend clients."""
        pending_events = [
            ('_pending_match_data', 'pug_match_found'),
            ('_pending_player_accepted_data', 'player_accepted'),
            ('_pending_match_ready_data', 'match_ready'),
            ('_pending_match_confirmed_data', 'match_confirmed'),
            ('_pending_veto_started_data', 'veto_started'),
            ('_pending_match_data_response', 'match_data'),
            ('_pending_veto_update_data', 'veto_update'),
            ('_pending_veto_complete_data', 'veto_complete'),
            ('_pending_veto_acknowledged_data', 'veto_acknowledged'),
        ]
        
        for attr_name, event_name in pending_events:
            data = getattr(valorant_service.api, attr_name, None)
            if data:
                setattr(valorant_service.api, attr_name, None)
                await self.broadcast(event_name, data)
                print(f"[HEARTBEAT] Broadcasted {event_name}")
    
    async def close_all(self):
        """Close all connections gracefully."""
        print("[CONN] Closing all connections...")
        for ws in list(self.active):
            with contextlib.suppress(Exception):
                await ws.close()
        self.active.clear()
        self.state.clear()
```

#### Step 1.5: Event Registry (`app/sockets/events.py`)
```python
"""
Event registry for WebSocket handlers.
Provides decorator-based event registration.
"""
from typing import Callable, Awaitable, Dict

# Type alias for handler functions
Handler = Callable[[dict, int, "Websocket", "ConnectionManager"], Awaitable[None]]

# Global registry
registry: Dict[str, Handler] = {}

def on(event: str):
    """
    Decorator to register a handler for a specific event.
    
    Usage:
        @on("get_status")
        async def handle_get_status(payload, client_id, ws, mgr):
            # handler logic
    """
    def wrapper(fn: Handler):
        registry[event] = fn
        print(f"[REGISTRY] Registered handler for '{event}'")
        return fn
    return wrapper

def get_handler(event: str) -> Handler | None:
    """Get a handler for a specific event."""
    return registry.get(event)
```

### Phase 2: Handler Migration (2-3 hours)

#### Step 2.1: Status Handlers (`app/sockets/handlers/status.py`)
```python
"""
Status and connection event handlers.
"""
from quart import current_app
from ..events import on

@on("connected")
async def handle_connected(payload: dict, client_id: int, ws, mgr):
    """Handle client connection - send initial status."""
    print(f"[CONNECT] Client {client_id} connected")
    
    # Get initial status
    valorant_service = current_app.ctx.valorant
    status = await valorant_service.check_status()
    
    await mgr.send(ws, 'status_update', {
        'backend_connected': True,
        'valorant': status,
        'authenticated': mgr.state[client_id].get('authenticated', False)
    })
    
    # Start heartbeat if not running
    if not mgr.state[client_id].get('in_game', False):
        # Heartbeat is managed by app lifecycle, always running

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

#### Step 2.2: Auth Handlers (`app/sockets/handlers/auth.py`)
```python
"""
Authentication event handlers.
"""
from quart import current_app
from ..events import on

@on("authenticate")
async def handle_authenticate(payload: dict, client_id: int, ws, mgr):
    """Authenticate with local Valorant client."""
    print("[AUTH] Authenticating with Valorant client...")
    
    valorant_service = current_app.ctx.valorant
    
    # Check if Valorant is running
    status = await valorant_service.check_status()
    if status['status'] != 'running':
        error_messages = {
            'riot_only': 'Please launch Valorant game (Riot Client is running but game is not)',
            'not_running': 'Riot Client is not running. Please start Valorant.',
        }
        message = error_messages.get(status['status'], status.get('message', 'Unable to authenticate'))
        
        await mgr.send(ws, 'authentication_error', {'message': message, 'timeout': 5})
        return
    
    # Get region from payload
    region = payload.get('region', 'na')
    print(f"[AUTH] Using region: {region}")
    
    result = await valorant_service.login(region)
    
    if result.get('status') == 'success':
        # Update client state
        mgr.state[client_id]['authenticated'] = True
        mgr.state[client_id]['puuid'] = valorant_service.api.client.puuid
        mgr.state[client_id]['in_game'] = False
        
        # Get player data
        player_result = await valorant_service.get_player_model()
        
        await mgr.send(ws, 'authentication_success', {
            'puuid': valorant_service.api.client.puuid,
            'player_data': player_result.get('data', {})
        })
    else:
        # Handle region mismatch or other errors
        if 'error' in result and 'status_code' in result:
            await mgr.send(ws, 'authentication_error', {
                'message': f'Region mismatch! You selected {region.upper()}, but your Valorant client is in a different region.',
                'timeout': 10
            })
        else:
            await mgr.send(ws, 'error', {'message': "Valorant authentication failed. Is Valorant running?"})

@on("get_initial_state")
async def handle_get_initial_state(payload: dict, client_id: int, ws, mgr):
    """Get current state after reconnect or refresh."""
    if not mgr.state[client_id]['authenticated']:
        await mgr.send(ws, 'not_authenticated', {})
        return
    
    valorant_service = current_app.ctx.valorant
    result = await valorant_service.get_player_model()
    
    await mgr.send(ws, 'initial_state', {
        'player_data': result.get('data'),
        'lobby_id': mgr.state[client_id].get('lobby_id'),
        'match_id': mgr.state[client_id].get('match_id'),
    })
```

#### Step 2.3: Queue Handlers (`app/sockets/handlers/queue.py`)
```python
"""
Queue and matchmaking event handlers.
"""
from quart import current_app
from ..events import on

@on("join_pug_queue")
async def handle_join_pug_queue(payload: dict, client_id: int, ws, mgr):
    """Player joins PUG queue."""
    if not mgr.state[client_id]['authenticated']:
        await mgr.send(ws, 'error', {'message': 'Not authenticated'})
        return
    
    valorant_service = current_app.ctx.valorant
    puuid = mgr.state[client_id]['puuid']
    
    # Create lobby
    print(f"[PUG QUEUE] Creating lobby for player {puuid}")
    create_result = await valorant_service.create_lobby()
    
    if not create_result or create_result.get('status') != 'success':
        await mgr.send(ws, 'error', {'message': 'Failed to create/get lobby'})
        return
    
    lobby_id = create_result['data']['id']
    
    # Update preferences if provided
    if payload.get('preferred_maps'):
        await valorant_service.api.pugsocket.send_message('update_lobby_preferences', {
            'lobby_id': lobby_id,
            'requester_puuid': puuid,
            'map_preferences': payload['preferred_maps'],
            'server_preferences': payload.get('preferred_servers', [])
        })
    
    # Join queue
    await valorant_service.api.pugsocket.send_message('add_lobby_to_queue', {
        'lobby_id': lobby_id,
        'requester_puuid': puuid,
        'queue_type': payload.get('queue_type', 'pug')
    })
    
    # Update state
    mgr.state[client_id]['in_queue'] = True
    mgr.state[client_id]['lobby_id'] = lobby_id
    
    await mgr.send(ws, 'queue_joined', {
        'queue_type': payload.get('queue_type', 'pug'),
        'estimated_wait': 60
    })

@on("leave_pug_queue")
async def handle_leave_pug_queue(payload: dict, client_id: int, ws, mgr):
    """Player leaves PUG queue."""
    if not mgr.state[client_id]['authenticated']:
        await mgr.send(ws, 'error', {'message': 'Not authenticated'})
        return
    
    lobby_id = mgr.state[client_id].get('lobby_id')
    if not lobby_id:
        await mgr.send(ws, 'error', {'message': 'No lobby found to leave'})
        return
    
    valorant_service = current_app.ctx.valorant
    await valorant_service.api.pugsocket.send_message('remove_lobby_from_queue', {
        'lobby_id': lobby_id,
        'requester_puuid': mgr.state[client_id]['puuid']
    })
    
    mgr.state[client_id]['in_queue'] = False
    await mgr.send(ws, 'queue_left', {})
```

*(Continue with other handlers: match.py, veto.py, chat.py, lobby.py - similar pattern)*

#### Step 2.4: WebSocket Route (`app/sockets/routes.py`)
```python
"""
WebSocket endpoint - thin routing layer.
"""
from quart import Blueprint, websocket, current_app
from ..models.messages import Envelope
from .events import get_handler

ws_bp = Blueprint("ws", __name__)

@ws_bp.websocket('/ws')
async def ws_endpoint():
    """Main WebSocket endpoint for frontend communication."""
    mgr = current_app.ctx.conn_mgr
    ws = websocket._get_current_object()
    client_id = mgr.add(ws)
    
    await mgr.send(ws, 'connected', {'message': 'Connected to Scrim.GG client service'})
    
    try:
        async for message in ws:
            # Parse and validate message
            try:
                envelope = Envelope.model_validate_json(message)
            except Exception as e:
                await mgr.send(ws, 'error', {'message': f'Invalid message format: {str(e)}'})
                continue
            
            # Route to handler
            handler = get_handler(envelope.event)
            if not handler:
                await mgr.send(ws, 'error', {'message': f'Unknown event: {envelope.event}'})
                continue
            
            try:
                await handler(envelope.payload or {}, client_id, ws, mgr)
            except Exception as e:
                print(f"[ERROR] Handler error for {envelope.event}: {e}")
                import traceback
                traceback.print_exc()
                await mgr.send(ws, 'error', {'message': f'Error handling {envelope.event}: {str(e)}'})
    
    finally:
        was_in_game = mgr.state[client_id].get('in_game', False) if client_id in mgr.state else False
        await mgr.remove(ws)
        print(f"[DISCONNECT] Client {client_id} disconnected")
```

#### Step 2.5: Health Endpoint (`app/routes/health.py`)
```python
"""
Health check endpoint for Electron readiness detection.
"""
from quart import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.get("/health")
async def health():
    """Simple health check - returns 200 OK when server is ready."""
    return jsonify({"ok": True, "status": "healthy"})
```

#### Step 2.6: Valorant Service Wrapper (`app/services/valorant.py`)
```python
"""
Async facade over ValorantAPI.
Provides clean async interface for handlers.
"""
from clientapi import ValorantAPI
import psutil
from valclient import Client

class ValorantService:
    def __init__(self):
        self.api = ValorantAPI()
    
    async def check_status(self):
        """Check if Valorant is running."""
        try:
            if self.api is None:
                return {
                    'status': 'not_running',
                    'message': 'Valorant API not initialized',
                    'details': None
                }
            
            # Check for VALORANT.exe process
            valorant_process_found = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and 'VALORANT' in proc.info['name'].upper():
                        valorant_process_found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Check Riot Client connection
            temp_client = Client(region='na')
            try:
                temp_client.activate()
                
                if valorant_process_found:
                    is_authenticated = (self.api.client is not None and 
                                      hasattr(self.api.client, 'puuid') and 
                                      self.api.client.puuid is not None)
                    
                    return {
                        'status': 'running',
                        'message': 'Valorant game is running and ready',
                        'details': {
                            'region': temp_client.region,
                            'is_authenticated': is_authenticated
                        }
                    }
                else:
                    return {
                        'status': 'riot_only',
                        'message': 'Valorant not launched',
                        'details': {'region': temp_client.region}
                    }
            except Exception:
                return {
                    'status': 'not_running',
                    'message': 'Riot Client is not running',
                    'details': None
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking status: {str(e)}',
                'details': None
            }
    
    async def login(self, region: str):
        """Login to Valorant."""
        return await self.api.login(region)
    
    async def get_player_model(self):
        """Get player model from Django."""
        return await self.api.get_player_model()
    
    async def create_lobby(self):
        """Create a lobby."""
        return await self.api.createlobby()
```

#### Step 2.7: App Factory (`app/__init__.py`)
```python
"""
Quart application factory.
Creates app, registers blueprints, sets up lifecycle.
"""
import asyncio
import contextlib
from quart import Quart
from quart_cors import cors

from .sockets.manager import ConnectionManager
from .services.valorant import ValorantService
from .sockets.routes import ws_bp
from .routes.health import health_bp
from . import settings

# Import all handlers to register them
from .sockets.handlers import status, auth, queue, match, veto, chat, lobby

def create_app() -> Quart:
    """Create and configure the Quart application."""
    app = Quart(__name__)
    
    # Configure CORS
    app = cors(
        app,
        allow_origin=settings.CORS_ORIGIN,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True
    )
    
    # Initialize services
    app.ctx.conn_mgr = ConnectionManager()
    app.ctx.valorant = ValorantService()
    
    # Register blueprints
    app.register_blueprint(ws_bp)
    app.register_blueprint(health_bp)
    
    @app.before_serving
    async def startup():
        """Run startup tasks."""
        print("=" * 60)
        print("Starting Scrim.GG Client Service")
        print("=" * 60)
        print(f"WebSocket server: ws://{settings.HOST}:{settings.PORT}/ws")
        print(f"Health check: http://{settings.HOST}:{settings.PORT}/health")
        print("Ready to connect to Valorant")
        print("=" * 60)
        
        # Start heartbeat
        app.ctx.heartbeat_task = asyncio.create_task(
            app.ctx.conn_mgr.start_heartbeat(app.ctx.valorant)
        )
    
    @app.after_serving
    async def shutdown():
        """Run shutdown tasks."""
        print("Shutting down...")
        
        # Stop heartbeat
        if hasattr(app.ctx, 'heartbeat_task') and app.ctx.heartbeat_task:
            app.ctx.heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await app.ctx.heartbeat_task
        
        # Close all connections
        await app.ctx.conn_mgr.close_all()
        
        print("Cleanup complete")
    
    return app
```

#### Step 2.8: Entry Point (`run.py`)
```python
"""
Entry point for the Scrim.GG client backend.
Replaces bootstrap.py
"""
from app import create_app
from app import settings

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    )
```

### Phase 3: Electron Integration (2-3 hours)

#### Step 3.1: Update main.js with Health Check
```javascript
const http = require('http');

const DEFAULT_PORT = 5888;

function waitForHealth(port, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    (function ping() {
      http.get(`http://127.0.0.1:${port}/health`, res => {
        if (res.statusCode === 200) return resolve();
        retry();
      }).on('error', retry);
      
      function retry() {
        if (Date.now() > deadline) {
          return reject(new Error('Backend health timeout'));
        }
        setTimeout(ping, 300);
      }
    })();
  });
}

function startPythonBackend() {
  const backendDir = path.join(__dirname, '..', 'backend');
  const entry = 'run.py'; // Changed from bootstrap.py
  const isWin = process.platform === 'win32';
  const isDev = process.env.NODE_ENV === 'development';

  let cmd, args;
  if (isDev) {
    const venvPy = process.env.BACKEND_PY || path.join(backendDir, '.venv', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python');
    cmd = venvPy;
    args = [entry];
  } else {
    const exe = path.join(backendDir, 'backend.exe');
    if (require('fs').existsSync(exe)) {
      cmd = exe;
      args = [];
    } else {
      cmd = 'python';
      args = [entry];
    }
  }

  pythonProcess = spawn(cmd, args, {
    cwd: backendDir,
    env: { ...process.env, PORT: String(DEFAULT_PORT), PYTHONUNBUFFERED: '1' },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  pythonProcessPid = pythonProcess.pid;
  pythonProcess.stdout.on('data', d => console.log(`🐍 ${d}`));
  pythonProcess.stderr.on('data', d => console.error(`🐍E ${d}`));
  pythonProcess.on('close', code => {
    console.log(`Python exited ${code}`);
    pythonProcessPid = null;
  });
}

app.whenReady().then(async () => {
  forceKillBackendProcesses();
  startPythonBackend();
  
  try {
    await waitForHealth(DEFAULT_PORT);
    console.log('✅ Backend ready');
  } catch (e) {
    console.error('❌ Backend not ready in time:', e.message);
  }
  
  createWindow();
});
```

#### Step 3.2: Improved Process Cleanup
```javascript
const kill = require('tree-kill'); // npm install tree-kill

function killPythonBackend() {
  if (!pythonProcessPid) return;
  console.log(`🛑 Killing backend PID ${pythonProcessPid}`);
  
  if (process.platform === 'win32') {
    kill(pythonProcessPid, 'SIGKILL', err => {
      if (err) console.error('kill error', err);
    });
  } else {
    try {
      process.kill(-pythonProcessPid, 'SIGTERM');
    } catch {
      try { process.kill(pythonProcessPid, 'SIGTERM'); } catch {}
    }
  }
}
```

#### Step 3.3: Security Hardening (Preload Script)
```javascript
// In createWindow():
const win = new BrowserWindow({
  // ... other options
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,
    preload: path.join(__dirname, 'preload.js')
  }
});

// preload.js
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('electronAPI', {
  closeApp: () => ipcRenderer.send('close-app'),
  fadeInWindow: () => ipcRenderer.send('react-ready')
});
```

---

## Testing & Validation

### Unit Tests
```python
# tests/test_connection_manager.py
import pytest
from app.sockets.manager import ConnectionManager

@pytest.mark.asyncio
async def test_add_connection():
    mgr = ConnectionManager()
    mock_ws = MockWebsocket()
    cid = mgr.add(mock_ws)
    
    assert cid in mgr.state
    assert mock_ws in mgr.active
    assert mgr.state[cid]['authenticated'] == False

# tests/test_handlers.py
import pytest
from app.sockets.handlers.status import handle_get_status

@pytest.mark.asyncio
async def test_get_status_handler():
    # Test status handler
    pass
```

### Integration Tests
```python
# tests/test_websocket.py
import pytest
from app import create_app

@pytest.mark.asyncio
async def test_websocket_connection():
    app = create_app()
    client = app.test_client()
    
    async with client.websocket('/ws') as ws:
        # Test connection
        msg = await ws.receive_json()
        assert msg['event'] == 'connected'
```

### Manual Testing Checklist
- [ ] Connect to WebSocket
- [ ] Authenticate with Valorant
- [ ] Join PUG queue
- [ ] Receive match found
- [ ] Accept match
- [ ] Veto system
- [ ] Match lifecycle
- [ ] Graceful shutdown
- [ ] Electron health check
- [ ] Process cleanup on quit

---

## Rollback Plan

### If Issues Arise

1. **Keep old bootstrap.py as backup:**
   ```bash
   cp bootstrap.py bootstrap.py.backup
   ```

2. **Switch entry point back:**
   - In main.js, change `run.py` back to `bootstrap.py`
   - Restart application

3. **Incremental rollback:**
   - If specific handlers fail, revert just those files
   - Keep new structure, copy old handler logic

4. **Full rollback:**
   ```bash
   git checkout bootstrap.py
   rm -rf app/
   rm run.py
   ```

---

## Appendix: File Mapping

### Handler Migration Reference

| Old Location (bootstrap.py) | New Location |
|----------------------------|--------------|
| `handle_connected` | `app/sockets/handlers/status.py` |
| `handle_get_status` | `app/sockets/handlers/status.py` |
| `handle_authenticate` | `app/sockets/handlers/auth.py` |
| `handle_get_initial_state` | `app/sockets/handlers/auth.py` |
| `handle_create_lobby` | `app/sockets/handlers/lobby.py` |
| `handle_join_pug_queue` | `app/sockets/handlers/queue.py` |
| `handle_leave_pug_queue` | `app/sockets/handlers/queue.py` |
| `handle_accept_match` | `app/sockets/handlers/match.py` |
| `handle_veto_map` | `app/sockets/handlers/veto.py` |
| `handle_lobby_chat` | `app/sockets/handlers/chat.py` |
| `valorant_heartbeat_loop` | `app/sockets/manager.py::start_heartbeat` |
| `check_valorant_status` | `app/services/valorant.py::check_status` |

---

## Success Criteria

✅ **The refactor is successful when:**

1. All WebSocket events work exactly as before
2. Electron reliably detects backend readiness
3. Process cleanup is clean on all platforms
4. Code is modular and testable
5. No regression in functionality
6. Documentation is updated
7. Team can easily add new event handlers

---

## Next Steps

1. **Review this plan** with the team
2. **Create a feature branch:** `feature/backend-refactor`
3. **Implement Phase 1** (Foundation)
4. **Test thoroughly** after each phase
5. **Merge incrementally** if possible
6. **Update documentation** as you go
7. **Deploy to staging** before production

---

**Ready to proceed? Let me know if you want me to start implementing any phase, or if you'd like to discuss/modify the plan!**

