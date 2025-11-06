# Entity Relationship Reference Guide

This document provides a quick reference for all entity relationships and associations in the Scrim.GG system.

---

## Entity Relationship Diagram (Text Format)

```
Player
├── Has Many: Lobbies (via ManyToMany)
├── Has Many: Teams (via TeamMember)
├── Has Many: Matches (via team_a_players/team_b_players JSON)
├── Has Many: Friends (via ManyToMany, symmetrical)
├── Has Many: ForumThreads (authored)
├── Has Many: ForumReplies (authored)
├── Has Many: SupportTickets (user)
├── Has One: Profile (OneToOne)
└── Has Many: Achievements

Lobby
├── Has Many: Players (ManyToMany)
├── Has One: Leader (ForeignKey → Player)
├── Has One: Team A Captain (ForeignKey → Player)
├── Has One: Team B Captain (ForeignKey → Player)
└── Has Many: ScrimInvites

Match
├── Has Many: Team A Players (JSON array)
├── Has Many: Team B Players (JSON array)
├── Has One: Team A Captain (referenced by PUUID)
├── Has One: Team B Captain (referenced by PUUID)
├── Has Many: VetoActions
├── Has Many: MatchStatistics
└── Has Many: RejoinTokens

Team
├── Has Many: Players (ManyToMany via TeamMember)
├── Has One: Owner (ForeignKey → Player)
├── Has One: Captain (ForeignKey → Player)
├── Has Many: Active Roster (ManyToMany → Player)
├── Has Many: Substitute Roster (ManyToMany → Player)
├── Has Many: LeagueRegistrations
├── Has Many: LeagueMatches
└── Has Many: TournamentRegistrations

League
├── Has Many: LeagueRegistrations
├── Has Many: LeagueMatches
└── Has Many: LeagueStandings

Tournament
├── Has Many: TournamentRegistrations
├── Has Many: TournamentBrackets
├── Has Many: TournamentMatches
└── Has Many: TournamentAnnouncements

ForumCategory
├── Has Many: ForumThreads
└── Has Count: PostCount

ForumThread
├── Has One: Author (ForeignKey → Player)
├── Has One: Category (ForeignKey → ForumCategory)
├── Has Many: ForumReplies
└── Has Many: ForumLikes

SupportTicket
├── Has One: User (ForeignKey → Player)
├── Has One: Assigned To (ForeignKey → Player, nullable)
├── Has Many: TicketMessages
└── Has One: TicketFeedback
```

---

## Core Entity Associations

### Player → Lobby
**Relationship**: ManyToMany
**Purpose**: Players can be in multiple lobbies (historical), but only one active lobby at a time
```python
# Get player's active lobby
lobby = Lobby.objects.filter(players=player, is_active=True).first()

# Get all players in lobby
players = lobby.players.all()
```

### Player → Team
**Relationship**: ManyToMany through TeamMember
**Purpose**: Players can be on multiple teams (current + historical)
```python
# Get player's active teams
teams = Team.objects.filter(
    teammember__player=player,
    teammember__status='active'
)

# Get team roster
members = TeamMember.objects.filter(team=team, status='active')
```

### Player → Match
**Relationship**: Embedded in JSON (team_a_players, team_b_players)
**Purpose**: Track which players participated in match
```python
# Check if player in match
player_in_match = any(
    p['puuid'] == player.puuid 
    for p in match.team_a_players + match.team_b_players
)

# Get player's team
player_team = 'team_a' if any(
    p['puuid'] == player.puuid for p in match.team_a_players
) else 'team_b'
```

### Lobby → Match
**Relationship**: Indirect via team_a_lobbies, team_b_lobbies JSON
**Purpose**: Track which lobbies formed the match teams
```python
# Lobbies that formed match
lobby_ids = match.team_a_lobbies + match.team_b_lobbies
lobbies = Lobby.objects.filter(id__in=lobby_ids)
```

### Match → MatchStatistics
**Relationship**: OneToMany (ForeignKey)
**Purpose**: Track individual player performance
```python
# Get all stats for match
stats = MatchStatistics.objects.filter(match=match)

# Get player's stats in match
player_stats = MatchStatistics.objects.get(match=match, player=player)
```

### Team → LeagueRegistration
**Relationship**: OneToMany (ForeignKey)
**Purpose**: Track team's league participations
```python
# Get team's active registrations
registrations = LeagueRegistration.objects.filter(
    team=team,
    status='confirmed'
)

# Get all teams in league
teams = LeagueRegistration.objects.filter(
    league=league,
    status='confirmed'
).select_related('team')
```

