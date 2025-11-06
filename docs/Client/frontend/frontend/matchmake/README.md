# Matchmaking Pages Overview

This directory contains detailed architecture documentation for matchmaking-related pages.

## Pages

1. **[Play Page](./PLAY_PAGE.md)** - PUG (Pick-Up Game) matchmaking queue
   - Lobby creation and management
   - Queue entry and exit
   - Match finding and acceptance
   - Real-time queue status updates

2. **[Scrim Page](./SCRIM_PAGE.md)** - Custom scrim match setup
   - Scrim lobby creation
   - Team invitation system
   - Ready check system
   - Match format configuration

## Common Entities

Both pages share these core entities:

- **Player** - User account and stats
- **Lobby** - Group of players for matchmaking
- **Match** - Confirmed and accepted match

## Event Flow Summary

### PUG Matchmaking Flow
```
Create Lobby → Join Queue → Match Found → Accept Match → Transition to Match Page
```

### Scrim Flow
```
Create Scrim Lobby → Invite Players/Teams → Ready Check → Start Match → Transition to Match Page
```

## Backend Architecture

Both pages utilize:
- **`realtime/consumers.py`** - WebSocket entry point
- **`realtime/handlers/lobby_handler.py`** - Lobby event handling
- **`lobby/manager.py`** - Lobby business logic (to be created)
- **`matchmaking/`** - Queue management and matchmaking algorithm

## Key Differences

| Feature | Play (PUG) | Scrim |
|---------|-----------|-------|
| Team Formation | Automatic by matchmaker | Manual team setup |
| Opponent | Random matched players | Invited opponents |
| Queue | Join matchmaking queue | No queue, direct invites |
| Map Selection | Preferences, then veto | Pre-configured or veto |
| Start Condition | All players accept | Ready check passed |

## Implementation Status

- ✅ Basic Lobby model exists
- ✅ WebSocket infrastructure ready
- ⚠️ Need to implement LobbyManager
- ⚠️ Need to implement ScrimManager
- ⚠️ Need to implement matchmaking algorithm
- ⚠️ Need to add ScrimInvite model
- ⚠️ Need to implement ready check system
