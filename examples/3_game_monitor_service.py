# Scrim.GG_Client/scrimgg/backend/game_monitor.py
# Monitors local Valorant client and broadcasts state changes

import asyncio
from datetime import datetime
from typing import Callable, Optional, Dict, Any


class ValorantGameMonitor:
    """
    Continuously monitors the local Valorant client for state changes
    and broadcasts them via callback to the frontend.
    
    Similar to FACEIT's client monitoring that detects:
    - When a player is in menus vs in-game
    - Match start/end detection
    - Party changes
    - Disconnections
    """
    
    def __init__(self, valclient):
        """
        Args:
            valclient: Instance of the Valorant API client
        """
        self.client = valclient
        self.running = False
        self.poll_interval = 2  # Poll every 2 seconds
        
        # State tracking
        self.last_state = {
            'game_state': 'UNKNOWN',  # MENUS, PREGAME, INGAME, etc.
            'party_id': None,
            'match_id': None,
            'session_id': None,
            'in_custom_game': False,
        }
        
        self.current_match_id = None
        self.match_start_time = None
        self.broadcast_callback: Optional[Callable] = None
    
    async def start_monitoring(self, broadcast_callback: Callable):
        """
        Start the monitoring loop.
        
        Args:
            broadcast_callback: Function to call when broadcasting events
                               Should accept (event: str, payload: dict)
        """
        self.running = True
        self.broadcast_callback = broadcast_callback
        
        print("🎮 Starting Valorant game state monitor...")
        
        # Start monitoring loop
        await self._monitor_loop()
    
    async def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.running = False
        print("🛑 Stopping game monitor...")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                await self._check_game_state()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _check_game_state(self):
        """
        Check the current Valorant client state and detect changes.
        """
        try:
            # Fetch current presence/session from Valorant client
            presence = self.client.fetch_presence()
            current_state = self._parse_game_state(presence)
            
            # Detect and broadcast state changes
            await self._detect_state_changes(current_state)
            
            # Update last known state
            self.last_state = current_state
            
        except Exception as e:
            print(f"Error fetching game state: {e}")
    
    def _parse_game_state(self, presence: dict) -> dict:
        """
        Parse the Valorant presence data into a simplified state.
        
        Args:
            presence: Raw presence data from Valorant API
            
        Returns:
            Simplified state dictionary
        """
        if not presence:
            return self.last_state
        
        # Extract relevant fields (adjust based on actual Valorant API response)
        session_loop_state = presence.get('sessionLoopState', 'UNKNOWN')
        party_id = presence.get('partyId')
        match_id = presence.get('matchId') or presence.get('provisioningFlowId')
        
        # Determine if in custom game
        is_custom = presence.get('isCustomGame', False) or \
                   presence.get('queueId', '').lower() == 'custom'
        
        return {
            'game_state': session_loop_state,
            'party_id': party_id,
            'match_id': match_id,
            'session_id': presence.get('sessionId'),
            'in_custom_game': is_custom,
            'timestamp': datetime.now().isoformat(),
        }
    
    async def _detect_state_changes(self, current_state: dict):
        """
        Compare current state to last state and broadcast changes.
        """
        
        # 1. Game state changed (MENUS → PREGAME → INGAME, etc.)
        if current_state['game_state'] != self.last_state['game_state']:
            await self._broadcast('game_state_change', {
                'previous': self.last_state['game_state'],
                'current': current_state['game_state'],
                'timestamp': current_state['timestamp'],
            })
            
            # Special handling for match start
            if current_state['game_state'] == 'INGAME' and \
               self.last_state['game_state'] in ['PREGAME', 'MENUS']:
                await self._on_match_start(current_state)
            
            # Special handling for match end
            if self.last_state['game_state'] == 'INGAME' and \
               current_state['game_state'] == 'MENUS':
                await self._on_match_end()
        
        # 2. Party changed
        if current_state['party_id'] != self.last_state['party_id']:
            await self._broadcast('party_change', {
                'previous_party': self.last_state['party_id'],
                'current_party': current_state['party_id'],
            })
        
        # 3. Match ID changed (joined different match/pregame)
        if current_state['match_id'] != self.last_state['match_id']:
            if current_state['match_id']:
                await self._broadcast('match_id_detected', {
                    'match_id': current_state['match_id'],
                    'is_custom': current_state['in_custom_game'],
                })
        
        # 4. Entered custom game
        if current_state['in_custom_game'] and not self.last_state['in_custom_game']:
            await self._broadcast('entered_custom_game', {
                'match_id': current_state['match_id'],
            })
        
        # 5. Left custom game
        if not current_state['in_custom_game'] and self.last_state['in_custom_game']:
            await self._broadcast('left_custom_game', {})
    
    async def _on_match_start(self, state: dict):
        """
        Called when a match starts (transition to INGAME).
        """
        self.current_match_id = state['match_id']
        self.match_start_time = datetime.now()
        
        print(f"🎮 Match started: {self.current_match_id}")
        
        await self._broadcast('match_started', {
            'match_id': self.current_match_id,
            'start_time': self.match_start_time.isoformat(),
            'is_custom': state['in_custom_game'],
        })
        
        # Notify Django server that match has started
        # (This confirms all players joined successfully)
    
    async def _on_match_end(self):
        """
        Called when a match ends (transition from INGAME to MENUS).
        """
        if not self.current_match_id:
            return
        
        match_duration = None
        if self.match_start_time:
            match_duration = (datetime.now() - self.match_start_time).total_seconds()
        
        print(f"🏁 Match ended: {self.current_match_id} (Duration: {match_duration}s)")
        
        await self._broadcast('match_ended', {
            'match_id': self.current_match_id,
            'end_time': datetime.now().isoformat(),
            'duration_seconds': match_duration,
        })
        
        # Fetch match results
        await self._fetch_match_results(self.current_match_id)
        
        # Reset match tracking
        self.current_match_id = None
        self.match_start_time = None
    
    async def _fetch_match_results(self, match_id: str):
        """
        Fetch match results from Valorant API and send to Django server.
        
        This is critical for FACEIT-like experience:
        - Automatic stat collection
        - ELO updates
        - Match history
        """
        try:
            # Give Valorant a few seconds to finalize the match
            await asyncio.sleep(5)
            
            # Fetch match details from Valorant API
            match_details = self.client.coregame_fetch_match(match_id)
            
            if match_details:
                # Parse and send to Django server
                await self._broadcast('match_results_ready', {
                    'match_id': match_id,
                    'details': match_details,
                })
                
                print(f"📊 Match results collected for {match_id}")
            else:
                print(f"⚠️ Could not fetch match results for {match_id}")
                
        except Exception as e:
            print(f"❌ Error fetching match results: {e}")
    
    async def _broadcast(self, event: str, payload: dict):
        """
        Broadcast an event to the frontend via callback.
        """
        if self.broadcast_callback:
            try:
                await self.broadcast_callback(event, payload)
            except Exception as e:
                print(f"Error broadcasting event {event}: {e}")
    
    def get_current_state(self) -> dict:
        """Get the current game state."""
        return self.last_state.copy()
    
    async def force_check(self):
        """Force an immediate state check (useful for debugging)."""
        await self._check_game_state()


# Example usage
if __name__ == "__main__":
    from valclient import Client
    
    async def test_callback(event, payload):
        print(f"📡 Event: {event}")
        print(f"   Payload: {payload}")
    
    async def main():
        # Initialize Valorant client
        client = Client(region="na")
        client.activate()
        
        # Create and start monitor
        monitor = ValorantGameMonitor(client)
        await monitor.start_monitoring(test_callback)
    
    asyncio.run(main())

