# Scrim Page Architecture

## Overview
The Scrim page allows players to create and manage custom scrim matches (practice matches between teams).

---

## Scrim Page - Full Architecture

### UI Components
- Scrim type selector (5v5, 10-man, custom)
- Team setup interface
- Map selection (single map or BO3/BO5)
- Server selection
- Match settings (overtime, tournament mode, etc.)
- Team captain selection
- Player invitation system
- Ready check system

### Entity Relationships

#### Primary Entities
```
Player (Django) - Same as Play page

Lobby (Django)
├── Same base structure as Play page
└── Additional fields for scrims:
    ├── queue_type: 'scrim'
    └── match_format: JSONField
        ├── type: '5v5' | '10man' | 'custom'
        ├── map_selection: 'single' | 'bo3' | 'bo5'
        ├── maps: [string]
        └── settings: {...}

ScrimInvite (Django) - NEW ENTITY NEEDED
├── id: UUID (PK)
├── lobby: ForeignKey → Lobby
├── inviter: ForeignKey → Player
├── invitee: ForeignKey → Player (nullable for team invites)
├── invitee_team: ForeignKey → Team (nullable)
├── invite_type: string ('player' | 'team')
├── status: string ('pending', 'accepted', 'declined', 'expired')
├── message: text
├── created_at: datetime
├── expires_at: datetime
└── responded_at: datetime

Match (Django)
├── All base Match fields
└── Additional scrim-specific fields:
    ├── is_scrim: boolean
    ├── scrim_format: JSONField
    │   ├── type: string
    │   ├── map_count: int
    │   └── maps: [string]
    └── team_names: JSONField
        ├── team_a_name: string
        └── team_b_name: string
```

### Frontend State Management

#### Scrim-Specific State
```javascript
{
  // Scrim setup state
  scrimSetup: {
    scrim_type: '5v5' | '10man' | 'custom',
    team_a: {
      name: string,
      tag: string,
      players: [Player],
      captain: Player,
      ready: boolean
    },
    team_b: {
      name: string,
      tag: string,
      players: [Player],
      captain: Player,
      ready: boolean
    },
    match_format: {
      map_selection: 'single' | 'bo3' | 'bo5',
      selected_maps: [string],
      server: string,
      overtime: boolean,
      tournament_mode: boolean
    }
  },
  
  // Invitation state
  pendingInvites: [{
    invite_id: UUID,
    inviter: Player,
    lobby_id: UUID,
    scrim_details: {...},
    expires_at: timestamp
  }],
  
  // Ready check state
  readyCheck: {
    initiated_at: timestamp,
    ready_players: [PUUID],
    not_ready_players: [PUUID],
    timeout_at: timestamp
  }
}
```

### Events & Data Flow

#### 1. Create Scrim Lobby

**Frontend → Backend**
```javascript
Event: 'create_scrim_lobby'
Payload: {
  scrim_type: '5v5' | '10man' | 'custom',
  match_format: {
    map_selection: 'single' | 'bo3' | 'bo5',
    maps: [string],
    server: string,
    settings: {
      overtime: boolean,
      tournament_mode: boolean,
      allow_pause: boolean
    }
  }
}
```

**Backend Processing**
1. Create Lobby with queue_type='scrim'
2. Initialize team structures
3. Set creator as captain of Team A
4. Create lobby WebSocket group

**Backend → Frontend**
```javascript
Event: 'scrim_lobby_created'
Payload: {
  lobby: {
    id: UUID,
    queue_type: 'scrim',
    scrim_type: string,
    match_format: {...},
    team_a: {
      captain: Player,
      players: [Player],
      ready: false
    },
    team_b: {
      captain: null,
      players: [],
      ready: false
    }
  }
}
```

#### 2. Send Scrim Invite

**Frontend → Backend**
```javascript
Event: 'send_scrim_invite'
Payload: {
  lobby_id: UUID,
  invite_type: 'player' | 'team',
  invitee_puuid: string | null,
  invitee_team_id: UUID | null,
  message: string
}
```

