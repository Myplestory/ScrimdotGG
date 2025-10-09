# ScrimGG/scrimgg/server/scrimgg/matchmaking/match_coordinator.py
# Coordinates the entire match lifecycle similar to FACEIT

from enum import Enum
from typing import List, Dict, Optional
from django.core.cache import cache
from django.apps import apps
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
import asyncio
import json
from datetime import datetime, timedelta


class MatchState(Enum):
    """All possible states for a match."""
    CREATED = "created"  # Match created by matchmaking
    VETO = "veto"  # Map/server veto in progress
    ACCEPTING = "accepting"  # Waiting for player acceptances
    READY = "ready"  # All accepted, creating custom game
    WAITING_JOIN = "waiting_join"  # Waiting for all players to join custom game
    LIVE = "live"  # Match is being played
    COMPLETED = "completed"  # Match finished successfully
    CANCELLED = "cancelled"  # Match cancelled (dodge, timeout, etc.)


class MatchCoordinator:
    """
    Coordinates the entire match flow from creation to completion.
    Handles timeouts, player verification, state transitions, etc.
    """
    
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.cache_key = f"match_coordinator:{match_id}"
        self.channel_layer = get_channel_layer()
    
    async def create_match(
        self,
        lobby_a_id: str,
        lobby_b_id: str,
        players_a: List[str],  # PUUIDs
        players_b: List[str],  # PUUIDs
        map_pool: List[str],
        server_pool: List[str],
    ) -> Dict:
        """
        Create a new match and initialize the match flow.
        
        Returns:
            Match state dictionary
        """
        Match = apps.get_model('scrimgg', 'Match')
        
        # Create Match model
        match = await sync_to_async(Match.objects.create)(
            parties={
                'team_a': players_a,
                'team_b': players_b,
            },
            maps=map_pool,
            servers=server_pool,
        )
        
        match_state = {
            'match_id': str(match.id),
            'state': MatchState.VETO.value,
            'lobby_a_id': lobby_a_id,
            'lobby_b_id': lobby_b_id,
            'players_a': players_a,
            'players_b': players_b,
            'all_players': players_a + players_b,
            'map_pool': map_pool,
            'server_pool': server_pool,
            'final_map': None,
            'final_server': None,
            'constructor_puuid': None,
            'pregame_id': None,
            'players_accepted': [],
            'players_joined': [],
            'players_ready': [],
            'created_at': datetime.now().isoformat(),
            'veto_started_at': datetime.now().isoformat(),
            'acceptance_deadline': None,
            'join_deadline': None,
            'match_started_at': None,
            'match_ended_at': None,
        }
        
        # Save state
        await self._save_state(match_state)
        
        # Broadcast match found to all players
        await self._broadcast_to_match('match_found', {
            'match_id': str(match.id),
            'players_a': players_a,
            'players_b': players_b,
            'state': MatchState.VETO.value,
        })
        
        # Start veto phase
        from .veto_system import VetoSystem
        veto = VetoSystem(str(match.id))
        veto.initialize_veto(
            team_a_lobbies=[lobby_a_id],
            team_b_lobbies=[lobby_b_id],
            available_maps=map_pool,
            available_servers=server_pool,
            veto_format="bo1"
        )
        
        # Set timeout for veto phase (5 minutes)
        asyncio.create_task(self._veto_timeout_handler(300))
        
        return match_state
    
    async def complete_veto(self, final_map: str, final_server: str):
        """
        Called when veto phase is complete.
        Transitions to acceptance phase.
        """
        state = await self._get_state()
        if not state:
            return
        
        state['final_map'] = final_map
        state['final_server'] = final_server
        state['state'] = MatchState.ACCEPTING.value
        state['acceptance_deadline'] = (datetime.now() + timedelta(seconds=30)).isoformat()
        
        await self._save_state(state)
        
        # Broadcast match acceptance required
        await self._broadcast_to_match('match_acceptance_required', {
            'match_id': self.match_id,
            'map': final_map,
            'server': final_server,
            'deadline': state['acceptance_deadline'],
            'timeout_seconds': 30,
        })
        
        # Start acceptance timeout
        asyncio.create_task(self._acceptance_timeout_handler(30))
    
    async def player_accept(self, puuid: str) -> bool:
        """
        Record a player's acceptance.
        
        Returns:
            True if all players have accepted, False otherwise
        """
        state = await self._get_state()
        if not state or state['state'] != MatchState.ACCEPTING.value:
            return False
        
        if puuid not in state['all_players']:
            return False
        
        if puuid not in state['players_accepted']:
            state['players_accepted'].append(puuid)
            await self._save_state(state)
        
        # Broadcast acceptance update
        await self._broadcast_to_match('player_accepted_match', {
            'puuid': puuid,
            'accepted_count': len(state['players_accepted']),
            'total_count': len(state['all_players']),
        })
        
        # Check if all accepted
        if len(state['players_accepted']) == len(state['all_players']):
            await self._all_players_accepted()
            return True
        
        return False
    
    async def player_decline(self, puuid: str):
        """
        A player declined the match. Cancel the match.
        """
        await self.cancel_match(f"Player {puuid} declined")
    
    async def _all_players_accepted(self):
        """
        All players have accepted. Assign constructor and proceed.
        """
        import random
        
        state = await self._get_state()
        if not state:
            return
        
        # Select a random player as constructor (or use ELO-based selection)
        constructor = random.choice(state['all_players'])
        state['constructor_puuid'] = constructor
        state['state'] = MatchState.READY.value
        
        await self._save_state(state)
        
        # Notify constructor to create custom game
        await self._broadcast_to_player(constructor, 'create_custom_game', {
            'match_id': self.match_id,
            'map': state['final_map'],
            'server': state['final_server'],
            'players': state['all_players'],
        })
        
        # Notify others to wait
        for puuid in state['all_players']:
            if puuid != constructor:
                await self._broadcast_to_player(puuid, 'match_starting', {
                    'match_id': self.match_id,
                    'constructor': constructor,
                    'status': 'Creating custom game...',
                })
    
    async def set_pregame_id(self, pregame_id: str):
        """
        Constructor has created the custom game.
        Broadcast pregame_id to all other players to join.
        """
        state = await self._get_state()
        if not state:
            return
        
        state['pregame_id'] = pregame_id
        state['state'] = MatchState.WAITING_JOIN.value
        state['join_deadline'] = (datetime.now() + timedelta(seconds=120)).isoformat()
        
        await self._save_state(state)
        
        # Update Match model
        Match = apps.get_model('scrimgg', 'Match')
        await sync_to_async(
            lambda: Match.objects.filter(id=self.match_id).update(pregame_id=pregame_id)
        )()
        
        # Broadcast to all non-constructor players
        for puuid in state['all_players']:
            if puuid != state['constructor_puuid']:
                await self._broadcast_to_player(puuid, 'join_custom_game', {
                    'match_id': self.match_id,
                    'pregame_id': pregame_id,
                })
        
        # Start join timeout (2 minutes)
        asyncio.create_task(self._join_timeout_handler(120))
    
    async def player_joined_game(self, puuid: str) -> bool:
        """
        Record that a player has joined the custom game.
        
        Returns:
            True if all players have joined
        """
        state = await self._get_state()
        if not state:
            return False
        
        if puuid not in state['players_joined']:
            state['players_joined'].append(puuid)
            await self._save_state(state)
        
        # Broadcast update
        await self._broadcast_to_match('player_joined_game', {
            'puuid': puuid,
            'joined_count': len(state['players_joined']),
            'total_count': len(state['all_players']),
        })
        
        # Check if all joined
        if len(state['players_joined']) == len(state['all_players']):
            await self._all_players_joined()
            return True
        
        return False
    
    async def _all_players_joined(self):
        """
        All players have joined the custom game.
        Signal constructor to start the match.
        """
        state = await self._get_state()
        if not state:
            return
        
        state['state'] = MatchState.LIVE.value
        state['match_started_at'] = datetime.now().isoformat()
        await self._save_state(state)
        
        # Tell constructor to start the game
        await self._broadcast_to_player(state['constructor_puuid'], 'start_custom_game', {
            'match_id': self.match_id,
        })
        
        # Notify all players match is live
        await self._broadcast_to_match('match_live', {
            'match_id': self.match_id,
            'started_at': state['match_started_at'],
        })
    
    async def match_ended(self, match_results: Dict):
        """
        Match has ended. Process results and update stats.
        """
        state = await self._get_state()
        if not state:
            return
        
        state['state'] = MatchState.COMPLETED.value
        state['match_ended_at'] = datetime.now().isoformat()
        await self._save_state(state)
        
        # Update Match model with results
        Match = apps.get_model('scrimgg', 'Match')
        await sync_to_async(
            lambda: Match.objects.filter(id=self.match_id).update(
                match_info=match_results,
                finish_time=datetime.now()
            )
        )()
        
        # Process player stats and ELO
        await self._process_match_results(match_results)
        
        # Broadcast match completion
        await self._broadcast_to_match('match_completed', {
            'match_id': self.match_id,
            'results': match_results,
        })
        
        # Clean up
        await self._cleanup()
    
    async def cancel_match(self, reason: str):
        """
        Cancel the match (dodge, timeout, error, etc.)
        """
        state = await self._get_state()
        if not state:
            return
        
        state['state'] = MatchState.CANCELLED.value
        state['cancellation_reason'] = reason
        await self._save_state(state)
        
        # Broadcast cancellation
        await self._broadcast_to_match('match_cancelled', {
            'match_id': self.match_id,
            'reason': reason,
        })
        
        # Apply penalties if appropriate
        await self._apply_dodge_penalties(state)
        
        # Clean up
        await self._cleanup()
    
    # ========== Timeout Handlers ==========
    
    async def _veto_timeout_handler(self, timeout_seconds: int):
        """Handle veto phase timeout."""
        await asyncio.sleep(timeout_seconds)
        
        state = await self._get_state()
        if not state or state['state'] != MatchState.VETO.value:
            return
        
        # Auto-complete veto
        from .veto_system import VetoSystem
        veto = VetoSystem(self.match_id)
        veto_state = veto.auto_complete_remaining_steps()
        
        if veto_state and veto_state['completed']:
            await self.complete_veto(
                veto_state['final_map'],
                veto_state['final_server']
            )
    
    async def _acceptance_timeout_handler(self, timeout_seconds: int):
        """Handle acceptance phase timeout."""
        await asyncio.sleep(timeout_seconds)
        
        state = await self._get_state()
        if not state or state['state'] != MatchState.ACCEPTING.value:
            return
        
        # Cancel match - not everyone accepted in time
        missing_players = set(state['all_players']) - set(state['players_accepted'])
        await self.cancel_match(f"Timeout - {len(missing_players)} players did not accept")
        
        # Penalize non-acceptors
        for puuid in missing_players:
            await self._apply_penalty(puuid, "dodge", 5)  # 5 minute cooldown
    
    async def _join_timeout_handler(self, timeout_seconds: int):
        """Handle join phase timeout."""
        await asyncio.sleep(timeout_seconds)
        
        state = await self._get_state()
        if not state or state['state'] != MatchState.WAITING_JOIN.value:
            return
        
        # Cancel match - not everyone joined
        missing_players = set(state['all_players']) - set(state['players_joined'])
        await self.cancel_match(f"Timeout - {len(missing_players)} players did not join")
        
        # Penalize no-shows
        for puuid in missing_players:
            await self._apply_penalty(puuid, "no_show", 15)  # 15 minute cooldown
    
    # ========== Utility Methods ==========
    
    async def _get_state(self) -> Optional[Dict]:
        """Get current match state from cache."""
        state_json = cache.get(self.cache_key)
        if state_json:
            return json.loads(state_json)
        return None
    
    async def _save_state(self, state: Dict):
        """Save match state to cache."""
        cache.set(self.cache_key, json.dumps(state), timeout=7200)  # 2 hours
    
    async def _broadcast_to_match(self, event: str, payload: dict):
        """Broadcast event to all players in the match."""
        await self.channel_layer.group_send(
            f"match_{self.match_id}",
            {
                'type': 'match_event',
                'event': event,
                'payload': payload,
            }
        )
    
    async def _broadcast_to_player(self, puuid: str, event: str, payload: dict):
        """Broadcast event to a specific player."""
        await self.channel_layer.group_send(
            f"player_{puuid}",
            {
                'type': 'player_event',
                'event': event,
                'payload': payload,
            }
        )
    
    async def _process_match_results(self, results: Dict):
        """Process match results and update player stats/ELO."""
        # TODO: Implement ELO calculation and stat updates
        pass
    
    async def _apply_dodge_penalties(self, state: Dict):
        """Apply penalties for dodging/not accepting."""
        # Players who didn't accept
        non_acceptors = set(state['all_players']) - set(state['players_accepted'])
        for puuid in non_acceptors:
            await self._apply_penalty(puuid, "dodge", 5)
    
    async def _apply_penalty(self, puuid: str, penalty_type: str, duration_minutes: int):
        """Apply a cooldown penalty to a player."""
        Player = apps.get_model('scrimgg', 'Player')
        
        # Update player's active_ban status
        await sync_to_async(
            lambda: Player.objects.filter(puuid=puuid).update(
                active_ban=True,
                finish_ban=datetime.now() + timedelta(minutes=duration_minutes)
            )
        )()
        
        print(f"Applied {penalty_type} penalty to {puuid}: {duration_minutes} minutes")
    
    async def _cleanup(self):
        """Clean up match state after completion/cancellation."""
        # Could delete from cache or move to persistent storage
        pass

