from django.contrib import admin
from .models import Match, MatchPlayer, VetoAction


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'state', 'match_quality', 'created_at', 'final_map', 'final_server')
    list_filter = ('state', 'created_at', 'server_region')
    search_fields = ('id', 'match_confirmation_id', 'team_a_captain_puuid', 'team_b_captain_puuid')
    readonly_fields = ('id', 'created_at', 'updated_at', 'match_confirmation_id')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'state', 'match_confirmation_id', 'created_at', 'updated_at')
        }),
        ('Teams', {
            'fields': ('team_a_lobbies', 'team_b_lobbies', 'team_a_players', 'team_b_players',
                      'team_a_captain_puuid', 'team_b_captain_puuid')
        }),
        ('Server Veto', {
            'fields': ('server_pool', 'vetoed_servers', 'server_veto_history', 'final_server',
                      'server_veto_turn', 'server_veto_deadline', 'server_veto_started_at')
        }),
        ('Map Veto', {
            'fields': ('map_pool', 'vetoed_maps', 'veto_history', 'final_map',
                      'veto_turn', 'veto_deadline', 'veto_started_at')
        }),
        ('Side Selection', {
            'fields': ('selected_side', 'side_selector', 'side_selection_deadline')
        }),
        ('Game Details', {
            'fields': ('server_region', 'constructor_puuid', 'pregame_id', 'coregame_id')
        }),
        ('Match Stats', {
            'fields': ('team_a_score', 'team_b_score', 'current_round', 'match_quality',
                      'team_a_avg_mmr', 'team_b_avg_mmr', 'game_started_at', 'game_ended_at')
        }),
    )


@admin.register(MatchPlayer)
class MatchPlayerAdmin(admin.ModelAdmin):
    list_display = ('player_alias', 'match', 'team', 'is_captain', 'joined_pregame', 'join_attempts')
    list_filter = ('team', 'is_captain', 'joined_pregame', 'is_ready')
    search_fields = ('player_puuid', 'player_alias', 'match__id')
    readonly_fields = ('created_at', 'last_seen')


@admin.register(VetoAction)
class VetoActionAdmin(admin.ModelAdmin):
    list_display = ('match', 'sequence_number', 'action_type', 'map_name', 'team', 'was_timeout', 'created_at')
    list_filter = ('action_type', 'team', 'was_timeout')
    search_fields = ('match__id', 'map_name', 'player_puuid')
    readonly_fields = ('created_at',)
    ordering = ('match', 'sequence_number')