**Backend Processing**
1. Create ScrimInvite entity
2. Validate invitee exists
3. Send notification to invitee
4. Set expiration (15 minutes)

**Backend → Frontend (To Invitee)**
```javascript
Event: 'scrim_invite_received'
Payload: {
  invite_id: UUID,
  lobby_id: UUID,
  inviter: {
    puuid: string,
    alias: string,
    rank: string
  },
  scrim_details: {
    scrim_type: string,
    map_format: string,
    maps: [string],
    server: string
  },
  message: string,
  expires_at: timestamp
}
```

#### 3. Accept/Decline Scrim Invite

**Frontend → Backend**
```javascript
Event: 'respond_to_scrim_invite'
Payload: {
  invite_id: UUID,
  response: 'accept' | 'decline'
}
```

**Backend Processing (If Accept)**
1. Update ScrimInvite status
2. Add player(s) to Team B
3. If team invite, assign team captain
4. Broadcast lobby update

**Backend → Frontend (To All Lobby Members)**
```javascript
Event: 'scrim_lobby_update'
Payload: {
  lobby_id: UUID,
  team_b: {
    captain: Player | null,
    players: [Player],
    ready: false
  },
  message: '{player} joined Team B'
}
```

#### 4. Assign Team Captain

**Frontend → Backend**
```javascript
Event: 'assign_scrim_captain'
Payload: {
  lobby_id: UUID,
  team: 'team_a' | 'team_b',
  captain_puuid: string
}
```

**Backend Processing**
1. Validate captain is in team
2. Update lobby team structure
3. Broadcast change

**Backend → Frontend**
```javascript
Event: 'scrim_captain_assigned'
Payload: {
  lobby_id: UUID,
  team: string,
  captain: Player
}
```

#### 5. Ready Check

**Frontend → Backend**
```javascript
Event: 'scrim_ready_check'
Payload: {
  lobby_id: UUID
}
```

**Backend Processing**
1. Initiate ready check timer (60 seconds)
2. Reset all player ready states
3. Broadcast to all players

**Backend → Frontend (To All)**
```javascript
Event: 'ready_check_initiated'
Payload: {
  lobby_id: UUID,
  initiated_by: Player,
  timeout_at: timestamp,
  timeout_seconds: 60
}
```

**Frontend → Backend**
```javascript
Event: 'player_ready'
Payload: {
  lobby_id: UUID,
  ready: boolean
}
```

**Backend → Frontend (Real-time)**
```javascript
Event: 'ready_check_update'
Payload: {
  lobby_id: UUID,
  ready_players: [PUUID],
  not_ready_players: [PUUID],
  ready_count: int,
  total_count: int
}
```

#### 6. Start Scrim Match

**Backend → Frontend (When All Ready)**
```javascript
Event: 'scrim_starting'
Payload: {
  lobby_id: UUID,
  match_id: UUID,
  match_format: {...},
  team_a: {...},
  team_b: {...},
  starting_in_seconds: 10
}
```

### Backend Django Architecture

#### New Models Required

