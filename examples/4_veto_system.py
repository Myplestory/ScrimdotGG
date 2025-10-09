# ScrimGG/scrimgg/server/scrimgg/matchmaking/veto_system.py
# Map/Server veto system similar to FACEIT

from enum import Enum
from typing import List, Dict, Optional
from django.core.cache import cache
import json


class VetoAction(Enum):
    BAN = "ban"
    PICK = "pick"


class VetoType(Enum):
    MAP = "map"
    SERVER = "server"


class VetoSystem:
    """
    Manages the map and server veto (ban/pick) system for matches.
    
    Standard flow (best-of-1):
    1. Team A bans a map
    2. Team B bans a map
    3. Team A bans a map
    4. Team B bans a map
    5. Team A bans a map
    6. Team B bans a map
    7. Last map remaining is played
    8. Team A picks server
    
    For best-of-3 or more complex formats, the flow can be adjusted.
    """
    
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.cache_key = f"veto:{match_id}"
        self.timeout_seconds = 300  # 5 minutes total veto time
    
    def initialize_veto(
        self,
        team_a_lobbies: List[str],
        team_b_lobbies: List[str],
        available_maps: List[str],
        available_servers: List[str],
        veto_format: str = "bo1"
    ) -> Dict:
        """
        Initialize the veto process for a match.
        
        Args:
            team_a_lobbies: List of lobby IDs for team A
            team_b_lobbies: List of lobby IDs for team B
            available_maps: List of map names
            available_servers: List of server region names
            veto_format: "bo1", "bo3", "bo5", etc.
        
        Returns:
            Initial veto state
        """
        
        # Define veto sequence based on format
        if veto_format == "bo1":
            # Best of 1: Ban until 1 map remains, then pick server
            veto_sequence = [
                {'team': 'a', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                {'team': 'b', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                {'team': 'a', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                {'team': 'b', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                {'team': 'a', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                {'team': 'b', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                # Last map auto-selected
                {'team': 'a', 'action': VetoAction.PICK, 'type': VetoType.SERVER},
            ]
        elif veto_format == "bo3":
            # Best of 3: More complex
            veto_sequence = [
                {'team': 'a', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                {'team': 'b', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                {'team': 'a', 'action': VetoAction.PICK, 'type': VetoType.MAP},  # Map 1
                {'team': 'b', 'action': VetoAction.PICK, 'type': VetoType.MAP},  # Map 2
                {'team': 'a', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                {'team': 'b', 'action': VetoAction.BAN, 'type': VetoType.MAP},
                # Last map is Map 3
                {'team': 'a', 'action': VetoAction.PICK, 'type': VetoType.SERVER},
            ]
        else:
            raise ValueError(f"Unknown veto format: {veto_format}")
        
        veto_state = {
            'match_id': self.match_id,
            'team_a_lobbies': team_a_lobbies,
            'team_b_lobbies': team_b_lobbies,
            'available_maps': available_maps.copy(),
            'available_servers': available_servers.copy(),
            'banned_maps': [],
            'picked_maps': [],
            'banned_servers': [],
            'picked_server': None,
            'veto_sequence': veto_sequence,
            'current_step': 0,
            'history': [],
            'completed': False,
            'final_map': None,
            'final_server': None,
            'format': veto_format,
        }
        
        # Store in cache
        cache.set(self.cache_key, json.dumps(veto_state), timeout=self.timeout_seconds)
        
        return veto_state
    
    def get_veto_state(self) -> Optional[Dict]:
        """Get the current veto state."""
        state_json = cache.get(self.cache_key)
        if state_json:
            return json.loads(state_json)
        return None
    
    def _save_state(self, state: Dict):
        """Save veto state to cache."""
        cache.set(self.cache_key, json.dumps(state), timeout=self.timeout_seconds)
    
    def get_current_turn(self) -> Optional[Dict]:
        """
        Get information about whose turn it is.
        
        Returns:
            Dict with 'team', 'action', 'type', or None if veto is complete
        """
        state = self.get_veto_state()
        if not state or state['completed']:
            return None
        
        current_step = state['current_step']
        if current_step >= len(state['veto_sequence']):
            return None
        
        return state['veto_sequence'][current_step]
    
    def is_player_turn(self, lobby_id: str) -> bool:
        """
        Check if it's the turn of a player in the given lobby.
        """
        state = self.get_veto_state()
        if not state:
            return False
        
        current_turn = self.get_current_turn()
        if not current_turn:
            return False
        
        team = current_turn['team']
        if team == 'a':
            return lobby_id in state['team_a_lobbies']
        else:
            return lobby_id in state['team_b_lobbies']
    
    def execute_veto_action(
        self,
        lobby_id: str,
        action: str,
        veto_type: str,
        value: str
    ) -> Dict:
        """
        Execute a veto action (ban or pick).
        
        Args:
            lobby_id: ID of the lobby making the action
            action: "ban" or "pick"
            veto_type: "map" or "server"
            value: The map or server being banned/picked
        
        Returns:
            Updated veto state
        
        Raises:
            ValueError: If action is invalid
        """
        state = self.get_veto_state()
        if not state:
            raise ValueError("Veto not initialized")
        
        if state['completed']:
            raise ValueError("Veto already completed")
        
        # Verify it's this player's turn
        if not self.is_player_turn(lobby_id):
            raise ValueError("Not your turn")
        
        current_turn = self.get_current_turn()
        expected_action = current_turn['action'].value
        expected_type = current_turn['type'].value
        
        if action != expected_action or veto_type != expected_type:
            raise ValueError(f"Expected {expected_action} {expected_type}, got {action} {veto_type}")
        
        # Validate the value
        if veto_type == "map":
            if value not in state['available_maps']:
                raise ValueError(f"Map {value} not available")
        elif veto_type == "server":
            if value not in state['available_servers']:
                raise ValueError(f"Server {value} not available")
        
        # Execute the action
        if action == "ban":
            if veto_type == "map":
                state['banned_maps'].append(value)
                state['available_maps'].remove(value)
            elif veto_type == "server":
                state['banned_servers'].append(value)
                state['available_servers'].remove(value)
        elif action == "pick":
            if veto_type == "map":
                state['picked_maps'].append(value)
                state['available_maps'].remove(value)
            elif veto_type == "server":
                state['picked_server'] = value
        
        # Record in history
        state['history'].append({
            'step': state['current_step'],
            'team': current_turn['team'],
            'action': action,
            'type': veto_type,
            'value': value,
        })
        
        # Move to next step
        state['current_step'] += 1
        
        # Check if veto is complete
        if state['current_step'] >= len(state['veto_sequence']):
            state['completed'] = True
            
            # Determine final map and server
            if state['format'] == "bo1":
                # Last remaining map
                if len(state['available_maps']) == 1:
                    state['final_map'] = state['available_maps'][0]
                else:
                    # Shouldn't happen, but handle gracefully
                    state['final_map'] = state['available_maps'][0] if state['available_maps'] else None
            elif state['format'] == "bo3":
                # Use picked maps
                state['final_map'] = state['picked_maps']
            
            state['final_server'] = state['picked_server']
        
        # Save updated state
        self._save_state(state)
        
        return state
    
    def auto_complete_remaining_steps(self) -> Dict:
        """
        Auto-complete any remaining veto steps (used for timeout).
        Randomly selects remaining actions.
        """
        import random
        
        state = self.get_veto_state()
        if not state or state['completed']:
            return state
        
        while not state['completed']:
            current_turn = self.get_current_turn()
            if not current_turn:
                break
            
            veto_type = current_turn['type'].value
            action = current_turn['action'].value
            
            # Randomly select
            if veto_type == "map":
                if state['available_maps']:
                    value = random.choice(state['available_maps'])
                else:
                    break
            elif veto_type == "server":
                if state['available_servers']:
                    value = random.choice(state['available_servers'])
                else:
                    break
            
            # Execute the action
            # Determine which lobby to attribute it to (first one in team)
            team = current_turn['team']
            lobby_id = state['team_a_lobbies'][0] if team == 'a' else state['team_b_lobbies'][0]
            
            try:
                state = self.execute_veto_action(lobby_id, action, veto_type, value)
            except Exception as e:
                print(f"Error auto-completing veto: {e}")
                break
        
        return state
    
    def get_veto_summary(self) -> Dict:
        """
        Get a human-readable summary of the veto process.
        """
        state = self.get_veto_state()
        if not state:
            return {}
        
        return {
            'match_id': self.match_id,
            'completed': state['completed'],
            'final_map': state.get('final_map'),
            'final_server': state.get('final_server'),
            'banned_maps': state['banned_maps'],
            'picked_maps': state.get('picked_maps', []),
            'history': state['history'],
            'current_turn': self.get_current_turn(),
        }


# Usage example in Django Consumer
"""
# In consumers.py

async def handle_veto_action(self, data):
    match_id = data.get('match_id')
    action = data.get('action')  # "ban" or "pick"
    veto_type = data.get('type')  # "map" or "server"
    value = data.get('value')  # e.g., "Ascent"
    
    veto_system = VetoSystem(match_id)
    
    try:
        # Execute the veto action
        updated_state = veto_system.execute_veto_action(
            lobby_id=self.lobby_id,
            action=action,
            veto_type=veto_type,
            value=value
        )
        
        # Broadcast to all players in the match
        await self.channel_layer.group_send(
            f"match_{match_id}",
            {
                'type': 'veto_updated',
                'state': veto_system.get_veto_summary()
            }
        )
        
        # If veto is complete, proceed to match acceptance
        if updated_state['completed']:
            await self.start_match_acceptance(match_id, updated_state)
            
    except ValueError as e:
        await self.send(text_data=json.dumps({
            'event': 'veto_error',
            'message': str(e)
        }))
"""

