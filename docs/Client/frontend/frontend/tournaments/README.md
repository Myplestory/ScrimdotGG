# Tournament Pages Architecture

## Overview
Tournament system for organizing and running competitive brackets, including single/double elimination, swiss, and round-robin formats.

---

## Entity Models

```
Tournament (Django) - NEW ENTITY
├── id: UUID (PK)
├── name: string
├── organizer: ForeignKey → Player
├── co_organizers: ManyToMany → Player
├── description: text (markdown)
├── banner_image: ImageField
├── format: string ('single_elim', 'double_elim', 'swiss', 'round_robin')
├── team_size: int (1 for 1v1, 5 for 5v5)
├── max_teams: int
├── registered_teams_count: int
├── min_teams: int (minimum to start)
├── region: string
├── status: string ('upcoming', 'registration', 'running', 'completed', 'cancelled')
├── visibility: string ('public', 'private', 'invite_only')
├── registration_opens: datetime
├── registration_closes: datetime
├── start_date: datetime
├── end_date: datetime (nullable)
├── check_in_required: boolean
├── check_in_opens: datetime
├── check_in_closes: datetime
├── prize_pool: decimal
├── prize_distribution: JSONField
│   └── [{'place': 1, 'prize': '500', 'description': 'First Place'}]
├── rules: text (markdown)
├── map_pool: JSONField [string]
├── match_format: JSONField
│   ├── type: 'bo1' | 'bo3' | 'bo5'
│   ├── map_veto: boolean
│   └── overtime: boolean
├── stream_url: string (nullable)
├── discord_url: string (nullable)
├── admins: ManyToMany → Player
├── created_at: datetime
└── updated_at: datetime

TournamentRegistration (Django) - NEW ENTITY
├── id: UUID (PK)
├── tournament: ForeignKey → Tournament
├── team: ForeignKey → Team (nullable for solo)
├── player: ForeignKey → Player (for solo tournaments)
├── status: string ('registered', 'checked_in', 'disqualified', 'withdrawn')
├── seed: int (for bracket placement)
├── checked_in_at: datetime (nullable)
├── roster_snapshot: JSONField
├── contact_info: JSONField
│   ├── captain_discord: string
│   └── backup_contact: string
├── registered_at: datetime
└── notes: text

TournamentBracket (Django) - NEW ENTITY
├── id: UUID (PK)
├── tournament: ForeignKey → Tournament
├── bracket_type: string ('winners', 'losers', 'main')
├── rounds: JSONField
│   └── [
│       {
│         'round_number': int,
│         'round_name': string,
│         'matches': [UUID] // match IDs
│       }
│     ]
└── generated_at: datetime

TournamentMatch (Django) - NEW ENTITY
├── id: UUID (PK)
├── tournament: ForeignKey → Tournament
├── bracket: ForeignKey → TournamentBracket
├── round_number: int
├── match_number: int
├── participant_a: ForeignKey → TournamentRegistration (nullable)
├── participant_b: ForeignKey → TournamentRegistration (nullable)
├── winner: ForeignKey → TournamentRegistration (nullable)
├── loser: ForeignKey → TournamentRegistration (nullable)
├── scheduled_time: datetime (nullable)
├── status: string ('pending', 'ready', 'in_progress', 'completed', 'forfeit')
├── match_id: ForeignKey → Match (actual game match)
├── score: JSONField
│   ├── participant_a_score: int
│   └── participant_b_score: int
├── maps_played: JSONField
├── vod_url: string (nullable)
├── next_match_winner: ForeignKey → TournamentMatch (nullable)
├── next_match_loser: ForeignKey → TournamentMatch (nullable, for double elim)
└── completed_at: datetime (nullable)

TournamentAnnouncement (Django) - NEW ENTITY
├── id: UUID (PK)
├── tournament: ForeignKey → Tournament
├── author: ForeignKey → Player
├── title: string
├── content: text (markdown)
├── is_important: boolean (pinned at top)
├── created_at: datetime
└── updated_at: datetime
```

---

## Page: Browse Tournaments (`browse.jsx`)

### Purpose
Discover and browse available tournaments

### UI Components
- Tournament grid/list view
- Filters
  - Status (upcoming, registration open, in progress)
  - Region
  - Format
  - Team size
