"""
WebSocket connection manager.
Handles connection lifecycle, state, and broadcasting.
"""
from __future__ import annotations
import asyncio
import contextlib
from typing import Dict, Set, Any
from quart import Websocket

class ConnectionManager:
    def __init__(self):
        self.active: Set[Websocket] = set()
        self.state: Dict[int, dict] = {}
        self._last_status: dict | None = None
        self._heartbeat_task: asyncio.Task | None = None
    
    def add(self, ws: Websocket) -> int:
        """Add a new WebSocket connection."""
        cid = id(ws)
        self.active.add(ws)
        self.state[cid] = {
            'puuid': None,
            'authenticated': False,
            'in_game': False,
            'in_queue': False,
            'lobby_id': None,
            'match_id': None,
            'connected': True,
            'websocket': ws,
        }
        print(f"[CONN] Added client {cid}. Total: {len(self.active)}")
        return cid
    
    async def remove(self, ws: Websocket):
        """Remove a WebSocket connection."""
        cid = id(ws)
        self.active.discard(ws)
        removed_state = self.state.pop(cid, None)
        print(f"[CONN] Removed client {cid}. Total: {len(self.active)}")
        return removed_state
    
    async def send(self, ws: Websocket, event: str, payload: Any = None):
        """Send a message to a specific WebSocket."""
        try:
            await ws.send_json({"event": event, "payload": payload})
        except Exception as e:
            print(f"[SEND] Error sending to client: {e}")
            await self.remove(ws)
    
    async def broadcast(self, event: str, payload: Any = None):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for ws in list(self.active):
            try:
                await self.send(ws, event, payload)
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            await self.remove(ws)
    
    async def broadcast_with_client_context(self, event: str, base_payload: dict):
        """
        Broadcast with per-client customization.
        Used for status updates that include client-specific auth state.
        """
        disconnected = []
        for ws in list(self.active):
            try:
                cid = id(ws)
                client_payload = base_payload.copy()
                
                # Add client-specific fields
                if 'authenticated' in client_payload and client_payload['authenticated'] is None:
                    client_payload['authenticated'] = self.state[cid].get('authenticated', False)
                
                await self.send(ws, event, client_payload)
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            await self.remove(ws)
    
    async def start_heartbeat(self, valorant_service):
        """Start the heartbeat monitoring loop."""
        print("[HEARTBEAT] Starting...")
        
        try:
            while True:
                # Check if any clients are connected
                if not self.active:
                    await asyncio.sleep(3)
                    continue
                
                try:
                    # Get Valorant status
                    current_status = await valorant_service.check_status()
                    
                    # Only broadcast if status changed
                    if current_status != self._last_status:
                        print(f"[HEARTBEAT] Status changed: {self._last_status} -> {current_status}")
                        self._last_status = current_status
                        
                        await self.broadcast_with_client_context('status_update', {
                            'backend_connected': True,
                            'valorant': current_status,
                            'authenticated': None  # Will be set per client
                        })
                    
                    # Drain pending events from Django WS
                    await self._drain_pending_events(valorant_service)
                    
                except Exception as e:
                    print(f"[HEARTBEAT] Error: {e}")
                
                await asyncio.sleep(3)
                
        except asyncio.CancelledError:
            print("[HEARTBEAT] Stopped")
            raise
    
    async def _drain_pending_events(self, valorant_service):
        """Forward pending events from ValorantAPI to frontend clients.
        
        NOTE: Time-sensitive events (veto_update, veto_complete, veto_acknowledged, side_selected)
        are now immediately broadcasted and no longer batched here.
        """
        pending_events = [
            ('_pending_match_data', 'pug_match_found'),
            ('_pending_match_proposed_data', 'match_acceptance_required'),
            ('_pending_player_accepted_data', 'player_accepted'),
            ('_pending_match_ready_data', 'match_ready'),
            ('_pending_match_confirmed_data', 'match_confirmed'),
            ('_pending_map_veto_started_data', 'map_veto_started'),
            ('_pending_match_data_response', 'match_data'),
            # Removed: veto_update, veto_complete, veto_acknowledged, side_selected (now immediate)
        ]
        
        for attr_name, event_name in pending_events:
            # Access pending events from api (ValorantAPI instance)
            data = getattr(valorant_service.api, attr_name, None)
            if data:
                setattr(valorant_service.api, attr_name, None)
                await self.broadcast(event_name, data)
                print(f"[HEARTBEAT] Broadcasted {event_name}")
    
    async def close_all(self):
        """Close all connections gracefully."""
        print("[CONN] Closing all connections...")
        for ws in list(self.active):
            with contextlib.suppress(Exception):
                await ws.close()
        self.active.clear()
        self.state.clear()

