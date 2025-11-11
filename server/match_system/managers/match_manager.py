"""
Match Manager - Pregame veto and setup orchestration.

MOVED FROM: matchmaking/match_manager.py

Handles everything AFTER players accept a match, BEFORE game starts:
- Creating Match from confirmation
- Server veto orchestration + broadcasting
- Map veto orchestration + broadcasting  
- Side selection + broadcasting
- Custom game coordination

This is NOT a wrapper - this IS the business logic for match_system app.
"""

from typing import Dict, List, Optional, Tuple
import logging
from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer

# Import models from match_system (this app)
from core.websocket_utils import WebSocketBroadcaster
from match_system.models import Match, MatchPlayer, VetoAction
from match_system.phases import server_veto, map_veto, side_selection, snapshot as snapshot_builder

logger = logging.getLogger(__name__)


class MatchManager:
    """
    Manages match state transitions and veto logic.
    
    This is the PRIMARY implementation for pregame match management.
    """
    
    # ------------------------------------------------------------------
    # Internal helpers for unified match state snapshots
    # ------------------------------------------------------------------

    # Snapshot assembly is handled by match_system.phases.snapshot

    @staticmethod
    async def build_match_state(match: Match, last_event: Optional[str] = None, event_context: Optional[Dict] = None) -> Dict:
        return await snapshot_builder.build(match, last_event=last_event, event_context=event_context)

    @staticmethod
    def build_match_state_sync(match: Match, last_event: Optional[str] = None, event_context: Optional[Dict] = None) -> Dict:
        return snapshot_builder.build_sync(match, last_event=last_event, event_context=event_context)

    @staticmethod
    async def broadcast_match_state(
        match_id: str,
        match: Optional[Match] = None,
        *,
        last_event: Optional[str] = None,
        event_context: Optional[Dict] = None,
    ) -> None:
        if match is None:
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
        state = await MatchManager.build_match_state(match, last_event=last_event, event_context=event_context)
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"match_{match_id}",
            {
                'type': 'match_state_update',
                'payload': state,
            }
        )

    @staticmethod
    def broadcast_match_state_sync(
        match_id: str,
        match: Optional[Match] = None,
        *,
        last_event: Optional[str] = None,
        event_context: Optional[Dict] = None,
    ) -> None:
        instance = match or Match.objects.get(id=match_id)
        state = MatchManager.build_match_state_sync(instance, last_event=last_event, event_context=event_context)
        WebSocketBroadcaster.broadcast_to_match(
            str(instance.id),
            'match_state_update',
            {
                'payload': state,
            }
        )
    
    # ============================================================================
    # MATCH CREATION (Transition from matchmaking)
    # ============================================================================
    
    @staticmethod
    async def create_match_from_confirmation(match_confirmation_id: str) -> Optional[Match]:
        """
        Create a Match instance after all players have accepted.
        
        This transitions from the MatchConfirmation system to the Match system.
        
        Args:
            match_confirmation_id: ID of the confirmed match
            
        Returns:
            Match instance or None if creation failed
        """
        try:
            # Import from matchmaking ONLY to get confirmation data
            from matchmaking.match_confirmation import MatchConfirmationManager
            
            # Get match confirmation data
            confirmation_data = await MatchConfirmationManager.get_match_data(match_confirmation_id)
            
            if not confirmation_data:
                logger.error(f"No confirmation data found for {match_confirmation_id}")
                return None
            
            # The confirmation_data IS the match data (it contains all the match information)
            match_data = confirmation_data
            match_lobbies = match_data.get('match_lobbies', [])
            
            # Get team assignments
            team_a_lobbies, team_b_lobbies = MatchManager._extract_team_lobbies(match_data)
            team_a_players, team_b_players = MatchManager._extract_team_players(match_data)
            
            # Get captains from matchmaker data (if available) or determine by highest MMR
            if 'team_a' in match_data and 'team_b' in match_data:
                team_a_captain = match_data['team_a'].get('captain', max(team_a_players, key=lambda p: p.get('mmr', 0)))
                team_b_captain = match_data['team_b'].get('captain', max(team_b_players, key=lambda p: p.get('mmr', 0)))
            else:
                # Fallback: determine captains (highest MMR player on each team)
                team_a_captain = max(team_a_players, key=lambda p: p.get('mmr', 0))
                team_b_captain = max(team_b_players, key=lambda p: p.get('mmr', 0))
            
            # Get map pool and server region
            map_pool = match_data.get('map_pool', [])
            server_pool = match_data.get('server_pool', [])
            server_region = server_pool[0] if server_pool else 'na'
            
            # Calculate team averages
            team_a_avg_mmr = sum(p.get('mmr', 0) for p in team_a_players) / len(team_a_players)
            team_b_avg_mmr = sum(p.get('mmr', 0) for p in team_b_players) / len(team_b_players)
            
            # Create Match instance (using sync_to_async for Celery compatibility)
            match = await sync_to_async(Match.objects.create, thread_sensitive=False)(
                match_confirmation_id=match_confirmation_id,
                state=Match.STATE_CONFIRMED,
                team_a_lobbies=team_a_lobbies,
                team_b_lobbies=team_b_lobbies,
                team_a_players=team_a_players,
                team_b_players=team_b_players,
                team_a_captain_puuid=team_a_captain['puuid'],
                team_b_captain_puuid=team_b_captain['puuid'],
                map_pool=map_pool,
                server_pool=server_pool,  # Store common servers from matchmaking
                server_region=server_region,
                match_quality=match_data.get('match_quality', 0.0),
                team_a_avg_mmr=team_a_avg_mmr,
                team_b_avg_mmr=team_b_avg_mmr,
            )
            
            # Create MatchPlayer entries for tracking
            await MatchManager._create_match_players(match, team_a_players, team_b_players)
            
            logger.info(f"Created match {match.id} from confirmation {match_confirmation_id}")
            
            return match
            
        except Exception as e:
            logger.error(f"Error creating match from confirmation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def _extract_team_lobbies(match_data: Dict) -> Tuple[List[str], List[str]]:
        """Extract lobby IDs for each team."""
        # Handle team_a/team_b format from matchmaker
        if 'team_a' in match_data and 'team_b' in match_data:
            # Extract lobby IDs from match_lobbies based on team assignments
            match_lobbies = match_data.get('match_lobbies', [])
            team_a_lobbies = []
            team_b_lobbies = []
            
            # Get team A and B player PUUIDs
            team_a_puuids = {p['puuid'] for p in match_data['team_a']['players']}
            team_b_puuids = {p['puuid'] for p in match_data['team_b']['players']}
            
            # Assign lobbies to teams based on which players are in them
            for lobby in match_lobbies:
                lobby_player_puuids = {p['puuid'] for p in lobby.get('players', [])}
                
                # Check if lobby players overlap more with team A or team B
                team_a_overlap = len(lobby_player_puuids.intersection(team_a_puuids))
                team_b_overlap = len(lobby_player_puuids.intersection(team_b_puuids))
                
                if team_a_overlap > team_b_overlap:
                    team_a_lobbies.append(lobby['id'])
                elif team_b_overlap > team_a_overlap:
                    team_b_lobbies.append(lobby['id'])
                else:
                    # Equal overlap - assign to team A by default
                    team_a_lobbies.append(lobby['id'])
            
            return team_a_lobbies, team_b_lobbies
        
        # Handle legacy lobby1/lobby2 format
        lobby1 = match_data.get('lobby1', {})
        lobby2 = match_data.get('lobby2', {})
        
        team_a_lobbies = [lobby1.get('id')] if lobby1.get('id') else []
        team_b_lobbies = [lobby2.get('id')] if lobby2.get('id') else []
        
        # Handle multiple lobbies per team (if any)
        lobbies = match_data.get('lobbies', [])
        if len(lobbies) > 2:
            # For now, assume first half go to team A, second half to team B
            mid = len(lobbies) // 2
            team_a_lobbies = lobbies[:mid]
            team_b_lobbies = lobbies[mid:]
        
        return team_a_lobbies, team_b_lobbies
    
    @staticmethod
    def _extract_team_players(match_data: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Extract player data for each team."""
        # Handle team_a/team_b format from matchmaker
        if 'team_a' in match_data and 'team_b' in match_data:
            team_a_players = match_data['team_a']['players']
            team_b_players = match_data['team_b']['players']
            return team_a_players, team_b_players
        
        # Handle legacy lobby1/lobby2 format
        lobby1 = match_data.get('lobby1', {})
        lobby2 = match_data.get('lobby2', {})
        
        team_a_players = lobby1.get('players', [])
        team_b_players = lobby2.get('players', [])
        
        return team_a_players, team_b_players
    
    @staticmethod
    async def _create_match_players(match: Match, team_a_players: List[Dict], team_b_players: List[Dict]):
        """Create MatchPlayer entries for all players."""
        match_players = []
        
        for player in team_a_players:
            match_players.append(MatchPlayer(
                match=match,
                player_puuid=player['puuid'],
                player_alias=player['alias'],
                player_elo=player.get('elo', 0),
                player_mmr=player.get('mmr', 0),
                team='team_a',
                is_captain=(player['puuid'] == match.team_a_captain_puuid)
            ))
        
        for player in team_b_players:
            match_players.append(MatchPlayer(
                match=match,
                player_puuid=player['puuid'],
                player_alias=player['alias'],
                player_elo=player.get('elo', 0),
                player_mmr=player.get('mmr', 0),
                team='team_b',
                is_captain=(player['puuid'] == match.team_b_captain_puuid)
            ))
        
        await sync_to_async(MatchPlayer.objects.bulk_create, thread_sensitive=False)(match_players)
        logger.info(f"Created {len(match_players)} MatchPlayer entries for match {match.id}")
    
    # ============================================================================
    # SERVER VETO
    # ============================================================================
    
    @staticmethod
    async def start_server_veto(match: Match) -> Dict:
        try:
            return await server_veto.start_phase(match)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f"Error starting server veto for match {match.id}: {exc}")
            return {'status': 'error', 'message': str(exc)}
    
    @staticmethod
    async def veto_server(match_id: str, player_puuid: str, server_name: str) -> Dict:
        """
        Veto a server with orchestration (business logic + broadcasting).
        
        HIGH-LEVEL method called by handlers.
        
        Args:
            match_id: Match UUID
            player_puuid: Player's PUUID
            server_name: Server being vetoed
            
        Returns:
            Dict with veto result
        """
        try:
            # Get match
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            
            # Determine team
            team = match.get_player_team(player_puuid)
            if not team:
                return {
                    'status': 'error',
                    'message': 'Player not found in match'
                }
            
            # Process veto (business logic)
            result = await server_veto.process_veto(match, server_name, team, player_puuid)
            
            if result['status'] != 'success':
                return result
            
            await MatchManager.broadcast_match_state(
                match_id,
                last_event='server_veto_complete' if result.get('server_veto_complete') else 'server_veto',
                event_context={
                    'server_name': server_name,
                    'team': team,
                    'auto': False,
                    'server_veto_complete': result.get('server_veto_complete', False),
                    }
                )
            
            return result
            
        except Match.DoesNotExist:
            return {
                'status': 'error',
                'message': f'Match {match_id} not found'
            }
        except Exception as e:
            logger.error(f"Error in veto_server orchestration: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    async def process_server_veto(match: Match, server_name: str, vetoing_team: str, player_puuid: str) -> Dict:
        return await server_veto.process_veto(match, server_name, vetoing_team, player_puuid)
    
    # ============================================================================
    # MAP VETO
    # ============================================================================
    
    @staticmethod
    async def veto_map(match_id: str, player_puuid: str, map_name: str) -> Dict:
        """
        Veto a map with orchestration (business logic + broadcasting).
        
        HIGH-LEVEL method called by handlers.
        
        Args:
            match_id: Match UUID
            player_puuid: Player's PUUID
            map_name: Map being vetoed
            
        Returns:
            Dict with veto result
        """
        try:
            # Get match
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            
            # Determine team
            team = match.get_player_team(player_puuid)
            if not team:
                return {
                    'status': 'error',
                    'message': 'Player not found in match'
                }
            
            # Process veto (business logic)
            result = await map_veto.process_veto(match, map_name, team, player_puuid)
            
            if result['status'] != 'success':
                return result
            
            await MatchManager.broadcast_match_state(
                match_id,
                last_event='map_veto_complete' if result.get('veto_complete') else 'map_veto',
                event_context={
                        'map_name': map_name,
                    'team': team,
                    'auto': False,
                    'veto_complete': result.get('veto_complete', False),
                    }
                )
            
            return result
            
        except Match.DoesNotExist:
            return {
                'status': 'error',
                'message': f'Match {match_id} not found'
            }
        except Exception as e:
            logger.error(f"Error in veto_map orchestration: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': str(e)
            }

    @staticmethod
    async def process_map_veto(match: Match, map_name: str, vetoing_team: str, player_puuid: str) -> Dict:
        return await map_veto.process_veto(match, map_name, vetoing_team, player_puuid)
    
    # ============================================================================
    # SIDE SELECTION
    # ============================================================================
    
    @staticmethod
    async def select_side(match_id: str, player_puuid: str, side: str) -> Dict:
        """
        Select side with orchestration (business logic + broadcasting).
        
        HIGH-LEVEL method called by handlers.
        
        Args:
            match_id: Match UUID
            player_puuid: Player's PUUID
            side: 'attack' or 'defend'
            
        Returns:
            Dict with side selection result
        """
        try:
            # Get match
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            
            # Determine team
            team = match.get_player_team(player_puuid)
            if not team:
                return {
                    'status': 'error',
                    'message': 'Player not found in match'
                }
            
            # Process side selection (business logic)
            result = await side_selection.process_selection(match, side, team, player_puuid)
            
            if result['status'] != 'success':
                return result
            
            await MatchManager.broadcast_match_state(
                match_id,
                last_event='side_selection_complete' if result.get('side_complete') else 'side_selected',
                event_context={
                    'side': side,
                    'team': team,
                    'auto': result.get('auto_selected', False),
                    'match_ready': result.get('match_ready', False),
                }
            )
            
            return result
            
        except Match.DoesNotExist:
            return {
                'status': 'error',
                'message': f'Match {match_id} not found'
            }
        except Exception as e:
            logger.error(f"Error in select_side orchestration: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    async def process_side_selection(match: Match, side: str, team: str, player_puuid: str) -> Dict:
        return await side_selection.process_selection(match, side, team, player_puuid)
    
    # ============================================================================
    # MATCH DATA
    # ============================================================================
    
    @staticmethod
    async def get_match_data(match_id: str) -> Optional[Dict]:
        """
        Get complete match data for frontend.
        
        Args:
            match_id: Match UUID
            
        Returns:
            Dict with match data or None
        """
        try:
            match = await sync_to_async(lambda: Match.objects.get(id=match_id), thread_sensitive=False)()
            return await MatchManager.build_match_state(match)
            
        except Match.DoesNotExist:
            logger.error(f"Match {match_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting match data for {match_id}: {str(e)}")
            return None

    @staticmethod
    def get_match_data_sync(match_id: str) -> Optional[Dict]:
        """
        Synchronous helper to get match data. Used by Celery tasks.
        """
        try:
            match = Match.objects.get(id=match_id)
            return MatchManager.build_match_state_sync(match)
            
        except Match.DoesNotExist:
            logger.error(f"Match {match_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting match data for {match_id} (sync): {str(e)}")
            return None
    
    # ============================================================================
    # TIMEOUT HANDLERS - ASYNC (for consumers)
    # ============================================================================
    
    @staticmethod
    async def handle_map_veto_timeout(match_id) -> Dict:
        return await sync_to_async(MatchManager.handle_map_veto_timeout_sync, thread_sensitive=True)(match_id)
    
    # ============================================================================
    # TIMEOUT HANDLERS - SYNC (for Celery tasks)
    # ============================================================================
    
    @staticmethod
    def handle_server_veto_timeout_sync(match_id) -> Dict:
        return server_veto.handle_timeout(
            match_id,
            lambda mid, instance, last_event=None, event_context=None: MatchManager.broadcast_match_state_sync(
                mid,
                match=instance,
                last_event=last_event,
                event_context=event_context,
            ),
        )

    @staticmethod
    def handle_map_veto_timeout_sync(match_id) -> Dict:
        return map_veto.handle_timeout(
            match_id,
            lambda mid, instance, last_event=None, event_context=None: MatchManager.broadcast_match_state_sync(
                mid,
                match=instance,
                last_event=last_event,
                event_context=event_context,
            ),
        )

    @staticmethod
    def handle_side_selection_timeout_sync(match_id: str) -> Dict:
        return side_selection.handle_timeout(
            match_id,
            lambda mid, instance, last_event=None, event_context=None: MatchManager.broadcast_match_state_sync(
                mid,
                match=instance,
                last_event=last_event,
                event_context=event_context,
            ),
        )
