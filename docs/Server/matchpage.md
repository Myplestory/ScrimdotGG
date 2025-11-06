# Match Page (Server)

Comprehensive server documentation for Match Page: models, functions, WebSocket payloads, and tasks.

## Models

### Match
```python
class Match(models.Model):
    """
    Extended match model for post-acceptance flow.
    """
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
    team_a_lobbies = models.JSONField()
    team_b_lobbies = models.JSONField()
    team_a_captain = models.ForeignKey(Player, related_name='matches_as_captain_a')
    team_b_captain = models.ForeignKey(Player, related_name='matches_as_captain_b')
    
    # Veto
    map_pool = models.JSONField()
    vetoed_maps = models.JSONField(default=list)
    final_map = models.CharField(max_length=50, null=True, blank=True)
    veto_turn = models.CharField(max_length=10)
    veto_deadline = models.DateTimeField(null=True)
    
    # Side selection
    selected_side = models.CharField(max_length=10, null=True)
    side_selector = models.CharField(max_length=10, null=True)
    
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

### MatchPlayer
```python
class MatchPlayer(models.Model):
    """Track individual player state within match."""
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

## Server Functions

### select_constructor(match: Match) -> Player
```python
def select_constructor(match: Match) -> Player:
    """Select which player will create the custom game."""
    constructor = match.team_a_captain
    if not is_player_online(constructor.puuid):
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

### initiate_custom_game_creation(match: Match)
```python
def initiate_custom_game_creation(match: Match):
    """Server sends event to constructor client to create custom game."""
    send_to_player(match.constructor.puuid, {
        'type': 'create_custom_game',
        'match_id': str(match.id),
        'map': match.final_map,
        'server': match.server_region,
        'starting_side': match.selected_side,
        'is_constructor': True
    })
    # Send waiting event to others
    for player in get_match_players(match):
        if player.puuid != match.constructor.puuid:
            send_to_player(player.puuid, {
                'type': 'waiting_for_game_creation',
                'match_id': str(match.id),
                'constructor': match.constructor.alias
            })
```

### handle_custom_game_created(data: dict)
```python
async def handle_custom_game_created(data: dict):
    match_id = data['match_id']
    pregame_id = data['pregame_id']
    match = Match.objects.get(id=match_id)
    match.pregame_id = pregame_id
    match.state = 'READY'
    match.save()
    # Broadcast join info
    for player in get_match_players(match):
        team = get_player_team(match, player.puuid)
        send_to_player(player.puuid, {
            'type': 'join_custom_game',
            'match_id': str(match.id),
            'pregame_id': pregame_id,
            'team': team
        })
```

## WebSocket Events (Server → Client)

- match_confirmed, veto_started, map_vetoed, veto_complete, side_selection_started, side_selected, create_custom_game, custom_game_created, join_custom_game, player_joined_pregame, match_starting, match_score_update, match_completed.

Payload shapes are referenced in Architecture; see Client docs for handler expectations.

## Tasks

- Celery: `check_veto_timeouts` enforces veto deadlines and auto-veto on timeout.
