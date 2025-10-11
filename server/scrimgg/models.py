from django.db import models
from django.db.models import JSONField
import uuid

class Player(models.Model):
    username = models.CharField(max_length=100)
    alias = models.CharField(max_length=100)
    puuid = models.CharField(max_length=100)
    region = models.CharField(max_length=5)
    elo = models.IntegerField(default=6493)
    karma = models.IntegerField(default=50)
    rank = models.CharField(max_length=1,default='S')
    team = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='avatars/', default='avatars/default/default_avatar.svg')
    friends = models.ManyToManyField('self', symmetrical=True, blank=True, related_name='friend_set')
    incoming_friend_requests = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='incoming_requests')
    outgoing_friend_requests = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='outgoing_requests')
    # Bans
    active_ban = models.BooleanField(default=False)
    finish_ban = models.DateTimeField(auto_now_add=True)
    # History of matches
    pug_history = JSONField(default=dict)
    league_history = JSONField(default=dict)
    team_history = JSONField(default=dict)
    team_active = JSONField(default=dict)
    # Player stats (overall)
    frags = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    maxfrag = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    loss = models.IntegerField(default=0)
    adr = models.FloatField(default=0.0)
    highest_adr = models.FloatField(default=0.0)
    acs = models.FloatField(default=0.0)
    hs = models.FloatField(default=0.0)
    rws = models.FloatField(default=0.0)
    highest_rws = models.FloatField(default=0.0)
    # Player stats (pugs)
    pug_rws = models.FloatField(default=0.0)
    pug_frags = models.IntegerField(default=0)
    pug_deaths = models.IntegerField(default=0)
    pug_adr = models.FloatField(default=0.0)
    # Player stats (league)
    league_adr = models.FloatField(default=0.0)
    league_rws = models.FloatField(default=0.0)
    league_frags = models.IntegerField(default=0)
    league_deaths = models.IntegerField(default=0)
    
class Lobby(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    players = models.ManyToManyField(Player, related_name='lobbies')
    lobby_leader = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, related_name='led_lobbies')
    
    # Lobby state
    is_active = models.BooleanField(default=True)
    in_queue = models.BooleanField(default=False)
    queue_type = models.CharField(max_length=20, default='pug')  # 'pug', 'scrim', 'custom'
    
    # Matchmaking preferences
    map_preferences = models.JSONField(default=list)  # List of preferred maps
    server_preferences = models.JSONField(default=list)  # List of preferred servers
    
    # Lobby stats for matchmaking
    average_elo = models.FloatField(default=0.0)
    elo_range = models.JSONField(default=dict)  # {'min': 1400, 'max': 1600}
    size = models.IntegerField(default=0)
    max_size = models.IntegerField(default=5)  # Maximum lobby size
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    queued_at = models.DateTimeField(null=True, blank=True)  # When lobby joined queue
    
    def __str__(self):
        return f"Lobby {self.id} - {self.size}/{self.max_size} players - Leader: {self.lobby_leader.alias if self.lobby_leader else 'None'}"

class Match(models.Model):
    # Legacy fields (keeping for backward compatibility)
    parties = models.JSONField(default=dict)
    banned_maps = models.JSONField(default=list)
    maps = models.JSONField(default=list)
    banned_servers = models.JSONField(default=list)
    servers = models.JSONField(default=list)
    match_info = models.JSONField(default=dict)
    
    # Match execution fields
    STATUS_CHOICES = [
        ('confirmed', 'All Players Accepted'),
        ('starting', 'Creating Custom Game'),
        ('in_progress', 'Match Live'),
        ('paused', 'Match Paused'),
        ('completed', 'Match Finished'),
        ('cancelled', 'Match Cancelled')
    ]
    status = models.CharField(max_length=20, default='confirmed', choices=STATUS_CHOICES)
    
    # Game server details
    constructor_puuid = models.CharField(max_length=100, null=True, blank=True)  # Party leader who creates custom game
    pregame_id = models.CharField(max_length=100, null=True, blank=True)  # Valorant pregame ID
    coregame_id = models.CharField(max_length=100, null=True, blank=True)  # Valorant in-game match ID
    game_server = models.CharField(max_length=100, null=True, blank=True)  # Server pod
    selected_map = models.CharField(max_length=50, null=True, blank=True)  # Final map after veto
    
    # Legacy naming (for backward compatibility)
    played_map = models.CharField(max_length=100, null=True, blank=True)
    played_server = models.CharField(max_length=100, null=True, blank=True)
    
    # Match timing
    start_time = models.DateTimeField(auto_now_add=True)
    confirmation_completed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    finish_time = models.DateTimeField(null=True, blank=True)  # Legacy
    
    # Live match data (cached for performance)
    current_round = models.IntegerField(default=0)
    team_a_score = models.IntegerField(default=0)
    team_b_score = models.IntegerField(default=0)
    team_a_data = models.JSONField(default=dict)  # Team A player data
    team_b_data = models.JSONField(default=dict)  # Team B player data
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Match {self.id} - {self.status} - {self.team_a_score}:{self.team_b_score}"


class MatchStatistics(models.Model):
    """
    Player statistics for a match - collected at round/match end.
    Optimized for performance with minimal writes during gameplay.
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='statistics')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.CharField(max_length=10)  # 'team_a' or 'team_b'
    
    # Core stats
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    
    # Advanced stats
    headshots = models.IntegerField(default=0)
    bodyshots = models.IntegerField(default=0)
    legshots = models.IntegerField(default=0)
    damage_dealt = models.IntegerField(default=0)
    damage_received = models.IntegerField(default=0)
    
    # Calculated metrics (updated post-match)
    adr = models.FloatField(default=0.0)  # Average Damage per Round
    rws = models.FloatField(default=0.0)  # Round Win Shares
    headshot_percentage = models.FloatField(default=0.0)
    kd_ratio = models.FloatField(default=0.0)
    
    # Round-specific data (JSON for performance)
    round_stats = models.JSONField(default=dict)  # Detailed per-round breakdown
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['match', 'player']
        indexes = [
            models.Index(fields=['match', 'team']),
        ]
    
    def __str__(self):
        return f"{self.player.alias} - {self.kills}/{self.deaths}/{self.assists} (Match {self.match.id})"


class MatchRejoinToken(models.Model):
    """
    Allow players to rejoin matches after disconnect.
    Tokens expire after 5 minutes for security.
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='rejoin_tokens')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['match', 'player']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['match', 'player']),
        ]
    
    def __str__(self):
        return f"Rejoin token for {self.player.alias} in match {self.match.id}"
    
class Team(models.Model):
    players = models.ManyToManyField(Player, related_name='teams')
    active_roster = models.ManyToManyField(Player, related_name='active_teams',blank=True)
    substitute_roster = models.ManyToManyField(Player, related_name='substitute_teams', blank=True)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    division = models.CharField(max_length=100)
    team_history = models.JSONField(default=dict)