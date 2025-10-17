"""
Match and MatchPlayer models for post-acceptance match flow.

These models track the state of a match after all players have accepted,
including veto phase, side selection, and custom game creation.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid


class Match(models.Model):
    """
    Represents a confirmed match that has been accepted by all players.
    Tracks the entire lifecycle from veto through completion.
    """
    
    # Match states
    STATE_CONFIRMED = 'CONFIRMED'       # All players accepted, ready for veto
    STATE_SERVER_VETO = 'SERVER_VETO'   # Server veto in progress
    STATE_VETO = 'VETO'                 # Map veto in progress
    STATE_SIDE_SELECTION = 'SIDE_SELECTION'  # Side selection in progress
    STATE_CREATING = 'CREATING'         # Custom game being created
    STATE_READY = 'READY'               # Waiting for all players to join
    STATE_IN_PROGRESS = 'IN_PROGRESS'   # Match started
    STATE_COMPLETED = 'COMPLETED'       # Match finished
    STATE_CANCELLED = 'CANCELLED'       # Match cancelled
    
    STATE_CHOICES = [
        (STATE_CONFIRMED, 'All players accepted'),
        (STATE_SERVER_VETO, 'Server veto in progress'),
        (STATE_VETO, 'Map veto in progress'),
        (STATE_SIDE_SELECTION, 'Side selection in progress'),
        (STATE_CREATING, 'Custom game being created'),
        (STATE_READY, 'Ready to start'),
        (STATE_IN_PROGRESS, 'Match started'),
        (STATE_COMPLETED, 'Match finished'),
        (STATE_CANCELLED, 'Match cancelled'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_CONFIRMED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Match identification
    match_confirmation_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Teams (stored as JSON for flexibility)
    team_a_lobbies = models.JSONField(help_text="List of lobby IDs in Team A")
    team_b_lobbies = models.JSONField(help_text="List of lobby IDs in Team B")
    team_a_players = models.JSONField(help_text="List of player data for Team A")
    team_b_players = models.JSONField(help_text="List of player data for Team B")
    
    # Captains
    team_a_captain_puuid = models.CharField(max_length=100)
    team_b_captain_puuid = models.CharField(max_length=100)
    
    # Server veto data
    server_pool = models.JSONField(default=list, help_text="Available servers for veto")
    vetoed_servers = models.JSONField(default=list, help_text="List of vetoed server names")
    server_veto_history = models.JSONField(default=list, help_text="History of server veto actions")
    final_server = models.CharField(max_length=20, null=True, blank=True)
    
    # Server veto turn tracking
    server_veto_turn = models.CharField(max_length=10, null=True, blank=True, help_text="'team_a' or 'team_b'")
    server_veto_deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    server_veto_started_at = models.DateTimeField(null=True, blank=True)
    
    # Map veto data
    map_pool = models.JSONField(help_text="Available maps for veto")
    vetoed_maps = models.JSONField(default=list, help_text="List of vetoed map names")
    veto_history = models.JSONField(default=list, help_text="History of veto actions")
    final_map = models.CharField(max_length=50, null=True, blank=True)
    
    # Veto turn tracking
    veto_turn = models.CharField(max_length=10, null=True, blank=True, help_text="'team_a' or 'team_b'")
    veto_deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    veto_started_at = models.DateTimeField(null=True, blank=True)
    
    # Side selection
    selected_side = models.CharField(max_length=10, null=True, blank=True, help_text="'attack' or 'defense'")
    side_selector = models.CharField(max_length=10, null=True, blank=True, help_text="Which team selects side")
    side_selection_deadline = models.DateTimeField(null=True, blank=True)
    
    # Server/game details
    server_region = models.CharField(max_length=20)
    constructor_puuid = models.CharField(max_length=100, null=True, blank=True)
    pregame_id = models.CharField(max_length=100, null=True, blank=True, help_text="Valorant pregame ID")
    coregame_id = models.CharField(max_length=100, null=True, blank=True, help_text="Valorant coregame ID")
    
    # Match scores
    team_a_score = models.IntegerField(default=0)
    team_b_score = models.IntegerField(default=0)
    current_round = models.IntegerField(default=0)
    
    # Timestamps
    game_started_at = models.DateTimeField(null=True, blank=True)
    game_ended_at = models.DateTimeField(null=True, blank=True)
    
    # Match quality metrics (from matchmaker)
    match_quality = models.FloatField(default=0.0)
    team_a_avg_mmr = models.FloatField(default=0.0)
    team_b_avg_mmr = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'matchmaking_match'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state', 'created_at']),
            models.Index(fields=['veto_deadline']),
            models.Index(fields=['pregame_id']),
        ]
    
    def __str__(self):
        return f"Match {self.id} - {self.state}"
    
    def get_all_player_puuids(self):
        """Get list of all player PUUIDs in this match."""
        puuids = []
        for player in self.team_a_players:
            puuids.append(player['puuid'])
        for player in self.team_b_players:
            puuids.append(player['puuid'])
        return puuids
    
    def get_player_team(self, puuid):
        """Determine which team a player is on."""
        for player in self.team_a_players:
            if player['puuid'] == puuid:
                return 'team_a'
        for player in self.team_b_players:
            if player['puuid'] == puuid:
                return 'team_b'
        return None
    
    def is_captain(self, puuid):
        """Check if a player is a team captain."""
        return puuid in [self.team_a_captain_puuid, self.team_b_captain_puuid]
    
    def get_remaining_maps(self):
        """Get maps that haven't been vetoed yet."""
        return [m for m in self.map_pool if m not in self.vetoed_maps]
    
    def is_veto_expired(self):
        """Check if current veto deadline has passed."""
        if not self.veto_deadline:
            return False
        return timezone.now() > self.veto_deadline


