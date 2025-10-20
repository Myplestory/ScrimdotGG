# ✅ Correct Refactor Implementation - Separation of Concerns

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ CLIENT                                                       │
│ WebSocket Connection                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ REALTIME APP (WebSocket Layer)                              │
│                                                              │
│ • realtime/consumers.py                                      │
│   - Broadcast handlers (server_veto_started, etc.)          │
│   - Just forwards channel_layer messages to WebSocket       │
│   - NO business logic                                        │
│                                                              │
│ • realtime/handlers/match_handler.py                         │
│   - Thin layer: receives client events                      │
│   - Calls match_system managers                              │
│   - Sends response back to client                            │
│   - NO orchestration/broadcasting                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ MATCH_SYSTEM APP (Orchestration Layer)                      │
│                                                              │
│ • match_system/managers/confirmation_manager.py              │
│   - Wraps old matchmaking/match_confirmation.py              │
│   - Adds orchestration: broadcasts to lobbies                │
│   - Broadcasts acceptance progress                           │
│   - Broadcasts match_ready                                   │
│                                                              │
│ • match_system/managers/veto_manager.py                      │
│   - Wraps old matchmaking veto logic                         │
│   - Broadcasts veto updates to match groups                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ MATCHMAKING APP (Legacy Business Logic)                     │
│                                                              │
│ • matchmaking/match_confirmation.py                          │
│   - Redis operations                                         │
│   - Match creation                                           │
│   - Veto phase logic                                         │
│   - NO broadcasting (moved to match_system)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 1: Add Missing Broadcast Handlers to RealtimeConsumer

**File:** `server/realtime/consumers.py`

**Add after line 270:**

```python
# -------------------- Veto Broadcast Handlers --------------------
# These receive from channel_layer and forward to WebSocket client

async def server_veto_started(self, event):
    """Server veto phase has begun."""
    await self.send(text_data=json.dumps({
        'event': 'server_veto_started',
        'payload': {
            'match_id': event.get('match_id'),
            'current_turn': event.get('current_turn'),
            'available_servers': event.get('available_servers', []),
            'deadline': event.get('deadline')
        }
    }))

async def server_vetoed(self, event):
    """A server was vetoed."""
    await self.send(text_data=json.dumps({
        'event': 'server_veto_update',
        'payload': {
            'match_id': event.get('match_id'),
            'server_name': event.get('server_name'),
            'vetoed_by': event.get('vetoed_by'),
            'next_turn': event.get('next_turn'),
            'remaining_servers': event.get('remaining_servers', []),
            'deadline': event.get('deadline')
        }
    }))

async def server_veto_complete(self, event):
    """Server veto phase completed - transition to map veto."""
    await self.send(text_data=json.dumps({
        'event': 'server_veto_complete',
        'payload': {
            'match_id': event.get('match_id'),
            'final_server': event.get('final_server'),
            'current_turn': event.get('current_turn'),
            'available_maps': event.get('available_maps', []),
            'veto_deadline': event.get('veto_deadline')
        }
    }))
    
    # Also send map_veto_started if applicable
    if event.get('map_veto_started', False):
        await self.send(text_data=json.dumps({
            'event': 'map_veto_started',
            'payload': {
                'match_id': event.get('match_id'),
                'current_turn': event.get('current_turn'),
                'available_maps': event.get('available_maps', []),
                'deadline': event.get('veto_deadline')
            }
        }))

async def server_veto_timeout(self, event):
    """Server veto timeout - auto-veto occurred."""
    await self.send(text_data=json.dumps({
        'event': 'server_veto_timeout',
        'payload': {
            'match_id': event.get('match_id'),
            'timed_out_team': event.get('timed_out_team'),
            'auto_vetoed_server': event.get('auto_vetoed_server'),
            'next_turn': event.get('next_turn'),
            'remaining_servers': event.get('remaining_servers', []),
            'deadline': event.get('deadline')
        }
    }))

async def map_vetoed(self, event):
    """A map was vetoed."""
    await self.send(text_data=json.dumps({
        'event': 'map_vetoed',
        'payload': {
            'match_id': event.get('match_id'),
            'map': event.get('map_name'),
            'vetoed_by': event.get('vetoed_by'),
            'next_turn': event.get('next_turn'),
            'remaining_maps': event.get('remaining_maps', []),
            'deadline': event.get('deadline')
        }
    }))

async def map_veto_started(self, event):
    """Map veto phase has begun."""
    await self.send(text_data=json.dumps({
        'event': 'map_veto_started',
        'payload': {
            'match_id': event.get('match_id'),
            'current_turn': event.get('current_turn'),
            'available_maps': event.get('available_maps', []),
            'deadline': event.get('deadline')
        }
    }))

async def map_veto_timeout(self, event):
    """Map veto timeout - auto-veto occurred."""
    await self.send(text_data=json.dumps({
        'event': 'map_veto_timeout',
        'payload': {
            'match_id': event.get('match_id'),
            'auto_vetoed_map': event.get('auto_vetoed_map'),
            'veto_complete': event.get('veto_complete', False),
            'next_turn': event.get('next_turn'),
            'remaining_maps': event.get('remaining_maps', []),
            'deadline': event.get('deadline'),
            'final_map': event.get('final_map')
        }
    }))

async def side_selection_timeout(self, event):
    """Side selection timeout - auto-select occurred."""
    await self.send(text_data=json.dumps({
        'event': 'side_selection_timeout',
        'payload': {
            'match_id': event.get('match_id'),
            'auto_selected_side': event.get('auto_selected_side'),
            'side_selection_complete': event.get('side_selection_complete', False),
            'match_ready': event.get('match_ready', False)
        }
    }))
```

