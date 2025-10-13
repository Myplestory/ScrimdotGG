# Match Page Implementation Plan

**Version**: 1.0  
**Date**: October 2025  
**Status**: Planning Phase

---

## Executive Summary

This document outlines the complete implementation plan for the Match Page system, which handles the post-acceptance flow from match confirmation through custom game creation and match execution.

### Key Features
1. **Auto-redirect** to match page after acceptance
2. **Snake draft map veto** system (alternating bans)
3. **Side selection** by losing team
4. **Delegated server creation** (one player creates, others join)
5. **Unique match pages** with persistent URL
6. **Global "Match in Progress" button** for navigation
7. **Late joiner handling** for slow connections

---

## Phase Breakdown

### Phase 1: Match Page Infrastructure (Week 1-2)
- Database models for match state
- WebSocket events for real-time sync
- Frontend routing and match page component
- Global navigation state management

### Phase 2: Map Veto System (Week 2-3)
- Snake draft veto logic (Team A ban → Team B ban → repeat)
- Real-time veto UI with countdown timers
- Veto timeout handling
- Final map selection

### Phase 3: Server Creation & Joining (Week 3-4)
- Constructor delegation logic
- Custom game creation via valclient
- Party joining mechanism
- Late joiner resilience

### Phase 4: Match Monitoring (Week 4-5)
- Live score tracking
- Match completion detection
- Post-match flow

---

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

## 1. Database Models

### Match Model Extension
```python
class Match(models.Model):
    """
    Extended match model for post-acceptance flow.
    """
    # Existing fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Match state
    state = models.CharField(max_length=20, choices=[
        ('CONFIRMED', 'All players accepted'),
        ('VETO', 'Map veto in progress'),
        ('SIDE_SELECTION', 'Side selection in progress'),
        ('CREATING', 'Custom game being created'),
        ('READY', 'Ready to start'),
        ('IN_PROGRESS', 'Match started'),
        ('COMPLETED', 'Match finished'),
        ('CANCELLED', 'Match cancelled'),
    ], default='CONFIRMED')
    
    # Teams
    team_a_lobbies = models.JSONField()  # List of lobby IDs
    team_b_lobbies = models.JSONField()
    team_a_captain = models.ForeignKey(Player, related_name='matches_as_captain_a')
    team_b_captain = models.ForeignKey(Player, related_name='matches_as_captain_b')
    
    # Veto data
    map_pool = models.JSONField()  # Available maps from lobbies
    vetoed_maps = models.JSONField(default=list)  # List of vetoed maps
    final_map = models.CharField(max_length=50, null=True, blank=True)
    veto_turn = models.CharField(max_length=10)  # 'team_a' or 'team_b'
    veto_deadline = models.DateTimeField(null=True)  # 30s countdown
    
    # Side selection
    selected_side = models.CharField(max_length=10, null=True)  # 'attack' or 'defense'
    side_selector = models.CharField(max_length=10, null=True)  # 'team_a' or 'team_b'
    
    # Server creation
    constructor = models.ForeignKey(Player, related_name='constructed_matches', null=True)
    pregame_id = models.CharField(max_length=100, null=True, blank=True)
    server_region = models.CharField(max_length=20)
    
    # Match data
    coregame_id = models.CharField(max_length=100, null=True, blank=True)
    team_a_score = models.IntegerField(default=0)
    team_b_score = models.IntegerField(default=0)
    current_round = models.IntegerField(default=0)
    
    # Timestamps
    veto_started_at = models.DateTimeField(null=True)
    game_started_at = models.DateTimeField(null=True)
    game_ended_at = models.DateTimeField(null=True)
```

### MatchPlayer Model
```python
class MatchPlayer(models.Model):
    """
    Track individual player state within match.
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.CharField(max_length=10)  # 'team_a' or 'team_b'
    
    # Connection tracking
    is_ready = models.BooleanField(default=False)
    joined_pregame = models.BooleanField(default=False)
    joined_at = models.DateTimeField(null=True)
    
    # Performance tracking
    last_seen = models.DateTimeField(auto_now=True)
    connection_issues = models.IntegerField(default=0)
```

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

