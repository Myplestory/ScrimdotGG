"""
Match Monitor
Low-overhead match monitoring system for live statistics.
Polls ValClient API at strategic intervals to minimize performance impact.
"""

import logging
from typing import Dict
from django.apps import apps
from django.utils import timezone
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class MatchMonitor:
    """
    Low-overhead match monitoring system.
    Receives updates from constructor client and broadcasts to spectators.
    """
    
    # Polling intervals (in seconds)
    POLL_INTERVAL_NORMAL = 30  # During regular play
    POLL_INTERVAL_ROUND_END = 5  # After detecting round end
    
    @staticmethod
    async def update_match_score(match_id: str, team_a_score: int, team_b_score: int, current_round: int) -> Dict:
        """
        Update match score (called from client polling ValClient API).
        Only broadcasts if score changed (delta update).
        
        Performance: O(1) - single update + conditional broadcast
        
        Args:
            match_id: UUID of the match
            team_a_score: Current Team A score
            team_b_score: Current Team B score
            current_round: Current round number
            
        Returns:
            Dict with status and whether score changed
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            def get_and_update_match():
                match = Match.objects.get(id=match_id)
                
                # Check if score actually changed
                score_changed = (
                    match.team_a_score != team_a_score or 
                    match.team_b_score != team_b_score or
                    match.current_round != current_round
                )
                
                if score_changed:
                    match.team_a_score = team_a_score
                    match.team_b_score = team_b_score
                    match.current_round = current_round
                    match.save()
                
                return match, score_changed
            
            match, changed = await sync_to_async(get_and_update_match)()
            
            # Only broadcast if something changed
            if changed:
                await MatchMonitor._broadcast_score_update(match)
                logger.info(f"Match {match_id} score update: {team_a_score}-{team_b_score} (Round {current_round})")
            
            return {'status': 'success', 'changed': changed}
            
        except Exception as e:
            logger.error(f"Error updating match score: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def _broadcast_score_update(match):
        """
        Broadcast score update to spectators and match room.
        Uses delta updates - only sends changed values.
        
        Performance: Single group_send to match channel
        
        Args:
            match: Match object
        """
        channel_layer = get_channel_layer()
        
        await channel_layer.group_send(
            f"match_{match.id}",
            {
                'type': 'match_score_update',
                'match_id': str(match.id),
                'team_a_score': match.team_a_score,
                'team_b_score': match.team_b_score,
                'current_round': match.current_round
            }
        )
    
    
    @staticmethod
    async def update_player_statistics(match_id: str, player_stats: Dict) -> Dict:
        """
        Update player statistics during match (called at round end).
        
        Performance: Batch update for all players
        
        Args:
            match_id: UUID of the match
            player_stats: Dict of player statistics {puuid: stats}
            
        Returns:
            Dict with status
        """
        try:
            MatchStatistics = apps.get_model('scrimgg', 'MatchStatistics')
            Match = apps.get_model('scrimgg', 'Match')
            Player = apps.get_model('scrimgg', 'Player')
            
            def update_stats():
                match = Match.objects.get(id=match_id)
                
                for puuid, stats in player_stats.items():
                    try:
                        player = Player.objects.get(puuid=puuid)
                        
                        # Get or create statistics record
                        match_stat, created = MatchStatistics.objects.get_or_create(
                            match=match,
                            player=player,
                            defaults={'team': stats.get('team', 'team_a')}
                        )
                        
                        # Update statistics
                        match_stat.kills = stats.get('kills', 0)
                        match_stat.deaths = stats.get('deaths', 0)
                        match_stat.assists = stats.get('assists', 0)
                        match_stat.headshots = stats.get('headshots', 0)
                        match_stat.bodyshots = stats.get('bodyshots', 0)
                        match_stat.legshots = stats.get('legshots', 0)
                        match_stat.damage_dealt = stats.get('damage_dealt', 0)
                        match_stat.damage_received = stats.get('damage_received', 0)
                        
                        # Calculate metrics
                        if match.current_round > 0:
                            match_stat.adr = match_stat.damage_dealt / match.current_round
                        
                        if match_stat.deaths > 0:
                            match_stat.kd_ratio = match_stat.kills / match_stat.deaths
                        else:
                            match_stat.kd_ratio = match_stat.kills
                        
                        total_shots = match_stat.headshots + match_stat.bodyshots + match_stat.legshots
                        if total_shots > 0:
                            match_stat.headshot_percentage = (match_stat.headshots / total_shots) * 100
                        
                        match_stat.save()
                        
                    except Player.DoesNotExist:
                        logger.warning(f"Player {puuid} not found for statistics update")
                        continue
            
            await sync_to_async(update_stats)()
            
            logger.info(f"Updated statistics for {len(player_stats)} players in match {match_id}")
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error updating player statistics: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def get_match_statistics(match_id: str) -> Dict:
        """
        Get current match statistics for spectators.
        
        Args:
            match_id: UUID of the match
            
        Returns:
            Dict with match and player statistics
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            MatchStatistics = apps.get_model('scrimgg', 'MatchStatistics')
            
            def get_stats():
                match = Match.objects.get(id=match_id)
                stats = MatchStatistics.objects.filter(match=match).select_related('player')
                
                # Organize by team
                team_a_stats = []
                team_b_stats = []
                
                for stat in stats:
                    stat_data = {
                        'puuid': stat.player.puuid,
                        'alias': stat.player.alias,
                        'kills': stat.kills,
                        'deaths': stat.deaths,
                        'assists': stat.assists,
                        'adr': round(stat.adr, 1),
                        'headshot_percentage': round(stat.headshot_percentage, 1),
                        'kd_ratio': round(stat.kd_ratio, 2)
                    }
                    
                    if stat.team == 'team_a':
                        team_a_stats.append(stat_data)
                    else:
                        team_b_stats.append(stat_data)
                
                return {
                    'match_id': str(match.id),
                    'status': match.status,
                    'team_a_score': match.team_a_score,
                    'team_b_score': match.team_b_score,
                    'current_round': match.current_round,
                    'map': match.selected_map,
                    'team_a_stats': team_a_stats,
                    'team_b_stats': team_b_stats
                }
            
            data = await sync_to_async(get_stats)()
            
            return {'status': 'success', 'data': data}
            
        except Exception as e:
            logger.error(f"Error getting match statistics: {str(e)}")
            return {'status': 'error', 'message': str(e)}