**Fix existing match_data handler (replace lines 264-266):**

```python
async def match_data(self, event):
    """
    Match data broadcast - ensures all players get captain/team info.
    CRITICAL: Adds player to match group for veto updates.
    """
    # Add player to match group for veto updates
    match_id = event.get('match_id')
    if match_id:
        await self.channel_layer.group_add(
            f"match_{match_id}",
            self.channel_name
        )
        logger.info(f"Added player {self.puuid} to match group match_{match_id}")
    
    await self.send(text_data=json.dumps({
        'event': 'match_data',
        'payload': event.get('payload', {})
    }))
```

---

### Step 2: Implement match_system Confirmation Manager

**File:** `server/match_system/managers/confirmation_manager.py`

**Replace entire file with:**

```python
"""
Match Confirmation Manager - Orchestration Layer
Wraps legacy matchmaking code and adds broadcasting.
"""
import logging
from typing import Dict
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class MatchConfirmationManager:
    """
    Orchestration layer for match confirmation.
    Wraps old matchmaking/match_confirmation.py and adds broadcasting.
    """
    
    @staticmethod
    async def accept_match(match_id: str, player_puuid: str) -> Dict:
        """
        Accept match for a player with full orchestration.
        
        This is the NEW orchestration layer that:
        1. Calls old match_confirmation.py for Redis/business logic
        2. Adds broadcasting to all lobbies involved
        3. Broadcasts match_ready when all players accept
        
        Args:
            match_id: Match confirmation ID
            player_puuid: Player's PUUID
            
        Returns:
            Dict with acceptance status
        """
        try:
            # Import old manager for business logic
            from matchmaking.match_confirmation import MatchConfirmationManager as OldManager
            
            # Call old manager for Redis operations and business logic
            result = await OldManager.accept_match(match_id, player_puuid)
            
            if result['status'] != 'success':
                return result
            
            # Extract data for broadcasting
            match_lobbies = result.get('match_lobbies', [])
            accepted_count = result.get('accepted_count')
            total_players = result.get('total_players')
            timeout_seconds = result.get('timeout_seconds')
            match_confirmed = result.get('match_confirmed', False)
            
            # Get channel layer for broadcasting
            channel_layer = get_channel_layer()
            
            if match_confirmed:
                # All players accepted - broadcast match_ready to ALL lobbies
                logger.info(f"🎉 MATCH READY! All players accepted match {match_id[:8]}...")
                logger.info(f"   Notifying {len(match_lobbies)} lobbies that match is ready")
                
                for lobby_id in match_lobbies:
                    await channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'match_ready',
                            'message': 'Match is ready!',
                            'match_id': str(result.get('match_id')) if result.get('match_id') else None
                        }
                    )
                
                logger.info(f"   ✅ All {len(match_lobbies)} lobbies notified - match starting!")
            else:
                # Broadcast acceptance progress to ALL lobbies involved
                if match_lobbies:
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
                    
                    logger.info(
                        f"Player acceptance update sent to ALL {len(match_lobbies)} lobbies: "
                        f"{accepted_count}/{total_players} accepted"
                    )
                else:
                    logger.warning(f"Could not determine match lobbies for player {player_puuid}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in match_system accept_match orchestration: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': f'Failed to accept match: {str(e)}'
            }
    
    @staticmethod
    async def decline_match(match_id: str, player_puuid: str) -> Dict:
        """
        Decline match for a player.
        
        Args:
            match_id: Match confirmation ID
            player_puuid: Player's PUUID
            
        Returns:
            Dict with decline status
        """
        try:
            # Import old manager for business logic
            from matchmaking.match_confirmation import MatchConfirmationManager as OldManager
            
            # Call old manager (which already handles broadcasting)
            result = await OldManager.decline_match(match_id, player_puuid)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in match_system decline_match orchestration: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to decline match: {str(e)}'
            }
    
    @staticmethod
    async def get_match_data(match_confirmation_id: str) -> Dict:
        """
        Get match data.
        
        Args:
            match_confirmation_id: Match confirmation ID
            
        Returns:
            Dict with match data
        """
        try:
            from matchmaking.match_confirmation import MatchConfirmationManager as OldManager
            return await OldManager.get_match_data(match_confirmation_id)
        except Exception as e:
            logger.error(f"Error getting match data: {str(e)}")
            return None
```

---

### Step 3: Update MatchHandler to Use New Manager

**File:** `server/realtime/handlers/match_handler.py`

**Replace entire file with:**