class MatchPlayer(models.Model):
    """
    Tracks individual player state within a match.
    Used for connection tracking, readiness, and performance monitoring.
    """
    
    # Relationships
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='players')
    player_puuid = models.CharField(max_length=100, db_index=True)
    
    # Player info (cached for performance)
    player_alias = models.CharField(max_length=100)
    player_elo = models.IntegerField()
    player_mmr = models.FloatField()
    
    # Team assignment
    team = models.CharField(max_length=10, help_text="'team_a' or 'team_b'")
    is_captain = models.BooleanField(default=False)
    
    # Connection tracking
    is_ready = models.BooleanField(default=False, help_text="Player ready for match")
    joined_pregame = models.BooleanField(default=False, help_text="Player joined custom game")
    joined_at = models.DateTimeField(null=True, blank=True)
    
    # Join retry tracking
    join_attempts = models.IntegerField(default=0)
    last_join_attempt = models.DateTimeField(null=True, blank=True)
    
    # Activity tracking
    last_seen = models.DateTimeField(auto_now=True)
    connection_issues = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'matchmaking_match_player'
        unique_together = [['match', 'player_puuid']]
        indexes = [
            models.Index(fields=['match', 'joined_pregame']),
            models.Index(fields=['player_puuid', 'match']),
        ]
    
    def __str__(self):
        return f"{self.player_alias} in Match {self.match_id}"
    
    def increment_join_attempts(self):
        """Increment join attempt counter."""
        self.join_attempts += 1
        self.last_join_attempt = timezone.now()
        self.save(update_fields=['join_attempts', 'last_join_attempt'])
    
    def mark_joined(self):
        """Mark player as successfully joined pregame."""
        self.joined_pregame = True
        self.joined_at = timezone.now()
        self.save(update_fields=['joined_pregame', 'joined_at'])


class VetoAction(models.Model):
    """
    Records each veto action for audit trail and display.
    """
    
    ACTION_BAN = 'BAN'
    ACTION_PICK = 'PICK'
    ACTION_TIMEOUT = 'TIMEOUT'
    ACTION_SERVER_VETO = 'SERVER_VETO'
    
    ACTION_CHOICES = [
        (ACTION_BAN, 'Map banned'),
        (ACTION_PICK, 'Map picked'),
        (ACTION_TIMEOUT, 'Timeout auto-action'),
        (ACTION_SERVER_VETO, 'Server vetoed'),
    ]
    
    # Relationships
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='veto_actions')
    
    # Action details
    action_type = models.CharField(max_length=15, choices=ACTION_CHOICES)
    map_name = models.CharField(max_length=50)
    team = models.CharField(max_length=10, help_text="'team_a' or 'team_b'")
    player_puuid = models.CharField(max_length=100, null=True, blank=True)
    
    # Sequence
    sequence_number = models.IntegerField(help_text="Order in veto sequence")
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    was_timeout = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'matchmaking_veto_action'
        ordering = ['match', 'sequence_number']
        indexes = [
            models.Index(fields=['match', 'sequence_number']),
        ]
    
    def __str__(self):
        return f"{self.team} {self.action_type} {self.map_name}"

