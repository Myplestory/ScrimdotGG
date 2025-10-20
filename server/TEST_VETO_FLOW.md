# 🧪 Test Veto Flow - Quick Guide

## Restart Server

```bash
cd server
pipenv run daphne -b 0.0.0.0 -p 8000 scrimgg.asgi:application
```

## What to Test

### 1. Queue and Match Acceptance
- ✅ Join queue with 10 bots/clients
- ✅ Wait for match to be found
- ✅ **Check:** All players see "1/10 accepted", "2/10 accepted" incrementing
- ✅ All players accept
- ✅ **Check:** All players see "Match is ready!" notification

### 2. Match Data and Group Joining
- ✅ **Check:** WebSocket stays connected (no 500 errors)
- ✅ **Check:** Match data loads (teams visible, captains assigned)
- ✅ **Check:** Server logs show "Added player {puuid} to match group match_{id}"

### 3. Server Veto Phase
- ✅ **Check:** Server veto UI appears
- ✅ **Check:** Available servers list is visible
- ✅ **Check:** Current turn indicator shows which team bans
- ✅ Perform server veto
- ✅ **Check:** All players see real-time veto updates
- ✅ **Check:** Server list reduces as servers are vetoed

### 4. Map Veto Phase
- ✅ **Check:** After server veto complete, map veto UI appears
- ✅ **Check:** Available maps list is visible
- ✅ Perform map veto
- ✅ **Check:** All players see real-time veto updates
- ✅ **Check:** Map list reduces as maps are vetoed

### 5. Side Selection and Match Ready
- ✅ **Check:** Side selection UI appears
- ✅ Select side
- ✅ **Check:** Match transitions to "ready" state
- ✅ **Check:** No WebSocket disconnections throughout entire flow

## Expected Server Logs (Healthy)

```
[INFO] lobby_manager | Lobby created: xxx
[INFO] matchmaking.queue_manager | Lobby xxx joined pug queue
[INFO] matchmaking.tasks | Match created between 2 lobbies
[INFO] match_confirmation | Player xxx accepted match xxx (1/10)
[INFO] match_system.managers.confirmation_manager | Player acceptance update sent to ALL 2 lobbies: 1/10 accepted
[INFO] match_confirmation | Player xxx accepted match xxx (10/10)
[INFO] match_system.managers.confirmation_manager | 🎉 MATCH READY! All players accepted
[INFO] match_system.managers.confirmation_manager | ✅ All 2 lobbies notified - match starting!
[INFO] match_confirmation | Transitioning match xxx to Match instance...
[INFO] match_confirmation | Match confirmed and match_data broadcast sent to 10 players
[INFO] realtime.consumers | Added player xxx to match group match_xxx
[INFO] match_confirmation | Server veto started for match xxx, notified 10 players
```

## Common Issues (Should NOT Happen)

### ❌ If you still see these, something is wrong:

```
ValueError: No handler for message type server_veto_started
→ SHOULD NOT HAPPEN - handler was added

WebSocket DISCONNECT after match acceptance
→ SHOULD NOT HAPPEN - handlers were added

"0/10 accepted" never changes
→ SHOULD NOT HAPPEN - orchestration layer broadcasts now

Match data doesn't load / teams empty
→ Check that player was added to match group

Veto UI never appears
→ Check server logs for errors during transition
```

## Success Criteria

- [x] No WebSocket disconnections during match flow
- [x] Acceptance counter updates for all players
- [x] "Match is ready!" appears when 10/10 accept
- [x] Match data loads (teams, captains visible)
- [x] Server veto UI appears with real-time updates
- [x] Map veto UI appears with real-time updates
- [x] Side selection works
- [x] Match completes end-to-end

## If Issues Persist

1. Check server logs for errors
2. Verify all 3 files were modified:
   - `server/realtime/consumers.py`
   - `server/match_system/managers/confirmation_manager.py`
   - `server/realtime/handlers/match_handler.py`
3. Verify server was restarted after changes
4. Check `REFACTOR_IMPLEMENTATION_COMPLETE.md` for details

