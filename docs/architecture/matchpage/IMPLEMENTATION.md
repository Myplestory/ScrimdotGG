# Match Page Implementation



## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Match Acceptance Complete                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  1. Create Match Instance     │
            │     - Unique match_id (UUID)  │
            │     - State: CONFIRMED        │
            │     - Teams assigned          │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  2. Auto-Redirect All Players │
            │     → /match/{match_id}       │
            └───────────────┬───────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  3. Map Veto Phase (Snake Draft)      │
        │     Team A Ban → Team B Ban → ...     │
        │     Until 1 map remains               │
        │     Timeout: 30s per veto             │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │  4. Side Selection                     │
        │     Losing team picks side            │
        │     (Attacker/Defender)               │
        │     Timeout: 15s                      │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │  5. Server Creation (Delegated)       │
        │     → Constructor creates lobby       │
        │     → Others join pregame_id          │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │  6. Match In Progress                 │
        │     → Live score monitoring           │
        │     → Constructor monitors via API    │
        └───────────────┬───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  7. Match Complete    │
            │     → Submit results  │
            │     → Update MMR/ELO  │
            └───────────────────────┘
```

---

## Detailed Implementation

## 1. Data Models (Reference)

- See `docs/Server/matchpage.md` for server-side `Match` and `MatchPlayer` model definitions.

---

## 2. WebSocket Events

### Server → Client Events

```python
# After all players accept
{
    'type': 'match_confirmed',
    'match_id': '<uuid>',
    'teams': {
        'team_a': [...player objects...],
        'team_b': [...player objects...]
    },
    'map_pool': ['Ascent', 'Bind', 'Haven', ...],
    'redirect_url': f'/match/{match_id}'
}

# Veto phase
{
    'type': 'veto_started',
    'match_id': '<uuid>',
    'current_turn': 'team_a',  # or 'team_b'
    'deadline': '<ISO timestamp>',  # 30 seconds from now
    'available_maps': [...],
    'vetoed_maps': [...]
}

{
    'type': 'map_vetoed',
    'match_id': '<uuid>',
    'map': 'Ascent',
    'vetoed_by': 'team_a',
    'next_turn': 'team_b',
    'deadline': '<ISO timestamp>',
    'remaining_maps': [...]
}

{
    'type': 'veto_complete',
    'match_id': '<uuid>',
    'final_map': 'Haven',
    'side_selector': 'team_b'  # Losing team in veto
}

# Side selection
{
    'type': 'side_selection_started',
    'match_id': '<uuid>',
    'selecting_team': 'team_b',
    'deadline': '<ISO timestamp>'  # 15 seconds
}

{
    'type': 'side_selected',
    'match_id': '<uuid>',
    'team': 'team_b',
    'side': 'attack',  # or 'defense'
    'constructor': '<player_puuid>'  # Designated constructor
}

# Custom game creation
{
    'type': 'create_custom_game',
    'match_id': '<uuid>',
    'map': 'Haven',
    'server': 'na-california-1',
    'starting_side': 'attack',
    'is_constructor': true  # Only constructor receives this
}

{
    'type': 'custom_game_created',
    'match_id': '<uuid>',
    'pregame_id': '<valorant_pregame_id>',
    'constructor_puuid': '<puuid>'
}

{
    'type': 'join_custom_game',
    'match_id': '<uuid>',
    'pregame_id': '<valorant_pregame_id>',
    'team': 'team_a'
}

# Match progress
{
    'type': 'player_joined_pregame',
    'match_id': '<uuid>',
    'player_puuid': '<puuid>',
    'players_joined': 8,
    'players_total': 10
}

{
    'type': 'match_starting',
    'match_id': '<uuid>',
    'coregame_id': '<coregame_id>',
    'all_players_joined': true
}

{
    'type': 'match_score_update',
    'match_id': '<uuid>',
    'team_a_score': 7,
    'team_b_score': 5,
    'current_round': 12
}

{
    'type': 'match_completed',
    'match_id': '<uuid>',
    'winner': 'team_a',
    'final_score': {'team_a': 13, 'team_b': 8}
}
```

### Client → Server Events

```python
{
    'action': 'veto_map',
    'match_id': '<uuid>',
    'map': 'Ascent'
}

{
    'action': 'select_side',
    'match_id': '<uuid>',
    'side': 'attack'  # or 'defense'
}