### Algorithm: Alternating Bans

```python
def start_veto(match: Match):
    """
    Initialize snake draft veto system.
    
    Format: Team A ban → Team B ban → Team A ban → ...
    Until 1 map remains (or 3 maps for BO3 scenarios).
    """
    # Determine starting team (higher average MMR bans first)
    team_a_avg_mmr = calculate_team_mmr(match.team_a_lobbies)
    team_b_avg_mmr = calculate_team_mmr(match.team_b_lobbies)
    
    starting_team = 'team_a' if team_a_avg_mmr >= team_b_avg_mmr else 'team_b'
    
    match.state = 'VETO'
    match.veto_turn = starting_team
    match.veto_started_at = timezone.now()
    match.veto_deadline = timezone.now() + timedelta(seconds=30)
    match.save()
    
    # Broadcast veto_started event
    broadcast_to_match(match.id, {
        'type': 'veto_started',
        'current_turn': starting_team,
        'available_maps': match.map_pool,
        'deadline': match.veto_deadline.isoformat()
    })


def process_veto(match: Match, map_name: str, vetoing_team: str):
    """
    Process a map veto and advance to next turn.
    """
    # Validate
    if match.veto_turn != vetoing_team:
        raise ValueError("Not your turn to veto")
    
    if map_name not in match.map_pool or map_name in match.vetoed_maps:
        raise ValueError("Invalid map")
    
    if timezone.now() > match.veto_deadline:
        # Timeout - auto-veto random map
        map_name = random.choice([m for m in match.map_pool if m not in match.vetoed_maps])
    
    # Add to vetoed list
    match.vetoed_maps.append(map_name)
    
    # Check if veto complete
    remaining_maps = [m for m in match.map_pool if m not in match.vetoed_maps]
    
    if len(remaining_maps) == 1:
        # Veto complete
        match.final_map = remaining_maps[0]
        match.state = 'SIDE_SELECTION'
        
        # Side selector is the team that vetoed last (losing team)
        match.side_selector = vetoing_team
        match.save()
        
        broadcast_to_match(match.id, {
            'type': 'veto_complete',
            'final_map': match.final_map,
            'side_selector': match.side_selector
        })
        
        # Start side selection phase
        start_side_selection(match)
    else:
        # Switch turns
        match.veto_turn = 'team_b' if vetoing_team == 'team_a' else 'team_a'
        match.veto_deadline = timezone.now() + timedelta(seconds=30)
        match.save()
        
        broadcast_to_match(match.id, {
            'type': 'map_vetoed',
            'map': map_name,
            'vetoed_by': vetoing_team,
            'next_turn': match.veto_turn,
            'remaining_maps': remaining_maps,
            'deadline': match.veto_deadline.isoformat()
        })
```

### Timeout Handling

```python
@celery_app.task
def check_veto_timeouts():
    """
    Celery task runs every 5 seconds to check for veto timeouts.
    """
    expired_matches = Match.objects.filter(
        state='VETO',
        veto_deadline__lt=timezone.now()
    )
    
    for match in expired_matches:
        # Auto-veto random map for the team that timed out
        available_maps = [m for m in match.map_pool if m not in match.vetoed_maps]
        
        if available_maps:
            auto_map = random.choice(available_maps)
            process_veto(match, auto_map, match.veto_turn)
            
            logger.warning(f"Match {match.id}: Team {match.veto_turn} timed out, auto-vetoed {auto_map}")
```

---

## 4. Side Selection

