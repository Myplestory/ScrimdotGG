# League Pages Architecture

## Overview
League pages handle competitive team-based league play, including team management, registration, standings, and scheduling.

---

## Entity Overview

### Core League Entities

```
League (Django) - NEW ENTITY
├── id: UUID (PK)
├── name: string
├── season: string
├── division: string ('Premier', 'Advanced', 'Intermediate', 'Open')
├── region: string
├── max_teams: int
├── registered_teams_count: int
├── status: string ('registration', 'active', 'playoffs', 'completed')
├── registration_opens: datetime
├── registration_closes: datetime
├── season_starts: datetime
├── season_ends: datetime
├── entry_fee: decimal
├── prize_pool: decimal
├── format: JSONField
│   ├── type: 'round_robin' | 'swiss' | 'double_elimination'
│   ├── matches_per_week: int
│   ├── playoffs_format: string
│   └── map_pool: [string]
├── rules: text
└── created_at: datetime

Team (Django) - EXPAND EXISTING
├── id: UUID (PK)
├── name: string
├── tag: string (3-5 chars)
├── logo: ImageField
├── owner: ForeignKey → Player (team owner/manager)
├── captain: ForeignKey → Player (in-game leader)
├── players: ManyToMany → Player (through TeamMember)
├── active_roster: ManyToMany → Player (5 starters)
├── substitute_roster: ManyToMany → Player (up to 2 subs)
├── region: string
├── division: string
├── verified: boolean (verified teams get special badges)
├── created_at: datetime
└── Stats:
    ├── wins: int
    ├── losses: int
    ├── total_rounds_won: int
    ├── total_rounds_lost: int
    ├── current_streak: int
    └── team_history: JSONField

TeamMember (Django) - NEW ENTITY
├── id: UUID (PK)
├── team: ForeignKey → Team
├── player: ForeignKey → Player
├── role: string ('IGL', 'Entry', 'AWP', 'Lurk', 'Support', 'Substitute')
├── status: string ('active', 'inactive', 'suspended')
├── joined_at: datetime
├── left_at: datetime (nullable)
└── stats_with_team: JSONField

LeagueRegistration (Django) - NEW ENTITY
├── id: UUID (PK)
├── league: ForeignKey → League
├── team: ForeignKey → Team
├── status: string ('pending', 'confirmed', 'waitlist', 'rejected')
├── payment_status: string ('unpaid', 'processing', 'paid', 'refunded')
├── payment_id: string
├── roster_snapshot: JSONField (locked roster at registration time)
├── registered_at: datetime
├── confirmed_at: datetime
└── paid_at: datetime

LeagueMatch (Django) - NEW ENTITY
├── id: UUID (PK)
├── league: ForeignKey → League
├── week: int
├── match_number: int
├── team_a: ForeignKey → Team
├── team_b: ForeignKey → Team
├── scheduled_time: datetime
├── match_id: ForeignKey → Match (links to actual match when played)
├── status: string ('scheduled', 'live', 'completed', 'forfeit', 'postponed')
├── team_a_score: int
├── team_b_score: int
├── winner: ForeignKey → Team (nullable)
├── maps_played: JSONField
│   └── [{map: string, team_a_score: int, team_b_score: int}]
├── vod_url: string
└── stats_recorded: boolean

LeagueStanding (Django) - NEW ENTITY
├── id: UUID (PK)
├── league: ForeignKey → League
├── team: ForeignKey → Team
├── rank: int
├── wins: int
├── losses: int
├── ties: int (if applicable)
├── maps_won: int
├── maps_lost: int
├── rounds_won: int
├── rounds_lost: int
├── round_differential: int
├── points: int
├── streak: string ('W3', 'L2', etc.)
└── last_updated: datetime

Profile (Django) - NEW ENTITY (Player profile extension)
├── player: OneToOne → Player
├── bio: text
├── social_links: JSONField
│   ├── twitter: string
│   ├── twitch: string
│   └── youtube: string
├── team_history: JSONField (career history)
├── achievements: JSONField
├── preferred_agents: JSONField [string]
├── preferred_roles: JSONField [string]
└── looking_for_team: boolean
```

---

## Page Architectures

### 1. Create Team Page (`createteam.jsx`)

**Purpose**: Allow players to create and manage their competitive team

#### UI Components
- Team name input
- Team tag input (3-5 characters)
- Logo upload
- Roster management
  - Add players (by username/PUUID)
  - Assign roles (IGL, Entry, AWP, Lurk, Support, Substitute)
  - Set captain
  - Set active roster (5 starters)
  - Set substitute roster (up to 2 subs)