- Search bar
- Sort options (date, prize pool, participants)
- Tournament cards with key info

### Events & Data Flow

#### 1. Get Tournaments

**Frontend → Backend**
```javascript
Event: 'get_tournaments'
Payload: {
  status: string | null,
  region: string | null,
  format: string | null,
  team_size: int | null,
  search_query: string | null,
  sort_by: 'start_date' | 'prize_pool' | 'participants',
  page: int,
  per_page: int
}
```

**Backend → Frontend**
```javascript
Event: 'tournaments_list'
Payload: {
  tournaments: [
    {
      id: UUID,
      name: string,
      organizer: Player,
      banner_image: string,
      format: string,
      team_size: int,
      registered_teams_count: int,
      max_teams: int,
      status: string,
      prize_pool: decimal,
      start_date: timestamp,
      registration_closes: timestamp,
      region: string
    }
  ],
  pagination: {
    current_page: int,
    total_pages: int,
    total_count: int
  }
}
```

#### 2. Get Tournament Details

**Frontend → Backend**
```javascript
Event: 'get_tournament_details'
Payload: {
  tournament_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'tournament_details'
Payload: {
  tournament: {
    id: UUID,
    name: string,
    organizer: Player,
    description: string,
    banner_image: string,
    format: string,
    team_size: int,
    max_teams: int,
    registered_teams_count: int,
    status: string,
    registration_opens: timestamp,
    registration_closes: timestamp,
    start_date: timestamp,
    check_in_required: boolean,
    check_in_opens: timestamp,
    check_in_closes: timestamp,
    prize_pool: decimal,
    prize_distribution: [...],
    rules: string,
    map_pool: [string],
    match_format: {...},
    stream_url: string,
    discord_url: string
  },
  user_registration: {
    registered: boolean,
    status: string | null,
    checked_in: boolean
  } | null
}
```

### Component Hierarchy
```
BrowseTournaments.jsx
├── TournamentFilters
│   ├── StatusFilter
│   ├── RegionFilter
│   ├── FormatFilter
│   └── TeamSizeFilter
├── SearchBar
├── SortSelector
├── ViewToggle (Grid/List)
├── TournamentGrid
│   └── TournamentCard
│       ├── BannerImage
│       ├── TournamentInfo
│       │   ├── Name
│       │   ├── Organizer
│       │   ├── Status Badge
│       │   └── Format Badge
│       ├── ParticipantCount
│       ├── PrizePool
│       ├── Dates
│       └── RegisterButton
└── Pagination
```

---

## Page: My Tournaments (`my.jsx`)

### Purpose
View user's tournament registrations and manage participation

### UI Components
- Tabs: Registered, Checked In, Completed, Organized
- Tournament list with status
- Check-in button (when available)
- Withdraw button
- Quick actions (view bracket, contact admin)

### Events & Data Flow

#### 1. Get User's Tournaments

**Frontend → Backend**
```javascript
Event: 'get_my_tournaments'
Payload: {
  filter: 'registered' | 'checked_in' | 'completed' | 'organized',
  page: int
}
```

**Backend → Frontend**
```javascript
Event: 'my_tournaments'
Payload: {
  tournaments: [
    {
      tournament: Tournament,
      registration: {
        status: string,
        checked_in: boolean,
        seed: int | null
      },
      next_match: {
        match_id: UUID,
        opponent: string,
        scheduled_time: timestamp
      } | null
    }
  ]
}
```

#### 2. Check In

**Frontend → Backend**
```javascript
Event: 'tournament_check_in'
Payload: {
  tournament_id: UUID
}
```

**Backend Processing**
1. Validate check-in window is open
2. Validate user is registered
3. Update registration status to 'checked_in'
4. Record check-in timestamp

**Backend → Frontend**
```javascript
Event: 'check_in_confirmed'
Payload: {
  tournament_id: UUID,
  checked_in_at: timestamp,
  message: 'Successfully checked in'
}
```

#### 3. Withdraw from Tournament

**Frontend → Backend**
```javascript
Event: 'withdraw_from_tournament'
Payload: {
  tournament_id: UUID,
  reason: string (optional)
}
```