```python
def start_side_selection(match: Match):
    """
    After veto, losing team selects starting side.
    """
    match.state = 'SIDE_SELECTION'
    match.veto_deadline = timezone.now() + timedelta(seconds=15)
    match.save()
    
    broadcast_to_match(match.id, {
        'type': 'side_selection_started',
        'selecting_team': match.side_selector,
        'deadline': match.veto_deadline.isoformat()
    })


def process_side_selection(match: Match, side: str, selecting_team: str):
    """
    Process side selection (attack/defense).
    """
    if match.side_selector != selecting_team:
        raise ValueError("Not your turn to select side")
    
    if timezone.now() > match.veto_deadline:
        # Timeout - default to attack
        side = 'attack'
    
    match.selected_side = side
    match.state = 'CREATING'
    match.save()
    
    # Delegate constructor (captain of Team A)
    match.constructor = match.team_a_captain
    match.save()
    
    broadcast_to_match(match.id, {
        'type': 'side_selected',
        'side': side,
        'constructor': match.constructor.puuid
    })
    
    # Trigger custom game creation
    initiate_custom_game_creation(match)
```

---

## 5. Custom Game Creation (Delegated Approach)

### Constructor Selection Logic

```python
def select_constructor(match: Match) -> Player:
    """
    Select which player will create the custom game.
    
    Priority:
    1. Team A captain (higher MMR team)
    2. Fallback to first available player
    """
    # Try Team A captain
    constructor = match.team_a_captain
    
    # Verify constructor is online
    if not is_player_online(constructor.puuid):
        # Fallback to any Team A player
        for lobby_id in match.team_a_lobbies:
            lobby_data = get_lobby_data(lobby_id)
            for player in lobby_data['players']:
                if is_player_online(player['puuid']):
                    constructor = Player.objects.get(puuid=player['puuid'])
                    break
    
    match.constructor = constructor
    match.save()
    
    return constructor
```

### Custom Game Creation Flow

```python
def initiate_custom_game_creation(match: Match):
    """
    Server sends event to constructor client to create custom game.
    """
    # Send to constructor only
    send_to_player(match.constructor.puuid, {
        'type': 'create_custom_game',
        'match_id': str(match.id),
        'map': match.final_map,
        'server': match.server_region,
        'starting_side': match.selected_side,
        'is_constructor': True
    })
    
    # Send "waiting" event to other players
    all_players = get_match_players(match)
    for player in all_players:
        if player.puuid != match.constructor.puuid:
            send_to_player(player.puuid, {
                'type': 'waiting_for_game_creation',
                'match_id': str(match.id),
                'constructor': match.constructor.alias
            })
```

### Client-Side Constructor Implementation

```python
# client/backend/clientapi.py

async def create_custom_game_for_match(self, match_id: str, map_name: str, 
                                       server: str, starting_side: str):
    """
    Constructor client creates the custom game.
    
    This leverages existing valclient functionality:
    1. Change party to custom mode
    2. Set custom game settings (map, server, rules)
    3. Get pregame_id
    4. Notify Django server with pregame_id
    """
    try:
        # Step 1: Change to custom game mode
        custom_response = self.client.party_change_to_custom()
        pregame_id = custom_response.get('ID')
        
        if not pregame_id:
            raise ValueError("Failed to create custom game")
        
        # Step 2: Configure game settings
        build_args = {
            "Map": self.args['mapPreferences'][map_name],
            "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
            "GamePod": self._get_server_url(server),
            "UseBots": False,
            "GameRules": {
                "AllowGameModifiers": "true",
                "PlayOutAllRounds": "true",
                "SkipMatchHistory": "true",  # Competitive rules
                "TournamentMode": "false",
                "IsOvertimeWinByTwo": "true",
            },
        }
        
        self.client.party_set_custom_game_settings(build_args)
        
        # Step 3: Notify Django server
        await self.pugsocket.send_message('custom_game_created', {
            'match_id': match_id,
            'pregame_id': pregame_id,
            'constructor_puuid': self.client.puuid
        })
        
        logger.info(f"Custom game created: {pregame_id} for match {match_id}")
        
        return {
            'status': 'success',
            'pregame_id': pregame_id
        }
        
    except Exception as e:
        logger.error(f"Failed to create custom game: {str(e)}")
        
        # Notify server of failure
        await self.pugsocket.send_message('custom_game_creation_failed', {
            'match_id': match_id,
            'error': str(e)
        })
        
        return {
            'status': 'error',
            'message': str(e)
        }
```

