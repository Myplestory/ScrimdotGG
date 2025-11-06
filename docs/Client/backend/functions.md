# Client Backend (Quart) - Function Reference

Sorted by file and grouped by functionality/logic flow. See `backend/index.rst` for overview.

## App Factory and Routing

### app/__init__.py
- create_app() -> Quart: Initializes app, blueprints, and lifecycle hooks

### app/sockets/routes.py
- ws_endpoint(): Single WS endpoint; validates envelope and dispatches

### app/sockets/events.py
- on(event: str): Decorator to register event handlers
- get_handler(event: str) -> Callable | None: Registry lookup

### app/routes/health.py
- health(): Returns readiness `{ ok: true }`

## Authentication and Status

### app/sockets/handlers/status.py
- handle_connected(payload, client_id, ws, mgr): Initial handshake
- handle_get_status(payload, client_id, ws, mgr): Backend + Valorant status

### app/sockets/handlers/auth.py
- handle_authenticate(payload, client_id, ws, mgr): Client authentication
- handle_get_initial_state(payload, client_id, ws, mgr): Initial client state

## Lobby and Queue

### app/sockets/handlers/lobby.py
- handle_create_lobby(payload, client_id, ws, mgr)
- handle_join_lobby(payload, client_id, ws, mgr)
- handle_leave_lobby(payload, client_id, ws, mgr)
- handle_queue_lobby(payload, client_id, ws, mgr)
- handle_dequeue_lobby(payload, client_id, ws, mgr)
- handle_get_player_data(payload, client_id, ws, mgr)
- handle_get_match_data(payload, client_id, ws, mgr)

### app/sockets/handlers/queue.py
- handle_join_pug_queue(payload, client_id, ws, mgr)
- handle_leave_pug_queue(payload, client_id, ws, mgr)

## Match Flow

### app/sockets/handlers/match.py
- handle_pug_match_found(payload, client_id, ws, mgr)
- handle_match_found(payload, client_id, ws, mgr)
- handle_accept_match(payload, client_id, ws, mgr)
- handle_decline_match(payload, client_id, ws, mgr)
- handle_match_starting(payload, client_id, ws, mgr)
- create_custom_game(valorant_service, match_id, map_name, server, client_id)
- handle_join_custom_game(payload, client_id, ws, mgr)
- handle_all_players_joined(payload, client_id, ws, mgr)
- handle_match_in_progress(payload, client_id, ws, mgr)
- handle_match_score_update(payload, client_id, ws, mgr)
- handle_match_completed(payload, client_id, ws, mgr)
- handle_match_started(payload, client_id, ws, mgr)
- handle_match_ended(payload, client_id, ws, mgr)
- handle_match_cancelled(payload, client_id, ws, mgr)
- handle_teams_assigned(payload, client_id, ws, mgr)
- handle_map_selected(payload, client_id, ws, mgr)
- handle_side_selected(payload, client_id, ws, mgr)
- handle_side_acknowledged(payload, client_id, ws, mgr)

## Veto and Side Selection

### app/sockets/handlers/veto.py
- handle_veto_map(payload, client_id, ws, mgr)
- handle_map_vetoed(payload, client_id, ws, mgr)
- handle_veto_complete(payload, client_id, ws, mgr)
- handle_veto_acknowledged(payload, client_id, ws, mgr)
- handle_veto_server(payload, client_id, ws, mgr)
- handle_server_veto_started(payload, client_id, ws, mgr)
- handle_server_veto_update(payload, client_id, ws, mgr)
- handle_server_vetoed(payload, client_id, ws, mgr)
- handle_server_veto_complete(payload, client_id, ws, mgr)
- handle_server_veto_acknowledged(payload, client_id, ws, mgr)
- handle_server_veto_timeout(payload, client_id, ws, mgr)
- handle_side_selection_timeout(payload, client_id, ws, mgr)

## Messaging and Utilities

### app/sockets/handlers/chat.py
- handle_lobby_chat(payload, client_id, ws, mgr)
- handle_direct_message(payload, client_id, ws, mgr)

### app/utils/logger.py
- get_logger(name, level=logging.INFO) -> logging.Logger
- setup_root_logger(): Configure global logging

Notes:
- Event names and payload shapes are defined alongside server docs in `docs/Server/*`.
- The backend acts as a mediator between the React frontend and the Django server via WebSocket.