**Backend Processing**
1. Update registration status to 'withdrawn'
2. Adjust bracket if already generated
3. Notify tournament admins

**Backend → Frontend**
```javascript
Event: 'withdrawal_confirmed'
Payload: {
  tournament_id: UUID,
  message: string
}
```

### Component Hierarchy
```
MyTournaments.jsx
├── FilterTabs
│   ├── RegisteredTab
│   ├── CheckedInTab
│   ├── CompletedTab
│   └── OrganizedTab
├── TournamentList
│   └── MyTournamentCard
│       ├── TournamentInfo
│       ├── RegistrationStatus
│       ├── NextMatchInfo (if applicable)
│       └── ActionButtons
│           ├── CheckInButton
│           ├── ViewBracketButton
│           ├── WithdrawButton
│           └── ManageButton (for organized)
└── Pagination
```

---

## Page: Create Tournament (`create.jsx`)

### Purpose
Create and configure a new tournament

### UI Components
- Tournament info form
  - Name, description, banner
  - Format selector
  - Team size
  - Max participants
  - Region
- Schedule settings
  - Registration dates
  - Check-in requirements
  - Start date
- Match settings
  - BO1/BO3/BO5
  - Map pool
  - Veto rules
- Prize settings
  - Prize pool
  - Distribution breakdown
- Advanced settings
  - Visibility (public/private)
  - Admin assignments
  - Rules editor
- Preview and create

### Events & Data Flow

#### 1. Create Tournament

**Frontend → Backend**
```javascript
Event: 'create_tournament'
Payload: {
  name: string,
  description: string,
  banner_image: File | base64,
  format: string,
  team_size: int,
  max_teams: int,
  min_teams: int,
  region: string,
  visibility: string,
  registration_opens: timestamp,
  registration_closes: timestamp,
  start_date: timestamp,
  check_in_required: boolean,
  check_in_opens: timestamp,
  check_in_closes: timestamp,
  prize_pool: decimal,
  prize_distribution: [...],
  rules: string,
  map_pool: [string],
  match_format: {...},
  stream_url: string,
  discord_url: string,
  admin_puuids: [string]
}
```

**Backend Processing**
1. Validate all fields
2. Check user permissions (verified account)
3. Upload banner image
4. Create Tournament entity
5. Assign organizer and admins
6. Set initial status

**Backend → Frontend**
```javascript
Event: 'tournament_created'
Payload: {
  tournament: {
    id: UUID,
    name: string,
    status: 'upcoming',
    url: string // redirect URL
  }
}
```

#### 2. Update Tournament Settings

**Frontend → Backend**
```javascript
Event: 'update_tournament'
Payload: {
  tournament_id: UUID,
  updates: {
    // any updateable fields
  }
}
```

**Backend Processing**
1. Validate user is organizer/admin
2. Check what can be updated based on status
3. Update tournament
4. Notify participants if significant changes

#### 3. Generate Bracket

**Frontend → Backend**
```javascript
Event: 'generate_tournament_bracket'
Payload: {
  tournament_id: UUID,
  seeding_method: 'random' | 'by_rank' | 'manual',
  manual_seeds: {
    [registration_id]: seed_number
  } | null
}
```

**Backend Processing**
1. Validate all participants checked in
2. Generate bracket structure based on format
3. Create TournamentMatch entities
4. Link matches for winners/losers progression
5. Broadcast bracket to all participants

**Backend → Frontend**
```javascript
Event: 'bracket_generated'
Payload: {
  tournament_id: UUID,
  bracket: {
    type: string,
    rounds: [...],
    matches: [...]
  }
}
```

### Component Hierarchy
```
CreateTournament.jsx
├── TournamentForm
│   ├── StepIndicator (multi-step form)
│   ├── BasicInfoStep
│   │   ├── NameInput
│   │   ├── DescriptionEditor
│   │   ├── BannerUploader
│   │   ├── FormatSelector
│   │   ├── TeamSizeSelector
│   │   ├── MaxTeamsInput
│   │   └── RegionSelector
│   ├── ScheduleStep
│   │   ├── RegistrationDates
│   │   ├── CheckInSettings
│   │   └── StartDatePicker
│   ├── MatchSettingsStep
│   │   ├── FormatSelector (BO1/BO3/BO5)
│   │   ├── MapPoolSelector
│   │   └── VetoRulesToggle
│   ├── PrizeStep
│   │   ├── PrizePoolInput
│   │   └── DistributionBuilder
│   │       └── PrizeRow
│   ├── RulesStep
│   │   └── MarkdownEditor
│   └── AdvancedStep
│       ├── VisibilitySelector
│       ├── AdminSelector
│       ├── StreamURLInput
│       └── DiscordURLInput
├── PreviewPanel
└── ActionButtons
    ├── SaveDraftButton
    └── CreateButton
```