```python
# scrimgg/models.py additions

class ScrimInvite(models.Model):
    INVITE_TYPE_CHOICES = [
        ('player', 'Player Invite'),
        ('team', 'Team Invite'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    lobby = models.ForeignKey(Lobby, on_delete=models.CASCADE, related_name='invites')
    inviter = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sent_scrim_invites')
    
    # Either player OR team invite
    invitee = models.ForeignKey(Player, null=True, blank=True, on_delete=models.CASCADE, related_name='received_scrim_invites')
    invitee_team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.CASCADE, related_name='scrim_invites')
    
    invite_type = models.CharField(max_length=10, choices=INVITE_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['invitee', 'status']),
        ]

# Update Lobby model
class Lobby(models.Model):
    # ... existing fields ...
    
    # Scrim-specific fields
    scrim_format = models.JSONField(default=dict, blank=True)
    # Structure:
    # {
    #   'type': '5v5' | '10man' | 'custom',
    #   'map_selection': 'single' | 'bo3' | 'bo5',
    #   'maps': [string],
    #   'settings': {
    #     'overtime': boolean,
    #     'tournament_mode': boolean,
    #     'allow_pause': boolean
    #   }
    # }
    
    team_a_captain = models.ForeignKey(Player, null=True, blank=True, on_delete=models.SET_NULL, related_name='captained_team_a')
    team_b_captain = models.ForeignKey(Player, null=True, blank=True, on_delete=models.SET_NULL, related_name='captained_team_b')
    
    team_a_ready = models.BooleanField(default=False)
    team_b_ready = models.BooleanField(default=False)
    
    ready_check_active = models.BooleanField(default=False)
    ready_check_started_at = models.DateTimeField(null=True, blank=True)
    ready_players = models.JSONField(default=list)  # List of PUUIDs
```

#### New Manager Methods

```python
# lobby/manager.py additions

class ScrimManager:
    async def create_scrim_lobby(self, creator_puuid, scrim_config):
        """Create a scrim lobby with team structure"""
        
    async def send_scrim_invite(self, lobby_id, inviter_puuid, invite_config):
        """Send scrim invite to player or team"""
        
    async def respond_to_invite(self, invite_id, response, responder_puuid):
        """Accept or decline scrim invite"""
        
    async def assign_captain(self, lobby_id, team, captain_puuid):
        """Assign team captain"""
        
    async def initiate_ready_check(self, lobby_id, initiator_puuid):
        """Start ready check for all players"""
        
    async def update_ready_status(self, lobby_id, player_puuid, ready):
        """Update player ready status"""
        
    async def check_all_ready(self, lobby_id):
        """Check if all players are ready and start match"""
        
    async def start_scrim_match(self, lobby_id):
        """Create match and transition to match page"""
```

### Frontend Component Hierarchy

```
Scrim.jsx
├── ScrimTypeSelector
│   └── TypeCard (5v5, 10-man, custom)
├── TeamSetup
│   ├── TeamAPanel
│   │   ├── TeamNameInput
│   │   ├── CaptainSelector
│   │   └── PlayerList
│   │       └── PlayerSlot
│   └── TeamBPanel
│       ├── InviteButton
│       ├── CaptainSelector
│       └── PlayerList
│           └── PlayerSlot
├── MatchFormatSelector
│   ├── MapSelectionMode (Single, BO3, BO5)
│   ├── MapPicker
│   └── SettingsPanel
│       ├── OvertimeToggle
│       ├── TournamentModeToggle
│       └── PauseToggle
├── ServerSelector
├── InviteModal
│   ├── InviteTypeTab (Player, Team)
│   ├── PlayerSearch
│   ├── TeamSearch
│   └── MessageInput
├── ReadyCheckModal
│   ├── PlayerReadyList
│   │   └── PlayerReadyStatus
│   ├── CountdownTimer
│   └── ReadyButton
└── PendingInvitesPanel
    └── InviteCard
        ├── InviterInfo
        ├── ScrimDetails
        └── AcceptDeclineButtons
```

### Database Queries

```python
# Get all pending invites for player
invites = await sync_to_async(
    ScrimInvite.objects.filter(
        invitee=player,
        status='pending',
        expires_at__gt=timezone.now()
    ).select_related('inviter', 'lobby').all
)()

# Get lobby with team structure
lobby = await sync_to_async(
    Lobby.objects.select_related(
        'lobby_leader',
        'team_a_captain',
        'team_b_captain'
    ).prefetch_related('players').get
)(id=lobby_id)

# Check if all players are ready
ready_count = len(lobby.ready_players)
total_count = await sync_to_async(lobby.players.count)()
all_ready = ready_count == total_count and ready_count >= 10
```

### Redis Data Structures