### Server Receives Pregame ID

```python
async def handle_custom_game_created(data: dict):
    """
    Django server receives pregame_id from constructor.
    Now tell all other players to join.
    """
    match_id = data['match_id']
    pregame_id = data['pregame_id']
    
    match = Match.objects.get(id=match_id)
    match.pregame_id = pregame_id
    match.state = 'READY'
    match.save()
    
    # Broadcast to ALL players (including constructor)
    all_players = get_match_players(match)
    
    for player in all_players:
        team = get_player_team(match, player.puuid)
        
        send_to_player(player.puuid, {
            'type': 'join_custom_game',
            'match_id': str(match.id),
            'pregame_id': pregame_id,
            'team': team
        })
```

### Client-Side Join Implementation

```python
# client/backend/clientapi.py

async def join_custom_game(self, pregame_id: str, match_id: str):
    """
    Non-constructor clients join the custom game.
    """
    try:
        # Leave current party if needed
        try:
            current_party = self.client.party_fetch_player()
            if current_party:
                self.client.party_leave(current_party['CurrentPartyID'])
        except:
            pass  # Already not in a party
        
        # Join the pregame via party_join
        result = self.client.party_join(pregame_id)
        
        # Notify Django server
        await self.pugsocket.send_message('player_joined_pregame', {
            'match_id': match_id,
            'player_puuid': self.client.puuid,
            'success': True
        })
        
        logger.info(f"Joined custom game {pregame_id} for match {match_id}")
        
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f"Failed to join custom game: {str(e)}")
        
        await self.pugsocket.send_message('player_joined_pregame', {
            'match_id': match_id,
            'player_puuid': self.client.puuid,
            'success': False,
            'error': str(e)
        })
        
        return {'status': 'error', 'message': str(e)}
```

---

## 6. Ghost Account Feasibility Analysis

### **Conclusion: NOT FEASIBLE**

Based on analysis of valclient API:

**Why Ghost Account Doesn't Work:**

1. **Authentication Required**
   - Valclient requires Riot account credentials via lockfile
   - Lockfile only exists when Valorant client is running
   - Cannot create lockfile without actual logged-in Valorant client

2. **Party API Limitations**
   - `party_change_to_custom()` requires active party
   - `party_set_custom_game_settings()` requires party leader permissions
   - `party_start_custom_game()` triggers client-side game start
   - All these operations need a real Valorant client instance running

3. **No Headless Mode**
   - Valorant has no headless/server mode
   - Riot Games doesn't provide server hosting API
   - All custom games must be created by a player client