---

## Page: Tournament History (`history.jsx`)

### Purpose
View past tournament results and statistics

### UI Components
- Completed tournaments list
- Filters (date range, format, region)
- Tournament cards with final standings
- Player statistics across tournaments
- Achievement showcase

### Events & Data Flow

#### 1. Get Tournament History

**Frontend → Backend**
```javascript
Event: 'get_tournament_history'
Payload: {
  player_puuid: string | null, // null for all tournaments
  date_from: timestamp | null,
  date_to: timestamp | null,
  format: string | null,
  region: string | null,
  page: int
}
```

**Backend → Frontend**
```javascript
Event: 'tournament_history'
Payload: {
  tournaments: [
    {
      tournament: Tournament,
      winner: {
        team: Team | null,
        player: Player | null
      },
      final_standings: [
        {
          place: int,
          participant: Team | Player,
          prize: string
        }
      ],
      user_placement: int | null // if user participated
    }
  ],
  user_stats: {
    tournaments_played: int,
    wins: int,
    top_3_finishes: int,
    total_prize_money: decimal
  }
}
```

#### 2. Get Tournament Bracket (Historical)

**Frontend → Backend**
```javascript
Event: 'get_tournament_bracket'
Payload: {
  tournament_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'tournament_bracket'
Payload: {
  tournament: Tournament,
  bracket: {
    type: string,
    rounds: [
      {
        round_number: int,
        round_name: string,
        matches: [
          {
            match_id: UUID,
            participant_a: {...},
            participant_b: {...},
            winner: {...},
            score: {...},
            vod_url: string | null
          }
        ]
      }
    ]
  },
  losers_bracket: {...} | null // for double elimination
}
```

### Component Hierarchy
```
TournamentHistory.jsx
├── HistoryFilters
│   ├── DateRangePicker
│   ├── FormatFilter
│   └── RegionFilter
├── UserStatsCard (if viewing own history)
│   ├── TournamentsPlayed
│   ├── Wins
│   ├── Top3Finishes
│   └── TotalPrizeMoney
├── TournamentHistoryList
│   └── HistoryTournamentCard
│       ├── TournamentInfo
│       ├── WinnerDisplay
│       ├── UserPlacement
│       └── ViewBracketButton
└── BracketModal
    ├── BracketView
    │   └── BracketMatch
    │       ├── Participants
    │       ├── Score
    │       └── VODButton
    └── Losersbracket (if applicable)
```

---

## Backend Django Architecture

### New Django App: `tournaments`

```
tournaments/
├── __init__.py
├── models.py
├── manager.py
├── bracket_generator.py
├── views.py
├── admin.py
├── urls.py
└── migrations/
```

#### Manager Methods

```python
# tournaments/manager.py

class TournamentManager:
    # Tournament CRUD
    async def create_tournament(self, organizer_puuid, tournament_data)
    async def get_tournament(self, tournament_id)
    async def update_tournament(self, tournament_id, updates)
    async def delete_tournament(self, tournament_id)
    async def get_tournaments(self, filters, page, per_page)
    
    # Registration
    async def register_for_tournament(self, tournament_id, team_id=None, player_puuid=None)
    async def withdraw_from_tournament(self, registration_id)
    async def check_in(self, registration_id)
    async def get_registrations(self, tournament_id)
    async def get_user_tournaments(self, player_puuid, filter_type)
    
    # Bracket management
    async def generate_bracket(self, tournament_id, seeding_method, seeds=None)
    async def get_bracket(self, tournament_id)
    async def update_match_result(self, match_id, winner_id, score)
    async def advance_bracket(self, match_id)
    
    # Announcements
    async def create_announcement(self, tournament_id, author_puuid, data)
    async def get_announcements(self, tournament_id)
    
    # Administration
    async def add_admin(self, tournament_id, admin_puuid)
    async def remove_admin(self, tournament_id, admin_puuid)
    async def disqualify_participant(self, registration_id, reason)
    
    # Statistics
    async def get_tournament_stats(self, tournament_id)
    async def get_player_tournament_history(self, player_puuid)
```

