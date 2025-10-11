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
    parties = models.JSONField(default=dict)
    pregame_id = models.CharField(max_length=100, null=True, blank=True)
    played_map = models.CharField(max_length=100,null=True, blank=True)
    banned_maps = models.JSONField(default=list)
    maps = models.JSONField(default=list)
    played_server = models.CharField(max_length=100, null=True, blank=True)
    banned_servers = models.JSONField(default=list)
    servers = models.JSONField(default=list)
    start_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(auto_now_add=True)
    match_info = models.JSONField(default=dict)
    
class Team(models.Model):
    players = models.ManyToManyField(Player, related_name='teams')
    active_roster = models.ManyToManyField(Player, related_name='active_teams',blank=True)
    substitute_roster = models.ManyToManyField(Player, related_name='substitute_teams', blank=True)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    division = models.CharField(max_length=100)
    team_history = models.JSONField(default=dict)