### League → LeagueMatch
**Relationship**: OneToMany (ForeignKey)
**Purpose**: Track matches within league season
```python
# Get league schedule
matches = LeagueMatch.objects.filter(
    league=league,
    week=current_week
).select_related('team_a', 'team_b')

# Get team's matches
team_matches = LeagueMatch.objects.filter(
    Q(team_a=team) | Q(team_b=team),
    league=league
)
```

### Tournament → TournamentMatch
**Relationship**: OneToMany through TournamentBracket
**Purpose**: Track bracket progression
```python
# Get tournament bracket
matches = TournamentMatch.objects.filter(
    tournament=tournament
).order_by('round_number', 'match_number')

# Get participant's next match
next_match = TournamentMatch.objects.filter(
    Q(participant_a=registration) | Q(participant_b=registration),
    status='pending'
).first()
```

---

## Event-to-Entity Mapping

### Lobby Events → Entities

| Event | Primary Entity | Related Entities |
|-------|---------------|------------------|
| `create_lobby` | Lobby | Player (leader) |
| `join_lobby` | Lobby | Player |
| `leave_lobby` | Lobby | Player |
| `update_lobby_preferences` | Lobby | - |
| `add_lobby_to_queue` | Lobby | Player (all members) |

### Match Events → Entities

| Event | Primary Entity | Related Entities |
|-------|---------------|------------------|
| `match_found` | Match | Lobby (multiple), Player (10) |
| `accept_match` | Match | Player |
| `veto_server` | Match | VetoAction, Player (captain) |
| `veto_map` | Match | VetoAction, Player (captain) |
| `select_side` | Match | Player (captain) |
| `match_started` | Match | Player (all) |
| `match_completed` | Match | MatchStatistics (10) |

### League Events → Entities

| Event | Primary Entity | Related Entities |
|-------|---------------|------------------|
| `create_team` | Team | Player (owner) |
| `add_team_member` | TeamMember | Team, Player |
| `register_team_for_league` | LeagueRegistration | League, Team |
| `update_standings` | LeagueStanding | League, Team |
| `schedule_match` | LeagueMatch | League, Team (2) |

### Tournament Events → Entities

| Event | Primary Entity | Related Entities |
|-------|---------------|------------------|
| `create_tournament` | Tournament | Player (organizer) |
| `register_for_tournament` | TournamentRegistration | Tournament, Team/Player |
| `tournament_check_in` | TournamentRegistration | - |
| `generate_bracket` | TournamentBracket | Tournament, TournamentMatch (many) |
| `record_match_result` | TournamentMatch | TournamentRegistration (2) |

---

## Database Queries by Use Case

### Use Case: Get Player's Current State

```python
# Get active lobby
active_lobby = await sync_to_async(
    Lobby.objects.filter(
        players__puuid=puuid,
        is_active=True
    ).select_related('lobby_leader').prefetch_related('players').first
)()

# Get active matches
active_matches = await sync_to_async(
    Match.objects.filter(
        Q(team_a_players__contains=[{'puuid': puuid}]) |
        Q(team_b_players__contains=[{'puuid': puuid}]),
        state__in=['CONFIRMED', 'IN_PROGRESS']
    ).all
)()

# Get active teams
active_teams = await sync_to_async(
    Team.objects.filter(
        teammember__player__puuid=puuid,
        teammember__status='active'
    ).all
)()
```

### Use Case: Get Match Full Data

```python
# Get match with all related data
match = await sync_to_async(
    Match.objects.select_related().get
)(id=match_id)

# Get statistics
stats = await sync_to_async(
    MatchStatistics.objects.filter(match=match)
    .select_related('player')
    .all
)()

# Get veto history
vetos = await sync_to_async(
    VetoAction.objects.filter(match=match)
    .order_by('timestamp')
    .all
)()
```

### Use Case: Get League Standings

```python
# Get standings
standings = await sync_to_async(
    LeagueStanding.objects.filter(league=league)
    .select_related('team')
    .order_by('rank')
    .all
)()

# Get team's upcoming matches
upcoming_matches = await sync_to_async(
    LeagueMatch.objects.filter(
        Q(team_a=team) | Q(team_b=team),
        league=league,
        status='scheduled',
        scheduled_time__gte=timezone.now()
    ).select_related('team_a', 'team_b')
    .order_by('scheduled_time')
    .all
)()
```

### Use Case: Get Tournament Bracket