```python
"""
Match confirmation WebSocket event handler.
Handles match acceptance/decline during confirmation phase.

EXTRACTED FROM: matchmaking/consumers.py
"""

import logging
from .base import BaseHandler

logger = logging.getLogger(__name__)


class MatchHandler(BaseHandler):
    """
    Handles match confirmation events (accept/decline).
    Thin layer that calls match_system orchestration.
    """
    
    async def handle_accept_match(self, data):
        """
        Handle accept_match event.
        Calls NEW match_system manager (which does orchestration).
        """
        try:
            # Import NEW manager from match_system (orchestration layer)
            from match_system.managers import MatchConfirmationManager
            
            payload = data.get('payload', {})
            match_id = payload.get('match_id') or payload.get('match_confirmation_id')
            
            if not match_id:
                await self.send_error("Match ID is required")
                return
            
            logger.info(f"✅ Player {self.puuid[:12]}... ACCEPTED match {match_id[:8]}...")
            
            # Call NEW manager - it handles ALL orchestration including broadcasting
            result = await MatchConfirmationManager.accept_match(match_id, self.puuid)
            
            if result['status'] == 'success':
                # Convert any UUID objects to strings for JSON serialization
                safe_result = {
                    'status': result.get('status'),
                    'match_confirmed': result.get('match_confirmed'),
                    'accepted_count': result.get('accepted_count'),
                    'total_players': result.get('total_players'),
                    'timeout_seconds': result.get('timeout_seconds'),
                    'match_id': str(result.get('match_id')) if result.get('match_id') else None,
                    'lobby_id': str(result.get('lobby_id')) if result.get('lobby_id') else None,
                }
                
                # Send acknowledgment to accepting player
                await self.send_event('match_accepted', safe_result)
                
                logger.info(f"Player {self.puuid} accepted match {match_id}")
            else:
                await self.send_error(result.get('message', 'Failed to accept match'))
                
        except Exception as e:
            logger.error(f"Error accepting match: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.send_error(str(e))
    
    async def handle_decline_match(self, data):
        """
        Handle decline_match event.
        Calls NEW match_system manager.
        """
        try:
            from match_system.managers import MatchConfirmationManager
            
            payload = data.get('payload', {})
            match_id = payload.get('match_id') or payload.get('match_confirmation_id')
            
            if not match_id:
                await self.send_error("Match ID is required")
                return
            
            result = await MatchConfirmationManager.decline_match(match_id, self.puuid)
            
            if result['status'] == 'success':
                await self.send_success("Match declined")
            else:
                await self.send_error(result.get('message'))
                
        except Exception as e:
            logger.error(f"Error declining match: {e}")
            await self.send_error(str(e))
```

---

## Summary of Changes

### 1. **RealtimeConsumer** (WebSocket Routing)
- ✅ Add 8 missing broadcast handlers (veto events)
- ✅ Fix `match_data` handler to add player to match group
- **Role:** Just forwards channel_layer messages to WebSocket clients

### 2. **MatchConfirmationManager** (New Orchestration)
- ✅ Create NEW manager in `match_system/managers/confirmation_manager.py`
- ✅ Wraps old `matchmaking/match_confirmation.py` for business logic
- ✅ Adds broadcasting for acceptance progress
- ✅ Adds broadcasting for match_ready
- **Role:** Orchestration layer that coordinates business logic + broadcasting

### 3. **MatchHandler** (Thin WebSocket Layer)
- ✅ Update to call NEW `match_system` manager
- ✅ Remove orchestration/broadcasting logic (moved to manager)
- **Role:** Thin layer between WebSocket and business logic

---

## Why This Architecture?

### Separation of Concerns ✅

```
realtime/         → WebSocket routing (no business logic)
match_system/     → Orchestration (business logic + broadcasting)
matchmaking/      → Legacy code (Redis operations, kept for compatibility)
```

### Benefits ✅

1. **Clean separation**: WebSocket layer doesn't know about business logic
2. **Reusable orchestration**: `match_system` managers can be called from anywhere
3. **Testable**: Can test orchestration without WebSocket
4. **Backward compatible**: Old `matchmaking` code still works
5. **Future-proof**: Easy to migrate more logic to `match_system` over time

---

## Testing After Implementation

```python
# 1. Queue joining works ✅ (already fixed)
# 2. Match found ✅ (should work)
# 3. Accept match → ALL players see acceptance count ✅ (NEW)
# 4. 10/10 accept → match_ready broadcast ✅ (NEW)
# 5. match_data → players added to match group ✅ (NEW)
# 6. server_veto_started → UI shows veto ✅ (NEW)
# 7. Veto updates in real-time ✅ (NEW)
# 8. Complete veto flow ✅ (NEW)
```

---

## Files to Modify

| File | Action | Lines |
|------|--------|-------|
| `realtime/consumers.py` | Add 8 handlers + fix match_data | After line 270 |
| `match_system/managers/confirmation_manager.py` | Implement orchestration | Replace entire file |
| `realtime/handlers/match_handler.py` | Use new manager | Replace entire file |

**Total changes:** 3 files, ~200 lines of code

