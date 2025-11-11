"""
Match State Validator for Scrim.GG matchmaking system.
Prevents players from queuing when they are already in active matches.
"""

import logging
from typing import Dict, List, Optional
from django.apps import apps
from django.db.models import Q
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class MatchStateValidator:
    """
    Service to validate if players can queue based on their current match state.
    Follows the async/sync pattern used throughout the matchmaking system.
    """
    
    # Match states that should block queuing
    ACTIVE_MATCH_STATES = [
        'CONFIRMED',           # All players accepted, ready for veto
        'SERVER_VETO',         # Server veto in progress
        'VETO',                # Map veto in progress
        'SIDE_SELECTION',      # Side selection in progress
        'CREATING',            # Custom game being created
        'READY',               # Waiting for all players to join
        'IN_PROGRESS'          # Match started
    ]
    
    # States that allow queuing
    INACTIVE_MATCH_STATES = [
        'COMPLETED',           # Match finished
        'CANCELLED'            # Match was cancelled
    ]
    
    @staticmethod
    async def can_player_queue(player_puuid: str) -> Dict:
        """
        Check if a player can queue based on their current match state - ASYNC version.
        
        Args:
            player_puuid: The player's PUUID
            
        Returns:
            {
                'can_queue': bool,
                'reason': str,  # If can_queue is False
                'match_id': str,  # Current active match if any
                'match_state': str  # Current match state
            }
        """
        try:
            active_match = await MatchStateValidator._get_player_active_match(player_puuid)
            
            if active_match:
                return {
                    'can_queue': False,
                    'reason': f'Player is in {active_match.state} match',
                    'match_id': str(active_match.id),
                    'match_state': active_match.state
                }
            
            return {
                'can_queue': True,
                'reason': None,
                'match_id': None,
                'match_state': None
            }
            
        except Exception as e:
            logger.error(f"Error checking player queue eligibility: {str(e)}")
            # Fail-open: allow queuing if we can't verify match status (better UX)
            return {
                'can_queue': True,
                'reason': None,
                'match_id': None,
                'match_state': None
            }
    
    @staticmethod
    def can_player_queue_sync(player_puuid: str) -> Dict:
        """
        Check if a player can queue based on their current match state - SYNC version.
        
        Args:
            player_puuid: The player's PUUID
            
        Returns:
            {
                'can_queue': bool,
                'reason': str,  # If can_queue is False
                'match_id': str,  # Current active match if any
                'match_state': str  # Current match state
            }
        """
        try:
            active_match = MatchStateValidator._get_player_active_match_sync(player_puuid)
            
            if active_match:
                return {
                    'can_queue': False,
                    'reason': f'Player is in {active_match.state} match',
                    'match_id': str(active_match.id),
                    'match_state': active_match.state
                }
            
            return {
                'can_queue': True,
                'reason': None,
                'match_id': None,
                'match_state': None
            }
            
        except Exception as e:
            logger.error(f"Error checking player queue eligibility: {str(e)}")
            # Fail-open: allow queuing if we can't verify match status (better UX)
            return {
                'can_queue': True,
                'reason': None,
                'match_id': None,
                'match_state': None
            }
    
    @staticmethod
    async def can_lobby_queue(lobby_id) -> Dict:
        """
        Check if all players in a lobby can queue - ASYNC version.
        
        Args:
            lobby_id: The lobby ID to check
            
        Returns:
            {
                'can_queue': bool,
                'blocked_players': List[str],  # PUUIDs of blocked players
                'reasons': Dict[str, str],     # Reasons per blocked player
                'active_matches': Dict[str, str]  # Player -> Match ID mapping
            }
        """
        try:
            Lobby = apps.get_model('scrimgg', 'Lobby')
            # Handle both UUID strings and integer IDs
            if isinstance(lobby_id, str):
                lobby = await sync_to_async(Lobby.objects.get)(id=lobby_id)
            else:
                lobby = await sync_to_async(Lobby.objects.get)(id=int(lobby_id))
            players = await sync_to_async(list)(lobby.players.all())
            
            blocked_players = []
            reasons = {}
            active_matches = {}
            
            for player in players:
                result = await MatchStateValidator.can_player_queue(player.puuid)
                if not result['can_queue']:
                    blocked_players.append(player.puuid)
                    reasons[player.puuid] = result['reason']
                    if result['match_id']:
                        active_matches[player.puuid] = result['match_id']
            
            return {
                'can_queue': len(blocked_players) == 0,
                'blocked_players': blocked_players,
                'reasons': reasons,
                'active_matches': active_matches
            }
            
        except Exception as e:
            logger.error(f"Error checking lobby queue eligibility: {str(e)}")
            return {
                'can_queue': False,
                'blocked_players': [],
                'reasons': {'error': 'Unable to verify lobby status'},
                'active_matches': {}
            }
    
    @staticmethod
    def can_lobby_queue_sync(lobby_id) -> Dict:
        """
        Check if all players in a lobby can queue - SYNC version.
        
        Args:
            lobby_id: The lobby ID to check
            
        Returns:
            {
                'can_queue': bool,
                'blocked_players': List[str],  # PUUIDs of blocked players
                'reasons': Dict[str, str],     # Reasons per blocked player
                'active_matches': Dict[str, str]  # Player -> Match ID mapping
            }
        """
        try:
            Lobby = apps.get_model('scrimgg', 'Lobby')
            # Handle both UUID strings and integer IDs
            if isinstance(lobby_id, str):
                lobby = Lobby.objects.get(id=lobby_id)
            else:
                lobby = Lobby.objects.get(id=int(lobby_id))
            players = list(lobby.players.all())
            
            blocked_players = []
            reasons = {}
            active_matches = {}
            
            for player in players:
                result = MatchStateValidator.can_player_queue_sync(player.puuid)
                if not result['can_queue']:
                    blocked_players.append(player.puuid)
                    reasons[player.puuid] = result['reason']
                    if result['match_id']:
                        active_matches[player.puuid] = result['match_id']
            
            return {
                'can_queue': len(blocked_players) == 0,
                'blocked_players': blocked_players,
                'reasons': reasons,
                'active_matches': active_matches
            }
            
        except Exception as e:
            logger.error(f"Error checking lobby queue eligibility: {str(e)}")
            return {
                'can_queue': False,
                'blocked_players': [],
                'reasons': {'error': 'Unable to verify lobby status'},
                'active_matches': {}
            }
    
    @staticmethod
    async def _get_player_active_match(player_puuid: str):
        """Get the active match for a player, if any - ASYNC version"""
        Match = apps.get_model('match_system', 'Match')
        
        def get_match():
            # Use the MatchPlayer relationship instead of JSON field queries
            MatchPlayer = apps.get_model('match_system', 'MatchPlayer')
            
            # Find matches where this player is a participant and match is in active state
            # Use Q objects to handle multiple state checks for better database compatibility
            from django.db.models import Q
            state_q = Q()
            for state in MatchStateValidator.ACTIVE_MATCH_STATES:
                state_q |= Q(match__state=state)
            
            active_match_player = MatchPlayer.objects.filter(
                player_puuid=player_puuid
            ).filter(state_q).select_related('match').first()
            
            return active_match_player.match if active_match_player else None
        
        return await sync_to_async(get_match, thread_sensitive=False)()
    
    @staticmethod
    def _get_player_active_match_sync(player_puuid: str):
        """Get the active match for a player, if any - SYNC version"""
        Match = apps.get_model('match_system', 'Match')
        
        # Use the MatchPlayer relationship instead of JSON field queries
        MatchPlayer = apps.get_model('match_system', 'MatchPlayer')
        
        # Find matches where this player is a participant and match is in active state
        # Use Q objects to handle multiple state checks for better database compatibility
        from django.db.models import Q
        state_q = Q()
        for state in MatchStateValidator.ACTIVE_MATCH_STATES:
            state_q |= Q(match__state=state)
        
        active_match_player = MatchPlayer.objects.filter(
            player_puuid=player_puuid
        ).filter(state_q).select_related('match').first()
        
        return active_match_player.match if active_match_player else None
    
    @staticmethod
    def get_active_match_states() -> List[str]:
        """Get list of match states that block queuing"""
        return MatchStateValidator.ACTIVE_MATCH_STATES.copy()
    
    @staticmethod
    def get_inactive_match_states() -> List[str]:
        """Get list of match states that allow queuing"""
        return MatchStateValidator.INACTIVE_MATCH_STATES.copy()