```python
# Ready check state (Redis Hash)
Key: f"lobby:{lobby_id}:ready_check"
Fields:
  - active: boolean
  - started_at: timestamp
  - timeout_at: timestamp
  - ready_players: JSON array of PUUIDs

# Scrim invites cache (Redis Hash with TTL)
Key: f"player:{puuid}:pending_scrim_invites"
TTL: 900 seconds (15 minutes)
Value: JSON array of invite objects
```

### Error Handling

```javascript
// Invite errors
{
  error: 'invite_failed',
  reason: 'PLAYER_NOT_FOUND' | 'PLAYER_IN_MATCH' | 'ALREADY_INVITED' | 'TEAM_FULL',
  message: string
}

// Ready check errors
{
  error: 'ready_check_failed',
  reason: 'ALREADY_ACTIVE' | 'NOT_ENOUGH_PLAYERS' | 'TEAMS_UNBALANCED',
  message: string
}

// Match start errors
{
  error: 'scrim_start_failed',
  reason: 'NOT_ALL_READY' | 'TEAMS_INCOMPLETE' | 'INVALID_FORMAT',
  message: string
}
```

### Testing Requirements

1. **Unit Tests**
   - Scrim lobby creation
   - Invite send/receive/respond
   - Captain assignment
   - Ready check logic
   
2. **Integration Tests**
   - Full scrim setup flow
   - Team invitation flow
   - Ready check timeout handling
   
3. **E2E Tests**
   - Create scrim → invite players → ready check → match start

---

## Implementation Status

### ✅ FULLY IMPLEMENTED

1. **Core Infrastructure** (`server/scrimgg/models.py`, `server/realtime/`)
   - ✅ Basic Lobby model with player tracking and leader
   - ✅ WebSocket handlers for lobby events (create, invite, kick)
   - ✅ Match model with team tracking
   - ✅ LobbyManager with create_lobby functionality

2. **Match System** (`server/match_system/`)
   - ✅ Match model with team_a/team_b player lists
   - ✅ Captain tracking (team_a_captain_puuid, team_b_captain_puuid)
   - ✅ Match creation from scrim lobbies possible

### ⚠️ PARTIALLY IMPLEMENTED / NEEDS ENHANCEMENT

1. **Lobby Model Scrim Fields** (`server/scrimgg/models.py`)
   - ⚠️ Lobby model exists but lacks scrim-specific fields:
     - ❌ team_a_captain (ForeignKey → Player)
     - ❌ team_b_captain (ForeignKey → Player)
     - ❌ ready_players (JSONField for ready check)
     - ❌ ready_check_active (BooleanField)
     - ❌ ready_check_started_at (DateTimeField)
     - ❌ scrim_format (CharField: '5v5', '10-man', 'custom')
     - ❌ match_format (JSONField: BO1/BO3/BO5, map pool, settings)

2. **Team Structure**
   - ⚠️ Match model has team_a_players and team_b_players (JSONField)
   - ⚠️ Need explicit team assignment in Lobby before match creation
   - ⚠️ Need captain selection and validation

### ❌ NOT IMPLEMENTED

1. **ScrimInvite Model** (`server/scrimgg/models.py`)
   - ❌ Entire model missing:
     ```python
     class ScrimInvite(models.Model):
         id: UUID
         lobby: ForeignKey → Lobby
         inviter: ForeignKey → Player
         invitee: ForeignKey → Player (nullable)
         invitee_team: ForeignKey → Team (nullable)
         status: CharField ('pending', 'accepted', 'declined', 'expired')
         message: TextField
         expires_at: DateTimeField
         responded_at: DateTimeField
         created_at: DateTimeField
     ```

2. **ScrimManager** (`server/lobby/scrim_manager.py`)
   - ❌ No dedicated ScrimManager class
   - ❌ Need scrim-specific business logic:
     - create_scrim_lobby()
     - send_scrim_invite()
     - respond_to_invite()
     - assign_captain()
     - initiate_ready_check()
     - update_ready_status()
     - check_all_ready()
     - start_scrim_match()