- Team settings
  - Region selection
  - Division preference
- Create/Save team button

#### Events & Data Flow

**1. Create Team**

**Frontend → Backend**
```javascript
Event: 'create_team'
Payload: {
  name: string,
  tag: string,
  logo: File | base64,
  region: string,
  owner_puuid: string,
  captain_puuid: string
}
```

**Backend Processing**
1. Validate team name and tag uniqueness
2. Validate logo size and format
3. Create Team entity
4. Set owner and captain
5. Save logo to media storage

**Backend → Frontend**
```javascript
Event: 'team_created'
Payload: {
  team: {
    id: UUID,
    name: string,
    tag: string,
    logo_url: string,
    owner: Player,
    captain: Player,
    region: string,
    created_at: timestamp
  }
}
```

**2. Add Team Member**

**Frontend → Backend**
```javascript
Event: 'add_team_member'
Payload: {
  team_id: UUID,
  player_identifier: string, // username or PUUID
  role: string
}
```

**Backend Processing**
1. Find player by username or PUUID
2. Check player not already on another team
3. Check roster size limits (max 7)
4. Create TeamMember entry
5. Send invitation to player

**Backend → Frontend (To Invited Player)**
```javascript
Event: 'team_invitation_received'
Payload: {
  invitation_id: UUID,
  team: {
    id: UUID,
    name: string,
    tag: string,
    logo_url: string
  },
  inviter: Player,
  role: string,
  expires_at: timestamp
}
```

**3. Accept/Decline Team Invitation**

**Frontend → Backend**
```javascript
Event: 'respond_to_team_invitation'
Payload: {
  invitation_id: UUID,
  response: 'accept' | 'decline'
}
```

**Backend → Frontend**
```javascript
Event: 'team_roster_updated'
Payload: {
  team_id: UUID,
  members: [TeamMember],
  message: string
}
```

**4. Update Active Roster**

**Frontend → Backend**
```javascript
Event: 'update_active_roster'
Payload: {
  team_id: UUID,
  active_puuids: [string], // exactly 5
  substitute_puuids: [string] // 0-2
}
```

**Backend Processing**
1. Validate exactly 5 starters
2. Validate max 2 substitutes
3. Update Team model
4. Broadcast to team members

#### Frontend State
```javascript
{
  teamForm: {
    name: string,
    tag: string,
    logo: File | null,
    logoPreview: string,
    region: string
  },
  roster: [
    {
      player: Player,
      role: string,
      is_active: boolean,
      is_substitute: boolean
    }
  ],
  captain_puuid: string,
  validation: {
    nameValid: boolean,
    tagValid: boolean,
    rosterValid: boolean,
    logoValid: boolean
  }
}
```

#### Component Hierarchy
```
LeagueCreateTeam.jsx
├── TeamInfoCard
│   ├── TeamNameInput
│   ├── TeamTagInput
│   ├── LogoUploadZone
│   └── RegionSelector
├── RosterCard
│   ├── RosterHeader
│   ├── PlayerSearchInput
│   ├── RosterList
│   │   └── RosterMemberRow
│   │       ├── PlayerInfo
│   │       ├── RoleSelector
│   │       ├── StarterToggle
│   │       └── RemoveButton
│   ├── CaptainSelector
│   └── RosterSummary (5 starters, 2 subs)
└── ActionButtons
    ├── SaveDraftButton
    └── CreateTeamButton
```

---

### 2. Register/Pay Page (`registerpay.jsx`)

**Purpose**: Register team for league and handle payment