{
    'action': 'ready_for_match',
    'match_id': '<uuid>'
}

{
    'action': 'pregame_joined',
    'match_id': '<uuid>',
    'success': true
}
```

---

## 3. Map Veto System (Snake Draft)

- Server algorithms and handlers: see `docs/Server/matchpage.md`.
- Client-side handlers and UI: see `docs/Client/frontend/matchpage.md`.

---

## 4. Side Selection

- Server logic: see `docs/Server/matchpage.md`.
- Client events/UI: see `docs/Client/frontend/matchpage.md`.

---

## 5. Custom Game Creation (Delegated Approach)

- Constructor selection and server events: see `docs/Server/matchpage.md`.
- Client constructor and join flows: see `docs/Client/backend/matchpage.md`.

---

## 6. Constructor Delegation Rationale

Delegate custom game creation to a player (constructor) rather than a headless account to comply with Riot client constraints and ensure reliability. The constructor is typically the Team A captain, with fallback to the first available online player.

---

## 7. Late Joiner Handling

- Server tracking and Celery checks: see `docs/Server/matchpage.md`.
- Client retry logic: see `docs/Client/backend/matchpage.md`.

---

## 8. Unique Match Pages & Navigation

- Frontend routing and global navigation: see `docs/Client/frontend/matchpage.md`.

---

## 9. Omitted Planning Content

Planning, timelines, milestones, and detailed project management items have been moved to `docs/implementation/`.

---

## 10. Technical Considerations

### Performance
- **Veto Phase**: Real-time WebSocket updates (<100ms latency)
- **Constructor Creation**: ~5-10 seconds (Valorant API call)
- **Player Join**: ~2-5 seconds per player
- **Match Monitoring**: Poll every 30 seconds (low overhead)

### Scalability
- **Concurrent Matches**: ~100+ matches supported
- **Redis**: Store active match state for fast access
- **Celery**: Background tasks for timeouts and monitoring
- **WebSocket**: Efficient real-time updates

### Reliability
- **Constructor Failover**: Auto-select backup if constructor fails
- **Join Retry**: 3 attempts with exponential backoff
- **Timeout Handling**: Auto-proceed if players AFK
- **State Recovery**: Match state persists in database

### Security
- **Authorization**: Only match participants can veto/select
- **Validation**: Server validates all veto/selection requests
- **Rate Limiting**: Prevent spam veto attempts
- **Audit Log**: Track all veto/selection actions

---

## 11. Open Questions & Decisions Needed

### 1. Map Pool Size
- **Option A**: Use intersection of all player preferences (may be small)
- **Option B**: Use union of preferences (may be too large)
- **Recommendation**: Start with intersection, fallback to default 7 maps if <5 maps

### 2. Veto Format
- **Option A**: Ban until 1 remains (simple)
- **Option B**: Ban/pick format (more complex, like pro play)
- **Recommendation**: Start with Option A, iterate based on feedback

### 3. Constructor Failover
- **If constructor fails to create game?**
- **Recommendation**: Auto-select next available player, retry up to 3 times

### 4. Match Cancellation
- **If <8 players join within grace period?**
- **Option A**: Cancel match, requeue all players
- **Option B**: Wait indefinitely
- **Recommendation**: Option A with 5-minute timeout

### 5. Post-Match Flow
- **Immediate ELO update vs delayed?**
- **Show detailed stats?**
- **Recommendation**: Delay ELO update until all data verified, show summary stats immediately

---

## 12. Success Criteria

### Must Have (MVP)
- ✅ All 10 players auto-redirect to match page
- ✅ Map veto completes successfully
- ✅ Custom game created by delegated constructor
- ✅ All players join custom game
- ✅ Match starts and completes

### Should Have
- ✅ Late joiners can rejoin successfully
- ✅ Timeout handling for AFK players
- ✅ Global navigation button for active match
- ✅ Match page persists across page refreshes

### Nice to Have
- ⭐ Detailed veto history/timeline
- ⭐ Team voice chat integration
- ⭐ Live agent selection display
- ⭐ In-game score overlay (desktop app)

---

## 13. Next Steps

See `docs/implementation/` for planning and delivery timelines.

---

**Document Owner**: Development Team  
**Last Updated**: October 2025  
**Status**: Awaiting Approval


