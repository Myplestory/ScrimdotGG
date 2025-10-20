# 📋 Exact Handlers to Copy from Original Consumer

## Copy These Broadcast Handlers

### From: `server/matchmaking/consumers.py`
### To: `server/realtime/consumers.py` (after line 270)

---

## 1. server_veto_started
**Copy from:** Lines 1112-1124
```python
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
```

---

## 2. server_vetoed
**Copy from:** Lines 1126-1140
```python
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
```

---

## 3. server_veto_complete
**Copy from:** Lines 1142-1167
```python
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
```

---

## 4. server_veto_timeout
**Copy from:** Lines 1169-1183
```python
async def server_veto_timeout(self, event):
    """Server veto timeout - a team took too long, auto-veto occurred."""
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
```

---

## 5. map_vetoed
**Copy from:** Lines 1203-1217
```python
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
```

---

## 6. map_veto_started
**Copy from:** Lines 1219-1231
```python
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
```

---

## 7. map_veto_timeout
**Copy from:** Lines 1233-1248
```python
async def map_veto_timeout(self, event):
    """Veto timeout occurred - auto-veto."""
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
```

---

## 8. side_selection_timeout
**Copy from:** Lines 1250-1262
```python
async def side_selection_timeout(self, event):
    """Side selection timeout occurred - auto-select side."""
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

---

## 9. FIX match_data (REPLACE existing)
**Original:** Lines 1080-1096
**Refactored:** Lines 264-266

**REPLACE** refactored version with this:
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

## Fix MatchHandler Acceptance Broadcasting

### File: `server/realtime/handlers/match_handler.py`

### REPLACE handle_accept_match method (lines 19-46)

**With this (from original consumer lines 679-758):**

```python
async def handle_accept_match(self, data):
    """Handle accept_match event."""
    from matchmaking.match_confirmation import MatchConfirmationManager
    
    try:
        payload = data.get('payload', {})
        match_id = payload.get('match_id') or payload.get('match_confirmation_id')
        
        if not match_id:
            await self.send_error("Match ID is required")
            return
        
        logger.info(f"✅ Player {self.puuid[:12]}... ACCEPTED match {match_id[:8]}...")
        
        result = await MatchConfirmationManager.accept_match(match_id, self.puuid)
        
        if result['status'] == 'success':
            if result.get('match_confirmed'):
                # All players accepted - match is ready
                logger.info(f"🎉 MATCH READY! All players accepted match {result.get('match_id', '')[:8]}...")
                
                # Send to ALL lobbies involved in the match
                match_lobbies = result.get('match_lobbies', [])
                logger.info(f"   Notifying {len(match_lobbies)} lobbies that match is ready")
                
                for lobby_id in match_lobbies:
                    await self.channel_layer.group_send(
                        f"lobby_{lobby_id}",
                        {
                            'type': 'match_ready',
                            'message': 'Match is ready!',
                            'match_id': str(result.get('match_id')) if result.get('match_id') else None
                        }
                    )
                logger.info(f"   ✅ All {len(match_lobbies)} lobbies notified - match starting!")
            else:
                # Send acceptance update to ALL lobbies in the match
                match_lobbies = result.get('match_lobbies', [])
                accepted_count = result.get('accepted_count')
                total_players = result.get('total_players')
                timeout_seconds = result.get('timeout_seconds')
                
                if match_lobbies:
                    # Broadcast to all lobbies involved in this match
                    for lobby_id in match_lobbies:
                        await self.channel_layer.group_send(
                            f"lobby_{lobby_id}",
                            {
                                'type': 'player_accepted',
                                'accepted_count': accepted_count,
                                'total_players': total_players,
                                'timeout_seconds': timeout_seconds
                            }
                        )
                    logger.info(f"Player acceptance update sent to ALL {len(match_lobbies)} lobbies: {accepted_count}/{total_players} accepted")
                else:
                    logger.warning(f"Could not determine match lobbies for player {self.puuid}")
            
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
            
            await self.send_event('match_accepted', safe_result)
            
            logger.info(f"Player {self.puuid} accepted match {match_id}")
        else:
            await self.send_error(result.get('message', 'Failed to accept match'))
            
    except Exception as e:
        logger.error(f"Error accepting match: {e}")
        await self.send_error(str(e))
```

---

## Summary

**Total handlers to add:** 9 broadcast handlers  
**Total handlers to fix:** 2 (match_data + handle_accept_match)

**After these changes:**
- ✅ WebSocket stays connected during veto
- ✅ All players see acceptance progress
- ✅ Veto UI displays correctly
- ✅ Real-time veto updates work
- ✅ Match flow completes end-to-end