```python
# Get tournament with bracket
tournament = await sync_to_async(
    Tournament.objects.select_related().get
)(id=tournament_id)

# Get all matches
matches = await sync_to_async(
    TournamentMatch.objects.filter(tournament=tournament)
    .select_related('participant_a', 'participant_b', 'winner')
    .order_by('round_number', 'match_number')
    .all
)()

# Get registrations
registrations = await sync_to_async(
    TournamentRegistration.objects.filter(
        tournament=tournament,
        status__in=['registered', 'checked_in']
    ).select_related('team', 'player')
    .all
)()
```

---

## Critical Indexes for Performance

### Player Table
```python
indexes = [
    models.Index(fields=['puuid']),  # Primary lookups
    models.Index(fields=['region']),  # Regional filtering
    models.Index(fields=['elo', 'mmr']),  # Matchmaking
]
```

### Lobby Table
```python
indexes = [
    models.Index(fields=['is_active', 'in_queue']),  # Status checks
    models.Index(fields=['queue_type', 'in_queue']),  # Queue filtering
]
```

### Match Table
```python
indexes = [
    models.Index(fields=['state', 'created_at']),  # State filtering
    models.Index(fields=['pregame_id']),  # Game tracking
    models.Index(fields=['veto_deadline']),  # Deadline checks
]
```

### LeagueMatch Table
```python
indexes = [
    models.Index(fields=['league', 'week']),  # Schedule queries
    models.Index(fields=['scheduled_time', 'status']),  # Upcoming matches
    models.Index(fields=['team_a', 'status']),  # Team schedule
    models.Index(fields=['team_b', 'status']),  # Team schedule
]
```

### TournamentMatch Table
```python
indexes = [
    models.Index(fields=['tournament', 'round_number']),  # Bracket queries
    models.Index(fields=['status']),  # Active match filtering
]
```

---

## Foreign Key Relationships Summary

### Player is referenced by:
- Lobby.players (M2M)
- Lobby.lobby_leader (FK)
- Team.owner (FK)
- Team.captain (FK)
- TeamMember.player (FK)
- MatchStatistics.player (FK)
- LeagueRegistration.team → Team → Players
- ForumThread.author (FK)
- ForumReply.author (FK)
- SupportTicket.user (FK)
- Profile.player (OneToOne)

### Lobby is referenced by:
- Match.team_a_lobbies (JSON)
- Match.team_b_lobbies (JSON)
- ScrimInvite.lobby (FK)

### Match is referenced by:
- MatchStatistics.match (FK)
- VetoAction.match (FK)
- MatchRejoinToken.match (FK)
- LeagueMatch.match_id (FK)
- TournamentMatch.match_id (FK)

### Team is referenced by:
- TeamMember.team (FK)
- LeagueRegistration.team (FK)
- LeagueMatch.team_a (FK)
- LeagueMatch.team_b (FK)
- LeagueStanding.team (FK)
- TournamentRegistration.team (FK)

### League is referenced by:
- LeagueRegistration.league (FK)
- LeagueMatch.league (FK)
- LeagueStanding.league (FK)

### Tournament is referenced by:
- TournamentRegistration.tournament (FK)
- TournamentBracket.tournament (FK)
- TournamentMatch.tournament (FK)
- TournamentAnnouncement.tournament (FK)

---

## Cascade Delete Behavior

### Critical: Prevent Data Loss
```python
# Players should NOT cascade delete
# Use SET_NULL or protect for most relationships
lobby_leader = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True)
```

### Safe Cascades
```python
# Match statistics should delete with match
match = models.ForeignKey(Match, on_delete=models.CASCADE)

# Forum replies should delete with thread
thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE)

# Ticket messages should delete with ticket
ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE)
```

---

## N+1 Query Prevention

### Always use select_related for ForeignKey
```python
# BAD: N+1 queries
lobbies = Lobby.objects.all()
for lobby in lobbies:
    print(lobby.lobby_leader.alias)  # Query per lobby!

# GOOD: Single query
lobbies = Lobby.objects.select_related('lobby_leader').all()
for lobby in lobbies:
    print(lobby.lobby_leader.alias)  # No extra queries
```

### Always use prefetch_related for ManyToMany
```python
# BAD: N+1 queries
teams = Team.objects.all()
for team in teams:
    for player in team.players.all():  # Query per team!
        print(player.alias)

# GOOD: Two queries total
teams = Team.objects.prefetch_related('players').all()
for team in teams:
    for player in team.players.all():  # No extra queries
        print(player.alias)
```

---

This reference guide should help you understand all entity relationships and write efficient queries for the Scrim.GG system.
