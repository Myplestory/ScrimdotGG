# Match Room Page Specification

## Overview
The Match Room is a dedicated page for each match where participants can interact, veto maps, view teams, and spectators can watch live stats.

---

## URL Structure

```
/match/:matchId
```

**Example**: `/match/a3f4b2e1-5678-1234-abcd-ef9876543210`

---

## Access Control

### **Participants** (10 players in the match)
- Full access to match room
- Can participate in map veto
- Can see team voice chat info
- Can ready up
- Can see match configuration

### **Spectators** (non-participants)
- Read-only access
- Can view teams, stats, scores
- Cannot participate in veto
- Cannot see voice chat details
- Cannot interact with match controls

### **Public/Private**
- All matches are **publicly viewable** by default
- Future: Add private match option

---

## Page Layout

### **Header Section**
```
┌─────────────────────────────────────────────────────────┐
│  MATCH #A3F4B2E1                    [LIVE] 🔴          │
│  5v5 Competitive • Virginia Server • Started 2m ago    │
└─────────────────────────────────────────────────────────┘
```

**Data**:
- Match ID (short version, first 8 chars)
- Match status (WAITING / VETO / LIVE / COMPLETED)
- Game mode (5v5 Competitive)
- Server region
- Time elapsed/remaining

---

### **Team Display**

```
┌──────────────── TEAM A ────────────────┐  ┌──────────────── TEAM B ────────────────┐
│ ⭐ Captain: evisc#erate                │  │ ⭐ Captain: Player5                     │
│                                        │  │                                        │
│ Players:                               │  │ Players:                               │
│  1. evisc#erate    [READY] ✅  A 6493 │  │  1. Player5        [READY] ✅  A 6400  │
│  2. Player2        [READY] ✅  A 6450 │  │  2. Player6        [WAIT]  ⏳  A 6350  │
│  3. Player3        [WAIT]  ⏳  A- 6100 │  │  3. Player7        [READY] ✅  B+ 5900 │
│  4. Player4        [READY] ✅  B+ 5950 │  │  4. Player8        [READY] ✅  B  5700 │
│  5. QueueBot1      [READY] ✅  A 6500 │  │  5. QueueBot5      [READY] ✅  A 6480  │
│                                        │  │                                        │
│ Avg MMR: 6180      Avg ELO: 6299      │  │ Avg MMR: 6165      Avg ELO: 6266      │
│ Discord: [JOIN VOICE] 🎙️              │  │ Discord: [JOIN VOICE] 🎙️              │
└────────────────────────────────────────┘  └────────────────────────────────────────┘
```

**Data per player**:
- Alias
- Ready status (READY ✅ / WAITING ⏳)
- Display rank + ELO
- Captain indicator (⭐)

**Team stats**:
- Average MMR (hidden from spectators, shown to participants)
- Average Display ELO
- Discord voice channel link (participants only)

---

### **Map Veto Phase**

```
┌──────────────────────────────────────────────────────────────────────┐
│                          MAP VETO                                    │
│  Team A Captain's Turn • Action: BAN                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [Ascent]     [Bind]      [Breeze]    [Fracture]   [Haven]          │
│   Available   Available    Available   Available   Available         │
│                                                                       │
│  [Icebox]     [Lotus]     [Pearl]     [Split]                       │
│   BANNED (A)  Available   Available   Available                      │
│                                                                       │
│  Veto History:                                                       │
│  1. Team A banned Icebox                                            │
│  2. Waiting for Team A...                                           │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**Veto Process** (Standard competitive format):
1. Team A **bans** 1 map
2. Team B **bans** 1 map
3. Team A **picks** 1 map (Map 1)
4. Team B **picks** 1 map (Map 2)
5. Team A **bans** 1 map
6. Team B **bans** 1 map
7. Remaining map = **Decider** (Map 3, if needed)

**Final result**: Best of 3 (BO3) with predetermined map order

**UI Elements**:
- Map cards showing map name + thumbnail
- Visual indication of status (Available / Banned / Picked)
- Turn indicator (which captain's turn)
- Action indicator (BAN / PICK)
- Veto history log
- Countdown timer per veto turn (30 seconds, auto-random if timeout)

---

### **Match Configuration**

```
┌──────────────────────────────────────────────────────────────────────┐
│                      MATCH SETTINGS                                  │
├──────────────────────────────────────────────────────────────────────┤
│  Format: Best of 3 (BO3)                                            │
│  Overtime: MR3 (First to 13 wins)                                   │
│  Server: Virginia (NA East)                                         │
│  Game Server: Connecting...                                         │
│                                                                       │
│  Maps:                                                               │
│  1. Ascent (Team A pick)                                            │
│  2. Haven (Team B pick)                                             │
│  3. Bind (Decider, if needed)                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