4. **Security & Anti-Cheat**
   - Vanguard (Riot's anti-cheat) prevents automated/bot accounts
   - API calls are validated against active game client
   - Lockfile contains temporary session tokens tied to actual game instance

**Alternative Considered: Dedicated Constructor Bot**
- Would require a physical machine running Valorant 24/7
- High resource cost (~8GB RAM, GPU, Windows OS)
- Riot TOS violation (automated/unattended accounts)
- Not practical or recommended

**Recommended Approach: Delegate to Player (Current Plan)**
- Select Team A captain as constructor
- Fallback to any available player
- 99.9% reliable (players are already online and in-game)
- No additional infrastructure needed
- Works within Riot's ecosystem

---

## 7. Late Joiner Handling

### Problem
Players with slow internet may take longer to join the pregame lobby.

### Solution: Grace Period + Retry Logic

```python
# Server-side tracking
class MatchPlayer(models.Model):
    # ... existing fields ...
    join_attempts = models.IntegerField(default=0)
    last_join_attempt = models.DateTimeField(null=True)
    join_timeout = models.DateTimeField(null=True)  # 2 minutes grace period


async def handle_player_joined_pregame(data: dict):
    """
    Track which players have successfully joined.
    """
    match_id = data['match_id']
    player_puuid = data['player_puuid']
    success = data.get('success', False)
    
    match_player = MatchPlayer.objects.get(
        match_id=match_id,
        player__puuid=player_puuid
    )
    
    if success:
        match_player.joined_pregame = True
        match_player.joined_at = timezone.now()
        match_player.save()
        
        # Broadcast progress
        total_players = MatchPlayer.objects.filter(match_id=match_id).count()
        joined_players = MatchPlayer.objects.filter(
            match_id=match_id,
            joined_pregame=True
        ).count()
        
        broadcast_to_match(match_id, {
            'type': 'player_joined_pregame',
            'player_puuid': player_puuid,
            'players_joined': joined_players,
            'players_total': total_players
        })
        
        # Check if all players joined
        if joined_players == total_players:
            # All players ready - constructor can start game
            trigger_match_start(match_id)
    else:
        # Join failed - increment attempts
        match_player.join_attempts += 1
        match_player.last_join_attempt = timezone.now()
        match_player.save()
        
        # If too many failures, notify player
        if match_player.join_attempts >= 3:
            send_to_player(player_puuid, {
                'type': 'join_failed',
                'match_id': match_id,
                'message': 'Failed to join custom game. Please check your connection.'
            })


@celery_app.task
def check_late_joiners():
    """
    Celery task: Check for players who haven't joined after 2 minutes.
    """
    grace_period = timezone.now() - timedelta(minutes=2)
    
    late_players = MatchPlayer.objects.filter(
        match__state='READY',
        joined_pregame=False,
        match__created_at__lt=grace_period
    )
    
    for late_player in late_players:
        match = late_player.match
        
        # Send retry prompt
        send_to_player(late_player.player.puuid, {
            'type': 'rejoin_prompt',
            'match_id': str(match.id),
            'pregame_id': match.pregame_id,
            'message': 'Please rejoin the custom game'
        })
        
        logger.warning(f"Player {late_player.player.alias} is late to join match {match.id}")


# Client-side retry logic
async def rejoin_custom_game_with_retry(self, pregame_id: str, match_id: str, max_retries=3):
    """
    Client attempts to join with exponential backoff.
    """
    for attempt in range(max_retries):
        try:
            result = await self.join_custom_game(pregame_id, match_id)
            
            if result['status'] == 'success':
                return result
            
            # Wait before retry (exponential backoff)
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)
    
    raise Exception("Failed to join custom game after multiple attempts")
```

---

## 8. Unique Match Pages & Navigation

### Frontend Routing

```javascript
// client/frontend/src/App.jsx

<Routes>
  <Route path="/" element={<HomePage />} />
  <Route path="/queue" element={<QueuePage />} />
  <Route path="/lobby" element={<LobbyPage />} />
  
  {/* Match Page - Unique per match */}
  <Route path="/match/:matchId" element={<MatchPage />} />
  
  <Route path="/profile" element={<ProfilePage />} />
  <Route path="/settings" element={<SettingsPage />} />
</Routes>
```

### Global Navigation State

```javascript
// client/frontend/src/contexts/MatchContext.jsx

export const MatchContext = createContext();

export function MatchProvider({ children }) {
  const [activeMatch, setActiveMatch] = useState(null);
  const [matchState, setMatchState] = useState(null);
  
  // Listen for match_confirmed event
  useEffect(() => {
    if (!ws) return;
    
    const handleMatchConfirmed = (data) => {
      setActiveMatch(data.match_id);
      setMatchState('CONFIRMED');
      
      // Auto-redirect to match page
      navigate(`/match/${data.match_id}`);
    };
    
    ws.on('match_confirmed', handleMatchConfirmed);
    
    return () => ws.off('match_confirmed', handleMatchConfirmed);
  }, [ws]);
  
  const value = {
    activeMatch,
    matchState,
    setActiveMatch,
    setMatchState
  };
  
  return (
    <MatchContext.Provider value={value}>
      {children}
    </MatchContext.Provider>
  );
}
```

### Global "Match in Progress" Button

```javascript
// client/frontend/src/components/GlobalMatchButton.jsx

export function GlobalMatchButton() {
  const { activeMatch, matchState } = useContext(MatchContext);
  const navigate = useNavigate();
  const location = useLocation();
  
  // Don't show if already on match page
  if (!activeMatch || location.pathname.includes('/match/')) {
    return null;
  }
  
  return (
    <FloatingButton
      onClick={() => navigate(`/match/${activeMatch}`)}
      className="pulse-animation"
    >
      <GameIcon />
      <span>Match in Progress</span>
      <Badge>{getMatchPhaseLabel(matchState)}</Badge>
    </FloatingButton>
  );
}

// Add to App.jsx layout
<div className="app-layout">
  <Navbar />
  <GlobalMatchButton />  {/* Floats over all pages */}
  <Routes>
    {/* ... */}
  </Routes>
</div>
```

### Match Page Component

```javascript
// client/frontend/src/pages/MatchPage.jsx

export function MatchPage() {
  const { matchId } = useParams();
  const { ws } = useContext(WebSocketContext);
  const [matchData, setMatchData] = useState(null);
  const [phase, setPhase] = useState('loading');
  
  // Fetch match data on load
  useEffect(() => {
    ws.send('get_match_data', { match_id: matchId });
  }, [matchId]);
  
  // Listen for match events
  useEffect(() => {
    ws.on('match_data', setMatchData);
    ws.on('veto_started', handleVetoStarted);
    ws.on('map_vetoed', handleMapVetoed);
    ws.on('veto_complete', handleVetoComplete);
    ws.on('side_selected', handleSideSelected);
    ws.on('join_custom_game', handleJoinGame);
    ws.on('match_starting', handleMatchStarting);
    
    return () => {
      ws.off('match_data', setMatchData);
      // ... cleanup all listeners
    };
  }, [ws]);
  
  // Render based on phase
  return (
    <div className="match-page">
      {phase === 'VETO' && <VetoPhase matchData={matchData} />}
      {phase === 'SIDE_SELECTION' && <SideSelectionPhase matchData={matchData} />}
      {phase === 'CREATING' && <WaitingForGamePhase matchData={matchData} />}
      {phase === 'IN_PROGRESS' && <LiveMatchPhase matchData={matchData} />}
    </div>
  );
}
```

---

## 9. Timeline & Milestones

### Week 1-2: Infrastructure
- [ ] Database models (Match, MatchPlayer)
- [ ] WebSocket events (server→client, client→server)
- [ ] Frontend routing (/match/:matchId)
- [ ] Global match context provider
- [ ] Basic match page shell

### Week 2-3: Map Veto
- [ ] Snake draft veto logic (backend)
- [ ] Veto UI component (frontend)
- [ ] Timeout handling (Celery task)
- [ ] Real-time veto updates (WebSocket)
- [ ] Auto-veto on timeout

### Week 3: Side Selection
- [ ] Side selection logic (backend)
- [ ] Side selection UI (frontend)
- [ ] Constructor delegation
- [ ] Timeout handling

### Week 4: Custom Game Creation
- [ ] Constructor client implementation
- [ ] `create_custom_game_for_match()` function
- [ ] Server pregame tracking
- [ ] Join flow for non-constructors
- [ ] Late joiner retry logic

### Week 4-5: Match Monitoring
- [ ] Constructor monitors coregame API
- [ ] Live score updates (WebSocket)
- [ ] Match completion detection
- [ ] Post-match flow

### Week 5: Polish & Testing
- [ ] Global "Match in Progress" button
- [ ] Match page persistence (refresh handling)
- [ ] Error handling & edge cases
- [ ] End-to-end testing with 10 players

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

1. **Review & Approval**: Get stakeholder approval on plan
2. **Database Schema**: Create Django migrations for Match/MatchPlayer models
3. **WebSocket Events**: Define and document all event payloads
4. **Frontend Prototypes**: Create mockups for match page UI
5. **Phased Implementation**: Start with Week 1-2 infrastructure

---

**Document Owner**: Development Team  
**Last Updated**: October 2025  
**Status**: Awaiting Approval