#### UI Components
- League selector
- Team selector (user's teams)
- League details display
  - Entry fee
  - Season dates
  - Format
  - Prize pool
- Roster lock confirmation
- Payment method selection
- Terms and conditions checkbox
- Pay/Register button

#### Events & Data Flow

**1. Get Available Leagues**

**Frontend → Backend**
```javascript
Event: 'get_available_leagues'
Payload: {
  region: string,
  division: string | null
}
```

**Backend → Frontend**
```javascript
Event: 'available_leagues'
Payload: {
  leagues: [
    {
      id: UUID,
      name: string,
      division: string,
      season: string,
      entry_fee: decimal,
      registered_teams: int,
      max_teams: int,
      registration_closes: timestamp,
      status: string
    }
  ]
}
```

**2. Register Team for League**

**Frontend → Backend**
```javascript
Event: 'register_team_for_league'
Payload: {
  league_id: UUID,
  team_id: UUID,
  roster_snapshot: [
    {
      puuid: string,
      role: string,
      is_active: boolean
    }
  ],
  payment_method: string,
  agree_to_terms: boolean
}
```

**Backend Processing**
1. Validate league is open for registration
2. Validate team meets requirements
3. Lock roster snapshot
4. Create LeagueRegistration with status='pending'
5. Initiate payment processing
6. Send confirmation email

**Backend → Frontend**
```javascript
Event: 'registration_initiated'
Payload: {
  registration_id: UUID,
  status: 'pending',
  payment_url: string | null,
  message: string
}
```

**3. Payment Confirmation**

**Backend → Frontend** (via webhook/polling)
```javascript
Event: 'payment_confirmed'
Payload: {
  registration_id: UUID,
  payment_status: 'paid',
  payment_id: string,
  team_id: UUID,
  league_id: UUID,
  confirmed_at: timestamp
}
```

**4. Get Team Registrations**

**Frontend → Backend**
```javascript
Event: 'get_team_registrations'
Payload: {
  team_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'team_registrations'
Payload: {
  registrations: [
    {
      registration_id: UUID,
      league: League,
      status: string,
      payment_status: string,
      registered_at: timestamp
    }
  ]
}
```

#### Component Hierarchy
```
LeagueRegisterPay.jsx
├── LeagueSelector
│   └── LeagueCard
│       ├── LeagueInfo
│       ├── RegistrationStatus
│       └── SelectButton
├── TeamSelector
│   └── TeamCard
├── RegistrationSummary
│   ├── LeagueDetails
│   ├── TeamRosterLocked
│   │   └── LockedRosterList
│   ├── EntryFeeDisplay
│   └── SeasonSchedule
├── PaymentSection
│   ├── PaymentMethodSelector
│   ├── PriceBreakdown
│   └── TermsCheckbox
└── RegisterButton
```

---

### 3. Standings Page (`standings.jsx`)

**Purpose**: Display league standings and team statistics

#### UI Components
- League/division selector
- Season selector
- Standings table
  - Rank
  - Team name + logo
  - Wins/Losses/Ties
  - Map differential
  - Round differential
  - Points
  - Recent form (W/L streak)
- Team detail modal (on click)
- Playoff bracket (when applicable)

#### Events & Data Flow

**1. Get League Standings**

**Frontend → Backend**
```javascript
Event: 'get_league_standings'
Payload: {
  league_id: UUID,
  division: string | null
}
```

**Backend → Frontend**
```javascript
Event: 'league_standings'
Payload: {
  league: {
    id: UUID,
    name: string,
    division: string,
    season: string
  },
  standings: [
    {
      rank: int,
      team: {
        id: UUID,
        name: string,
        tag: string,
        logo_url: string
      },
      wins: int,
      losses: int,
      ties: int,
      maps_won: int,
      maps_lost: int,
      round_differential: int,
      points: int,
      streak: string,
      recent_matches: [
        {result: 'W'|'L'|'T', opponent: string}
      ]
    }
  ],
  last_updated: timestamp
}
```

**2. Get Team Details**

**Frontend → Backend**
```javascript
Event: 'get_team_league_details'
Payload: {
  team_id: UUID,
  league_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'team_league_details'
Payload: {
  team: Team,
  stats: {
    wins: int,
    losses: int,
    maps_won: int,
    maps_lost: int,
    average_rounds_per_map: float
  },
  recent_matches: [LeagueMatch],
  upcoming_matches: [LeagueMatch],
  roster: [TeamMember]
}
```

#### Real-time Updates

**Backend → Frontend** (during live matches)
```javascript
Event: 'standings_update'
Payload: {
  league_id: UUID,
  updated_standings: [Standing],
  affected_teams: [UUID]
}
```

#### Component Hierarchy
```
LeagueStandings.jsx
├── LeagueSelector
├── DivisionTabs
├── StandingsTable
│   ├── TableHeader
│   └── StandingRow
│       ├── RankBadge
│       ├── TeamInfo (name, logo)
│       ├── Record (W-L-T)
│       ├── MapDifferential
│       ├── RoundDifferential
│       ├── Points
│       └── StreakIndicator
├── TeamDetailModal
│   ├── TeamHeader
│   ├── StatsOverview
│   ├── RecentMatches
│   ├── UpcomingMatches
│   └── RosterList
└── PlayoffBracket (conditional)
```

---

### 4. Schedule Page (`schedule.jsx`)

**Purpose**: Display league match schedule

#### UI Components
- League selector
- Week selector
- Calendar/list view toggle
- Match cards
  - Team A vs Team B
  - Scheduled time
  - Match status
  - Score (if completed)
  - Watch VOD button (if available)
- Filter by team
- Filter by status (upcoming, live, completed)

#### Events & Data Flow

**1. Get League Schedule**

**Frontend → Backend**
```javascript
Event: 'get_league_schedule'
Payload: {
  league_id: UUID,
  week: int | null,
  team_id: UUID | null,
  status_filter: string | null
}
```

**Backend → Frontend**
```javascript
Event: 'league_schedule'
Payload: {
  league: League,
  current_week: int,
  total_weeks: int,
  matches: [
    {
      match_id: UUID,
      week: int,
      match_number: int,
      team_a: {
        id: UUID,
        name: string,
        tag: string,
        logo_url: string
      },
      team_b: {...},
      scheduled_time: timestamp,
      status: string,
      score: {
        team_a: int,
        team_b: int
      } | null,
      vod_url: string | null,
      can_reschedule: boolean
    }
  ]
}
```

**2. Request Match Reschedule**

**Frontend → Backend**
```javascript
Event: 'request_match_reschedule'
Payload: {
  match_id: UUID,
  requester_team_id: UUID,
  proposed_time: timestamp,
  reason: string
}
```

**Backend Processing**
1. Validate requester is team captain/owner
2. Check reschedule policy
3. Create reschedule request
4. Notify opponent team
5. Notify league admin

**Backend → Frontend (To Opponent)**
```javascript
Event: 'reschedule_request_received'
Payload: {
  request_id: UUID,
  match_id: UUID,
  from_team: Team,
  proposed_time: timestamp,
  reason: string,
  expires_at: timestamp
}
```

#### Real-time Updates

**Backend → Frontend** (when match starts)
```javascript
Event: 'match_started'
Payload: {
  match_id: UUID,
  league_id: UUID,
  status: 'live',
  stream_url: string | null
}
```

**Backend → Frontend** (when match completes)
```javascript
Event: 'match_completed'
Payload: {
  match_id: UUID,
  winner: Team,
  final_score: {
    team_a: int,
    team_b: int
  },
  maps_played: [...]
}
```

#### Component Hierarchy
```
LeagueSchedule.jsx
├── ScheduleControls
│   ├── LeagueSelector
│   ├── WeekSelector
│   ├── ViewToggle (Calendar/List)
│   └── FilterPanel
│       ├── TeamFilter
│       └── StatusFilter
├── ScheduleView
│   ├── CalendarView (conditional)
│   │   └── DayCell
│   │       └── MatchCard (compact)
│   └── ListView (conditional)
│       └── WeekSection
│           └── MatchCard
│               ├── MatchHeader (teams, time)
│               ├── MatchStatus
│               ├── MatchScore (if completed)
│               ├── LiveIndicator (if live)
│               └── MatchActions
│                   ├── WatchVODButton
│                   ├── RescheduleButton
│                   └── MatchDetailsButton
└── RescheduleModal
    ├── CurrentScheduleInfo
    ├── ProposedTimeSelector
    ├── ReasonInput
    └── SubmitButton
```

---

### 5. Rules Page (`rules.jsx`)

**Purpose**: Display league rules and regulations

#### UI Components
- League selector
- Rules sections
  - Eligibility requirements
  - Roster rules
  - Match rules
  - Format and scoring
  - Code of conduct
  - Penalties
  - Protest procedure
- FAQ accordion
- Contact support button

#### Events & Data Flow

**1. Get League Rules**

**Frontend → Backend**
```javascript
Event: 'get_league_rules'
Payload: {
  league_id: UUID
}
```

**Backend → Frontend**
```javascript
Event: 'league_rules'
Payload: {
  league: League,
  rules_content: string, // Markdown or HTML
  last_updated: timestamp,
  version: string
}
```

This page is mostly static content but may need versioning for rule updates.

#### Component Hierarchy
```
LeagueRules.jsx
├── LeagueSelector
├── RulesHeader
│   ├── LeagueName
│   ├── Version
│   └── LastUpdated
├── RulesNavigation (sidebar)
│   └── SectionLink
├── RulesContent
│   ├── EligibilitySection
│   ├── RosterRulesSection
│   ├── MatchRulesSection
│   ├── ScoringSection
│   ├── CodeOfConductSection
│   ├── PenaltiesSection
│   └── ProtestSection
└── SupportButton
```

---

## Backend Django Architecture

### New Django App: `league`

```
league/
├── __init__.py
├── models.py
├── manager.py
├── views.py
├── admin.py
├── urls.py
└── migrations/
```

#### Manager Methods

```python
# league/manager.py

class LeagueManager:
    # League operations
    async def get_available_leagues(self, region, division=None)
    async def get_league_details(self, league_id)
    async def get_league_rules(self, league_id)
    
    # Team operations
    async def create_team(self, team_data, owner_puuid)
    async def update_team(self, team_id, updates)
    async def get_team_details(self, team_id)
    async def delete_team(self, team_id)
    
    # Roster management
    async def add_team_member(self, team_id, player_puuid, role)
    async def remove_team_member(self, team_id, player_puuid)
    async def update_member_role(self, team_member_id, new_role)
    async def set_active_roster(self, team_id, active_puuids, sub_puuids)
    async def validate_roster(self, team_id)
    
    # Registration
    async def register_team(self, league_id, team_id, roster_snapshot)
    async def process_payment(self, registration_id, payment_method)
    async def confirm_registration(self, registration_id)
    async def get_team_registrations(self, team_id)
    
    # Standings
    async def get_league_standings(self, league_id, division=None)
    async def update_standings(self, league_id)
    async def get_team_league_stats(self, team_id, league_id)
    
    # Schedule
    async def get_league_schedule(self, league_id, week=None, team_id=None)
    async def create_match_schedule(self, league_id)
    async def request_reschedule(self, match_id, team_id, proposed_time)
    async def approve_reschedule(self, request_id)
    
    # Match recording
    async def record_league_match_result(self, match_id, winner_id, score)
    async def update_match_stats(self, match_id)
```

### Database Indexes

```python
# Important indexes for performance
class League(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['status', 'region']),
            models.Index(fields=['registration_closes']),
        ]

class LeagueStanding(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['league', 'rank']),
            models.Index(fields=['team', 'league']),
        ]
        
class LeagueMatch(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['league', 'week']),
            models.Index(fields=['scheduled_time', 'status']),
            models.Index(fields=['team_a', 'status']),
            models.Index(fields=['team_b', 'status']),
        ]
```

---

## Implementation Status

### ✅ FULLY IMPLEMENTED

**NONE** - No league-specific functionality has been implemented.

### ⚠️ PARTIALLY IMPLEMENTED

1. **Basic Team Model** (`server/scrimgg/models.py`)
   - ⚠️ Team model exists but is very basic:
     - ✅ Has: players (ManyToMany), active_roster, substitute_roster, wins, losses, division, team_history
     - ❌ Missing: name, tag, logo, owner, captain, region, verified, created_at
     - ❌ Missing: Detailed stats (total_rounds_won/lost, current_streak)
   - ⚠️ Team is a functional model but needs **major expansion** for league play

2. **Player Model** (`server/scrimgg/models.py`)
   - ✅ Player model is comprehensive with stats tracking
   - ⚠️ Lacks profile/bio fields needed for team profiles (social links, bio, country)

### ❌ NOT IMPLEMENTED

1. **League Django App**
   - ❌ No `league` Django app exists in `server/`
   - ❌ Need to create entire app structure

2. **League Models** (`server/league/models.py` - DOES NOT EXIST)
   - ❌ League model - Define leagues, seasons, divisions, registration periods
   - ❌ LeagueRegistration model - Team registration and payment tracking
   - ❌ LeagueMatch model - Scheduled matches with week/match_number
   - ❌ LeagueStanding model - Cached standings with win/loss records

3. **TeamMember Model**
   - ❌ No through model for team roster management
   - ❌ No role tracking (IGL, Entry, AWP, etc.)
   - ❌ No join/leave date tracking
   - ❌ No per-team stats tracking

4. **Profile Model**
   - ❌ No profile extension for Player
   - ❌ No bio, country, social links fields
   - ❌ No team history display

5. **League Manager** (`server/league/manager.py` - DOES NOT EXIST)
   - ❌ No league business logic:
     - create_league()
     - register_team()
     - validate_roster()
     - lock_roster()
     - generate_schedule()
     - record_match_result()
     - update_standings()

6. **Team Manager** (`server/league/team_manager.py` - DOES NOT EXIST)
   - ❌ No team management logic:
     - create_team()
     - invite_player()
     - accept_invite()
     - remove_player()
     - transfer_ownership()
     - assign_captain()
     - validate_roster_size()

7. **Standings Calculator** (`server/league/standings.py` - DOES NOT EXIST)
   - ❌ No standings calculation
   - ❌ No tiebreaker logic
   - ❌ No head-to-head record tracking

8. **Match Scheduler** (`server/league/scheduler.py` - DOES NOT EXIST)
   - ❌ No automatic schedule generation
   - ❌ No conflict detection
   - ❌ No reschedule handling

9. **League WebSocket Handlers** (`server/realtime/handlers/league_handler.py` - DOES NOT EXIST)
   - ❌ No league event handlers:
     - register_team
     - submit_match_result
     - challenge_result
     - reschedule_match

10. **Frontend Integration**
    - ❌ No league pages integrated with backend
    - ❌ No team creation UI
    - ❌ No league browser
    - ❌ No standings display
    - ❌ No match scheduling UI

---

## Implementation Priority

### 🔥 HIGH PRIORITY (Foundation)
1. **Create League Django App** - Set up app structure in `server/league/`
2. **Create All League Models** - League, LeagueRegistration, LeagueMatch, LeagueStanding, TeamMember
3. **Expand Team Model** - Add name, tag, logo, owner, captain, region, verified fields
4. **Create Profile Model** - Player bio, social links, country for team profiles
5. **Implement TeamManager** - Basic team creation, roster management, invites
6. **Implement LeagueManager** - League creation, team registration, roster validation

### 🔶 MEDIUM PRIORITY (Core Features)
7. **Build Registration System** - Payment integration, roster locking, waitlist
8. **Implement Match Scheduler** - Generate round-robin/swiss schedules
9. **Create Standings Calculator** - Real-time standings with tiebreakers
10. **Add League Handlers** - WebSocket events for league operations
11. **Build Frontend League Browser** - Display leagues, divisions, registration status
12. **Build Team Creation UI** - Logo upload, roster management, invite system

### 🔷 LOW PRIORITY (Enhanced Features)
13. **Team Profile Pages** - Display team stats, history, achievements
14. **League Stats & Analytics** - Team performance metrics, MVP tracking
15. **Match Rescheduling** - Captain-initiated reschedule requests
16. **Playoff Bracket System** - Bracket generation and management
17. **VOD Integration** - Link matches to Twitch/YouTube VODs
18. **Team Verification System** - Verify pro/semi-pro teams
19. **Free Agency System** - Player LFT (Looking For Team) board

---

## Summary

**Overall Status**: ~5% Complete

The league system is **almost entirely unimplemented**. Only a very basic Team model exists, but it lacks most fields needed for league play (owner, captain, logo, verified status, etc.). There is no dedicated `league` Django app, no league models, no managers, no handlers, and no frontend integration.

**What Exists**:
- Basic Team model skeleton (players, roster, wins/losses)
- Player model with stats (can be extended for profiles)

**What's Missing (Everything)**:
- Entire League Django app
- All league-related models (League, LeagueRegistration, LeagueMatch, LeagueStanding, TeamMember)
- Profile model for player bios
- Team expansion (owner, captain, logo, verified)
- All business logic (LeagueManager, TeamManager, StandingsCalculator, Scheduler)
- All WebSocket handlers for league events
- All frontend pages (browser, team creation, standings, schedule)

**Dependencies**:
- Requires Team model expansion first
- Requires Profile model creation
- Requires dedicated league Django app
- Should wait until PUG matchmaking is stable

**Estimated Development Time**: 8-12 weeks for full league system

**Recommendation**: League system is a **Phase 3+ feature**. It's a complex subsystem that requires:
1. Payment processing integration (for entry fees)
2. Scheduling algorithms (round-robin, Swiss, playoffs)
3. Team management infrastructure (invites, transfers, roster locks)
4. Standings calculation with tiebreakers
5. Match result validation and dispute resolution
6. VOD integration
7. Extensive frontend UI work

Should only be started after:
- ✅ PUG matchmaking is production-ready
- ✅ Match veto system is stable
- ✅ Team model expansion is complete
- ✅ Profile system is implemented

**Alternative Approach**: Start with a simplified "Season 0" league:
- Manual registration (no payment integration)
- Simple round-robin format
- Manual schedule generation
- Manual result reporting
- Basic standings display
This would allow testing league infrastructure before building full automation.