### **Live Match Stats** (During game)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    LIVE MATCH - Map 1: Ascent                        │
│                    TEAM A [5] - [4] TEAM B                           │
│                    Round 10/24 • ATK/DEF                             │
├──────────────────────────────────────────────────────────────────────┤
│  Team A (ATK)                                           Team B (DEF) │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────┤
│  │ Player        K  D  A  ACS  ADR         │  │ Player      K  D  A │
│  │ evisc#erate   12 8  3  245  150         │  │ Player5    10 10 5  │
│  │ Player2       10 9  5  220  145         │  │ Player6     9 11 4  │
│  │ Player3        8 10 7  200  130         │  │ Player7    11  9 6  │
│  │ Player4        9  9  4  215  140         │  │ Player8     8 10 3  │
│  │ QueueBot1     11  8  6  230  148         │  │ QueueBot5  10  8 7  │
│  └─────────────────────────────────────────┘  └─────────────────────┘
└──────────────────────────────────────────────────────────────────────┘
```

**Live data** (updates every 5-10 seconds):
- Current score
- Round number
- Round timer
- Player stats (K/D/A, ACS, ADR)
- Economy (if available from game server)

---

### **Post-Match Results**

```
┌──────────────────────────────────────────────────────────────────────┐
│                        MATCH COMPLETE                                │
│                    TEAM A [2] - [1] TEAM B                           │
│                       🏆 TEAM A WINS                                 │
├──────────────────────────────────────────────────────────────────────┤
│  Map 1: Ascent     - Team A won 13-10                               │
│  Map 2: Haven      - Team B won 13-8                                │
│  Map 3: Bind       - Team A won 13-11                               │
│                                                                       │
│  Match MVP: evisc#erate (28K, 267 ACS, 1.45 K/D)                    │
│                                                                       │
│  ELO Changes:                                                        │
│  Team A: +25 ELO each                                               │
│  Team B: -25 ELO each                                               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Backend Data Structure

### **Match Model** (Enhanced)

```python
class Match(models.Model):
    # Identification
    match_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    match_confirmation_id = models.UUIDField(null=True)  # Link to confirmation
    
    # Teams
    team_a_players = models.ManyToManyField(Player, related_name='team_a_matches')
    team_b_players = models.ManyToManyField(Player, related_name='team_b_matches')
    team_a_captain = models.ForeignKey(Player, related_name='captain_a_matches', on_delete=models.SET_NULL, null=True)
    team_b_captain = models.ForeignKey(Player, related_name='captain_b_matches', on_delete=models.SET_NULL, null=True)
    
    # Team stats
    team_a_avg_mmr = models.FloatField(default=0.0)
    team_b_avg_mmr = models.FloatField(default=0.0)
    team_a_avg_elo = models.FloatField(default=0.0)
    team_b_avg_elo = models.FloatField(default=0.0)
    
    # Configuration
    game_mode = models.CharField(max_length=20, default='5v5')  # '5v5', '10mans', etc
    format = models.CharField(max_length=20, default='bo3')  # 'bo1', 'bo3', 'bo5'
    server_region = models.CharField(max_length=50)
    
    # Maps
    map_pool = models.JSONField(default=list)  # Original available maps
    veto_history = models.JSONField(default=list)  # Veto actions log
    map_order = models.JSONField(default=list)  # Final map order: ['Ascent', 'Haven', 'Bind']
    map_picks = models.JSONField(default=dict)  # {'map_1': 'team_a', 'map_2': 'team_b', 'map_3': 'decider'}
    
    # Status
    status = models.CharField(max_length=20, default='waiting')  
    # 'waiting' -> 'ready_check' -> 'veto' -> 'connecting' -> 'live' -> 'completed' -> 'cancelled'
    
    veto_phase = models.CharField(max_length=20, default='pending')  
    # 'pending' -> 'team_a_ban_1' -> 'team_b_ban_1' -> 'team_a_pick' -> 'team_b_pick' -> 'team_a_ban_2' -> 'team_b_ban_2' -> 'complete'
    
    current_veto_team = models.CharField(max_length=10, default='team_a')  # 'team_a' or 'team_b'
    current_veto_action = models.CharField(max_length=10, default='ban')  # 'ban' or 'pick'
    veto_deadline = models.DateTimeField(null=True)  # 30 second timer
    
    # Player ready status
    players_ready = models.JSONField(default=list)  # List of player PUUIDs who are ready
    
    # Game server
    game_server_id = models.CharField(max_length=100, null=True, blank=True)
    game_server_ip = models.CharField(max_length=100, null=True, blank=True)
    game_server_password = models.CharField(max_length=100, null=True, blank=True)
    pregame_id = models.CharField(max_length=100, null=True, blank=True)  # Valorant pregame ID
    
    # Scores
    team_a_score = models.IntegerField(default=0)  # Maps won
    team_b_score = models.IntegerField(default=0)
    map_scores = models.JSONField(default=list)  # [{'map': 'Ascent', 'team_a': 13, 'team_b': 10}, ...]
    
    # Stats
    player_stats = models.JSONField(default=dict)  # {puuid: {kills, deaths, assists, acs, adr, ...}}
    match_mvp = models.ForeignKey(Player, related_name='mvp_matches', on_delete=models.SET_NULL, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    veto_started_at = models.DateTimeField(null=True)
    match_started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    
    # Discord
    team_a_voice_channel = models.CharField(max_length=200, null=True)
    team_b_voice_channel = models.CharField(max_length=200, null=True)
    
    # Visibility
    is_public = models.BooleanField(default=True)
```

