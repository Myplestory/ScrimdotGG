# WebSocket Communication Verification

## ✅ WebSocket-Only Architecture Confirmed
All communication between client backend and Django server is now using WebSockets exclusively. No REST API calls remain in active use.

---

## 🔄 Client Backend → Django Server Events (High-Level)
- Lobby management: create, join/leave queue
- Match operations: accept/decline match
- Match execution: custom game created, player joined, match started, score update, match completed

See `docs/Client/backend/` for client event APIs and payloads.

---

## 📥 Django Server → Client Backend Events (High-Level)
- Lobby events: created, invited, kicked, preferences updated
- Queue events: joined/left queue
- Match events: found, accepted/declined, starting, join_custom_game, in_progress, score_update, completed

See `docs/Server/` consumer/producer docs for event schemas.

---

## 🚫 Deprecated REST API Methods
Deprecated methods are retained but unused; replaced by WebSocket events. See client backend deprecation notes in `docs/Client/backend/`.

---

## 🎯 Current Active Flow (Summary)
1. Queue join: frontend → client backend → server → responses
2. Match found and acceptance → transition to match
3. Match execution via constructor/joins → live updates

Detailed sequences and payload shapes are in server/client docs (`docs/Server/`, `docs/Client/`).

---

## ✅ Verification Results
- Client backend uses WebSocket provider exclusively
- Server consumers handle all events with `event` and `data` fields
- Heartbeat optimizations and polling intervals verified

---

## 🧪 Ready for Testing
Authentication, queue join, match found, execution, live updates — see testing guides under `docs/Client/testing.md` and `docs/Server/testing.md`.