#### Bracket Generator

```python
# tournaments/bracket_generator.py

class BracketGenerator:
    def generate_single_elimination(participants, seeding)
    def generate_double_elimination(participants, seeding)
    def generate_swiss(participants, rounds)
    def generate_round_robin(participants)
    
    def calculate_rounds(participant_count, format)
    def seed_participants(participants, method)
    def create_match_structure(rounds, participants)
```

### Database Queries

```python
# Get tournament with registrations
tournament = await sync_to_async(
    Tournament.objects.select_related('organizer')
    .prefetch_related('registrations__team', 'registrations__player')
    .get
)(id=tournament_id)

# Get user's active tournaments
registrations = await sync_to_async(
    TournamentRegistration.objects.filter(
        Q(team__players__puuid=puuid) | Q(player__puuid=puuid),
        tournament__status__in=['registration', 'running'],
        status__in=['registered', 'checked_in']
    ).select_related('tournament')
    .all
)()

# Get bracket matches
matches = await sync_to_async(
    TournamentMatch.objects.filter(
        tournament_id=tournament_id
    ).select_related('participant_a', 'participant_b', 'winner')
    .order_by('round_number', 'match_number')
    .all
)()
```

---

## Implementation Status

### ✅ FULLY IMPLEMENTED

**NONE** - No tournament functionality has been implemented.

### ⚠️ PARTIALLY IMPLEMENTED

1. **Team Model** (`server/scrimgg/models.py`)
   - ⚠️ Basic Team model exists for team tournaments
   - ⚠️ Needs expansion (see League README) for proper team management

2. **Match System** (`server/match_system/`)
   - ✅ Match model with veto system can be reused for tournament matches
   - ✅ Match execution infrastructure exists

### ❌ NOT IMPLEMENTED

1. **Tournament Django App**
   - ❌ No `tournaments` Django app exists in `server/`
   - ❌ Need to create entire app structure

2. **Tournament Models** (`server/tournaments/models.py` - DOES NOT EXIST)
   - ❌ Tournament model - Define tournaments, formats, registration, prizes
   - ❌ TournamentRegistration model - Team/player registration and seeding
   - ❌ TournamentMatch model - Bracket matches with round/position tracking
   - ❌ TournamentBracket model - Bracket state management
   - ❌ TournamentCheckIn model - Check-in tracking before tournament starts
   - ❌ TournamentAdmin model - Admin permissions for tournament management

3. **Tournament Manager** (`server/tournaments/manager.py` - DOES NOT EXIST)
   - ❌ No tournament business logic:
     - create_tournament()
     - register_team()
     - validate_registration()
     - open_check_in()
     - process_check_ins()
     - generate_bracket()
     - seed_teams()
     - record_match_result()
     - advance_bracket()

4. **Bracket Generator** (`server/tournaments/bracket_generator.py` - DOES NOT EXIST)
   - ❌ No bracket generation algorithms:
     - Single elimination bracket
     - Double elimination bracket (winner/loser brackets)
     - Swiss pairing algorithm
     - Round-robin schedule generation
   - ❌ No seeding logic (random, manual, by rating)
   - ❌ No bracket progression logic

5. **Check-In System** (`server/tournaments/checkin_manager.py` - DOES NOT EXIST)
   - ❌ No check-in tracking
   - ❌ No auto-disqualification for missed check-ins
   - ❌ No check-in notifications

6. **Tournament Admin Tools** (`server/tournaments/admin_manager.py` - DOES NOT EXIST)
   - ❌ No admin permissions system
   - ❌ No manual bracket adjustments
   - ❌ No dispute resolution tools
   - ❌ No DQ/forfeit handling