---

## WebSocket Events

### **For Participants**

```javascript
// Join match room
ws.send({
  type: 'join_match_room',
  payload: {
    match_id: 'a3f4b2e1-...',
    player_puuid: 'player-uuid'
  }
})

// Player ready up
ws.send({
  type: 'player_ready',
  payload: {
    match_id: 'a3f4b2e1-...',
    player_puuid: 'player-uuid'
  }
})

// Veto action (captain only)
ws.send({
  type: 'veto_action',
  payload: {
    match_id: 'a3f4b2e1-...',
    captain_puuid: 'captain-uuid',
    action: 'ban',  // 'ban' or 'pick'
    map: 'Icebox'
  }
})
```

### **Received Events**

```javascript
// Player joined room
{
  type: 'player_joined_room',
  payload: {
    player_puuid: '...',
    alias: 'evisc#erate'
  }
}

// Player ready status changed
{
  type: 'player_ready_update',
  payload: {
    player_puuid: '...',
    is_ready: true,
    ready_count: 8,
    total_players: 10
  }
}

// Veto phase update
{
  type: 'veto_update',
  payload: {
    veto_history: [...],
    current_team: 'team_b',
    current_action: 'ban',
    available_maps: ['Ascent', 'Bind', ...],
    deadline: '2025-10-12T20:35:00Z'
  }
}

// Veto complete
{
  type: 'veto_complete',
  payload: {
    map_order: ['Ascent', 'Haven', 'Bind'],
    map_picks: {...}
  }
}

// Match starting
{
  type: 'match_starting',
  payload: {
    game_server_ip: '192.168.1.100:7777',
    password: 'match123',
    connect_command: 'valorant://connect?ip=...'
  }
}

// Live stats update
{
  type: 'match_stats_update',
  payload: {
    current_map: 'Ascent',
    round: 10,
    team_a_rounds: 5,
    team_b_rounds: 4,
    player_stats: {...}
  }
}

// Match complete
{
  type: 'match_complete',
  payload: {
    winner: 'team_a',
    final_score: { team_a: 2, team_b: 1 },
    map_scores: [...],
    mvp: {...},
    elo_changes: {...}
  }
}
```

---

 

## API Endpoints

```
GET    /api/match/:matchId              - Get match details
POST   /api/match/:matchId/ready        - Mark player as ready
POST   /api/match/:matchId/veto         - Submit veto action (captain only)
GET    /api/match/:matchId/stats        - Get current match stats
POST   /api/match/:matchId/connect      - Get game server connect info
```

---

 