3. **Scrim WebSocket Handlers** (`server/realtime/handlers/`)
   - ❌ No scrim_handler.py for scrim-specific events
   - ❌ Need handlers for:
     - send_scrim_invite
     - respond_to_scrim_invite
     - assign_team_captain
     - start_ready_check
     - update_ready_status
     - cancel_ready_check

4. **Ready Check System**
   - ❌ No ready check state tracking
   - ❌ No timeout handling for ready checks
   - ❌ No broadcasting of ready status updates
   - ❌ No automatic match start on all-ready

5. **Team Invitation System**
   - ❌ No team-based invites (only player invites exist)
   - ❌ No bulk team roster invitation
   - ❌ No team captain invite acceptance

6. **Scrim Notifications**
   - ❌ No invite notification system
   - ❌ No pending invite tracking
   - ❌ No invite expiration handling

7. **Frontend Integration**
   - ❌ No scrim.jsx integration with backend
   - ❌ No team setup UI
   - ❌ No ready check modal
   - ❌ No invite acceptance UI

---

## Implementation Priority

### 🔥 HIGH PRIORITY (Core Scrim Functionality)
1. **Extend Lobby Model** - Add team_a_captain, team_b_captain, ready_players, scrim_format fields
2. **Create ScrimInvite Model** - Full invite system with player/team support
3. **Create ScrimManager** - Dedicated manager for scrim business logic
4. **Implement Ready Check** - State tracking, timeout, and broadcasting
5. **Add Scrim Handlers** - WebSocket handlers for scrim events
6. **Frontend Scrim UI** - Basic team setup and invite interface

### 🔶 MEDIUM PRIORITY (Enhanced Scrim Experience)
1. **Team Captain System** - Captain assignment, permissions, and validation
2. **Match Format Config** - BO3/BO5 support, map pool selection, overtime settings
3. **Invite Notifications** - Real-time invite delivery and expiration
4. **Ready Check Enhancements** - Auto-unready on disconnect, captain-only start
5. **Team Bulk Invites** - Invite entire team roster at once

### 🔷 LOW PRIORITY (Advanced Features)
1. **Scrim History** - Track past scrims between teams
2. **Scrim Templates** - Save and reuse scrim configurations
3. **Scrim Scheduling** - Schedule scrims for future time
4. **Private Scrim Codes** - Invite via shareable code
5. **Scrim Chat** - Dedicated team-based chat channels

---

## Summary

**Overall Status**: ~30% Complete

The foundational infrastructure exists (Lobby model, WebSocket handlers, Match system), but **scrim-specific features are almost entirely missing**. The current implementation can handle basic lobby creation and player management, but lacks the team structure, invitation system, and ready check mechanics that differentiate scrims from PUG matchmaking.

**What's Working**:
- Basic lobby creation and player management
- WebSocket event routing for lobbies
- Match creation with team tracking
- Captain tracking in Match model

**Critical Gaps**:
- No ScrimInvite model or invitation system
- No ready check implementation
- Lobby model lacks team/captain fields
- No scrim-specific WebSocket handlers
- No frontend integration

**Dependencies**:
- Requires Lobby model expansion first (add scrim fields)
- Requires ScrimInvite model creation
- Requires ScrimManager implementation
- Frontend depends on backend handlers being ready

**Next Immediate Steps**:
1. Add scrim fields to Lobby model (team_a_captain, team_b_captain, ready_players, etc.)
2. Create ScrimInvite model with full schema
3. Build ScrimManager with invite and ready check logic
4. Add scrim WebSocket handlers
5. Build frontend scrim UI and integrate with backend

**Recommendation**: Scrim system should be **Phase 2** implementation after PUG matchmaking is stable. The invitation and ready check systems are complex and require dedicated development time. Consider starting with a simplified "custom 10-man" mode that reuses PUG infrastructure before building full scrim features.