7. **Tournament WebSocket Handlers** (`server/realtime/handlers/tournament_handler.py` - DOES NOT EXIST)
   - ❌ No tournament event handlers:
     - register_for_tournament
     - check_in
     - start_tournament
     - report_match_result
     - challenge_result

8. **Frontend Integration**
   - ❌ No tournament browser page
   - ❌ No tournament creation UI
   - ❌ No bracket display component
   - ❌ No registration UI
   - ❌ No check-in interface
   - ❌ No admin panel

---

## Implementation Priority

### 🔥 HIGH PRIORITY (Foundation)
1. **Create Tournaments Django App** - Set up app structure in `server/tournaments/`
2. **Create Tournament Models** - Tournament, TournamentRegistration, TournamentMatch, TournamentBracket
3. **Implement TournamentManager** - Tournament creation, registration, validation
4. **Create BracketGenerator** - Single elimination and Swiss algorithms
5. **Build Registration System** - Team/player registration with validation
6. **Implement Check-In System** - Check-in tracking and notifications

### 🔶 MEDIUM PRIORITY (Core Features)
7. **Build Bracket Display** - Frontend bracket visualization component
8. **Implement Match Progression** - Auto-advance bracket on match completion
9. **Add Tournament Handlers** - WebSocket events for tournament operations
10. **Create Tournament Browser** - List and filter tournaments
11. **Build Tournament Creation UI** - Form for creating tournaments
12. **Add Admin Tools** - Manual bracket adjustments, DQ handling

### 🔷 LOW PRIORITY (Enhanced Features)
13. **Double Elimination** - Winner/loser bracket system
14. **Round-Robin Format** - Full round-robin tournament support
15. **Seeding Options** - Manual seeding, rating-based seeding
16. **Prize Distribution** - Automatic prize calculation and display
17. **Tournament Stats** - MVP tracking, match statistics
18. **Stream Integration** - Twitch stream embedding
19. **Tournament Templates** - Reusable tournament configurations
20. **Spectator Mode** - Live bracket updates for viewers

---

## Summary

**Overall Status**: ~3% Complete

The tournament system is **entirely unimplemented** except for the underlying Match system (which can be reused for tournament matches). There is no dedicated `tournaments` Django app, no tournament models, no bracket generation algorithms, no managers, no handlers, and no frontend integration.

**What Can Be Reused**:
- Match model and veto system (for tournament matches)
- Match execution infrastructure
- Team model (needs expansion first)

**What's Missing (Everything)**:
- Entire Tournaments Django app
- All tournament models (Tournament, TournamentRegistration, TournamentMatch, TournamentBracket)
- Bracket generation algorithms (single/double elimination, Swiss, round-robin)
- Check-in system
- Tournament lifecycle management (registration → check-in → bracket → matches → completion)
- Admin tools for tournament organizers
- All WebSocket handlers for tournament events
- All frontend pages (browser, creation, bracket display, admin panel)

**Dependencies**:
- Requires Team model expansion (for team tournaments)
- Requires Match system to be stable (already done ✅)
- Should wait until PUG matchmaking and League system are stable

**Estimated Development Time**: 10-16 weeks for full tournament system

**Key Challenges**:
1. **Bracket Generation**: Complex algorithms for different formats
2. **Bracket Progression**: Auto-advancing winners, handling byes
3. **Double Elimination**: Managing winner/loser bracket splits and grand finals
4. **Swiss Pairing**: Round-by-round pairing based on W/L records
5. **Seeding**: Fair seeding algorithms and manual overrides
6. **Check-In System**: Time-limited check-ins with auto-DQ
7. **Admin Tools**: Manual interventions, dispute resolution
8. **Real-Time Updates**: Broadcasting bracket changes to all viewers

**Recommendation**: Tournament system is a **Phase 4+ feature**. It's one of the most complex subsystems and should only be started after:
- ✅ PUG matchmaking is production-ready
- ✅ League system is implemented and tested
- ✅ Team management is fully functional
- ✅ Match system is battle-tested

**Alternative Approach**: Start with a minimal viable tournament:
- Single elimination only
- Manual bracket generation (admin creates matches manually)
- No check-in system (assume all registered teams show up)
- Manual result reporting
- Basic bracket display
This would allow running small tournaments while the full system is being developed.
