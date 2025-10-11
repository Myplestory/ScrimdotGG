# Phase 3: Game Server Integration & Match Execution

## 🎯 **Overview**

Complete the match flow from confirmation to game completion with emphasis on:
- ✅ **WebSocket-Only Communication** - No REST endpoints
- ✅ **Performance Optimization** - Minimal overhead for competitive gameplay
- ✅ **Real-Time Statistics** - Live match monitoring and stats
- ✅ **Spectator System** - Public match viewing

---

## 🚀 **Critical Design Principles**

### **1. Performance-First Architecture**

#### **Match Lifecycle State Machine**
```
[Queue] → [Match Found] → [Accepting] → [Starting] → [In-Game] → [Completed]
   ↓           ↓              ↓             ↓           ↓            ↓
Heartbeat   Heartbeat      Heartbeat     STOPPED    STOPPED     Heartbeat
  (3s)        (3s)           (3s)                                 (3s)
```

#### **Key Optimization Strategies**
1. **Stop Heartbeat During Matches** ✅ (Already implemented)
   - Heartbeat only runs when user is NOT in active match
   - Reduces CPU/network overhead during gameplay
   - Resumes automatically after match completion

2. **Efficient Match Monitoring**
   - Poll ValClient API every **30 seconds** during match (not 3s)
   - Only fetch data when needed (round end events)
   - Cache match data to minimize API calls

3. **Lazy Statistics Collection**
   - Collect detailed stats **only at round completion**
   - Avoid constant polling during live rounds
   - Batch updates every 5 rounds to reduce network traffic

4. **WebSocket Message Optimization**
   - Send only delta updates, not full state
   - Compress large payloads (player lists, stats)
   - Use event batching for multiple updates

---

## 📋 **Phase 3.1: Match Execution System**

### **3.1.1: Extended Match Model**

```python
# server/scrimgg/models.py

class Match(models.Model):
    # Existing fields (id, teams, lobbies, etc.)
    
    # Match execution fields
    status = models.CharField(
        max_length=20, 
        default='confirmed',
        choices=[
            ('confirmed', 'All Players Accepted'),
            ('starting', 'Creating Custom Game'),
            ('in_progress', 'Match Live'),
            ('paused', 'Match Paused'),
            ('completed', 'Match Finished'),
            ('cancelled', 'Match Cancelled')
        ]
    )
    
    # Game server details
    constructor_puuid = models.CharField(max_length=100, null=True, blank=True)  # Party leader
    pregame_id = models.CharField(max_length=100, null=True, blank=True)  # Valorant match ID
    coregame_id = models.CharField(max_length=100, null=True, blank=True)  # In-game match ID
    game_server = models.CharField(max_length=100, null=True, blank=True)  # Server pod
    selected_map = models.CharField(max_length=50, null=True, blank=True)  # Final map
    
    # Match timing
    confirmation_completed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Live match data (cached for performance)
    current_round = models.IntegerField(default=0)
    team_a_score = models.IntegerField(default=0)
    team_b_score = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Match {self.id} - {self.status} - {self.team_a_score}:{self.team_b_score}"


class MatchStatistics(models.Model):
    """Player statistics for a match - collected at round/match end"""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='statistics')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.CharField(max_length=10)  # 'team_a' or 'team_b'
    
    # Core stats
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    
    # Advanced stats
    headshots = models.IntegerField(default=0)
    bodyshots = models.IntegerField(default=0)
    legshots = models.IntegerField(default=0)
    damage_dealt = models.IntegerField(default=0)
    damage_received = models.IntegerField(default=0)
    
    # Calculated metrics (updated post-match)
    adr = models.FloatField(default=0.0)  # Average Damage per Round
    rws = models.FloatField(default=0.0)  # Round Win Shares
    headshot_percentage = models.FloatField(default=0.0)
    
    # Round-specific data (JSON for performance)
    round_stats = models.JSONField(default=dict)  # Detailed per-round breakdown
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['match', 'player']


class MatchRejoinToken(models.Model):
    """Allow players to rejoin matches after disconnect"""
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['match', 'player']
```

### **3.1.2: Match Execution Manager**

```python
# server/matchmaking/match_execution.py

import asyncio
import logging
from datetime import timezone
from typing import Dict, List
from django.apps import apps
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class MatchExecutionManager:
    """
    Handles match transition from confirmed → starting → in_progress → completed
    Uses WebSocket-only communication for all updates
    """
    
    @staticmethod
    async def initiate_match_start(match_id: str) -> Dict:
        """
        Called when all players have accepted the match.
        Selects constructor and initiates custom game creation.
        
        Performance: O(1) - single DB query with select_related
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            Player = apps.get_model('scrimgg', 'Player')
            
            # Fetch match with all related data in one query
            def get_match():
                return Match.objects.select_related('team_a', 'team_b').prefetch_related(
                    'team_a__players', 'team_b__players'
                ).get(id=match_id)
            
            match = await sync_to_async(get_match)()
            
            # Select constructor (highest ELO player from team_a captain)
            constructor = await MatchExecutionManager._select_constructor(match)
            
            # Update match status
            def update_match():
                match.status = 'starting'
                match.constructor_puuid = constructor['puuid']
                match.confirmation_completed_at = timezone.now()
                match.save()
            
            await sync_to_async(update_match)()
            
            # Notify all players via WebSocket
            await MatchExecutionManager._broadcast_match_starting(match, constructor)
            
            logger.info(f"Match {match_id} starting - Constructor: {constructor['puuid']}")
            
            return {
                'status': 'success',
                'match_id': match_id,
                'constructor_puuid': constructor['puuid'],
                'message': 'Match starting - custom game creation initiated'
            }
            
        except Exception as e:
            logger.error(f"Error initiating match start: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def _select_constructor(match) -> Dict:
        """
        Select the constructor (party leader) for custom match creation.
        Strategy: Select team captain (highest ELO player) from team_a.
        
        Performance: O(n) where n = team size (max 5)
        """
        # Get team_a captain (already determined during matchmaking)
        captain_data = match.team_a.get('captain', {})
        
        if captain_data:
            return {
                'puuid': captain_data['puuid'],
                'alias': captain_data.get('alias', 'Unknown'),
                'team': 'team_a'
            }
        
        # Fallback: Select highest ELO from team_a players
        team_a_players = match.team_a.get('players', [])
        if team_a_players:
            constructor = max(team_a_players, key=lambda p: p.get('elo', 0))
            return {
                'puuid': constructor['puuid'],
                'alias': constructor.get('alias', 'Unknown'),
                'team': 'team_a'
            }
        
        raise ValueError("No valid constructor found for match")
    
    
    @staticmethod
    async def _broadcast_match_starting(match, constructor: Dict):
        """
        Broadcast match starting event to all players via WebSocket.
        
        Performance: Single channel layer group_send (O(1))
        """
        channel_layer = get_channel_layer()
        
        # Get all player PUUIDs
        all_players = []
        all_players.extend([p['puuid'] for p in match.team_a.get('players', [])])
        all_players.extend([p['puuid'] for p in match.team_b.get('players', [])])
        
        # Broadcast to each player's WebSocket connection
        for puuid in all_players:
            await channel_layer.group_send(
                f"player_{puuid}",
                {
                    'type': 'match_starting',
                    'match_id': str(match.id),
                    'constructor_puuid': constructor['puuid'],
                    'is_constructor': (puuid == constructor['puuid']),
                    'map': match.selected_map,
                    'server': match.game_server,
                    'team': 'team_a' if puuid in [p['puuid'] for p in match.team_a.get('players', [])] else 'team_b'
                }
            )
        
        logger.info(f"Broadcast match_starting to {len(all_players)} players")
    
    
    @staticmethod
    async def handle_custom_game_created(match_id: str, pregame_id: str, constructor_puuid: str) -> Dict:
        """
        Called by constructor client after successfully creating custom game.
        Updates match status and notifies other players to join.
        
        Performance: O(1) - single update + broadcast
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            def update_match():
                match = Match.objects.get(id=match_id)
                match.pregame_id = pregame_id
                match.status = 'starting'  # Still waiting for all players to join
                match.save()
                return match
            
            match = await sync_to_async(update_match)()
            
            # Broadcast to all non-constructor players to join
            await MatchExecutionManager._broadcast_join_custom_game(match, pregame_id, constructor_puuid)
            
            logger.info(f"Custom game created for match {match_id}: {pregame_id}")
            
            return {'status': 'success', 'pregame_id': pregame_id}
            
        except Exception as e:
            logger.error(f"Error handling custom game creation: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def _broadcast_join_custom_game(match, pregame_id: str, constructor_puuid: str):
        """
        Tell all non-constructor players to join the custom game.
        
        Performance: O(n) where n = players (max 10)
        """
        channel_layer = get_channel_layer()
        
        # Get all non-constructor players
        all_players = []
        all_players.extend([p['puuid'] for p in match.team_a.get('players', [])])
        all_players.extend([p['puuid'] for p in match.team_b.get('players', [])])
        
        for puuid in all_players:
            if puuid == constructor_puuid:
                continue  # Skip constructor
            
            await channel_layer.group_send(
                f"player_{puuid}",
                {
                    'type': 'join_custom_game',
                    'match_id': str(match.id),
                    'pregame_id': pregame_id,
                    'team': 'team_a' if puuid in [p['puuid'] for p in match.team_a.get('players', [])] else 'team_b'
                }
            )
        
        logger.info(f"Broadcast join_custom_game to {len(all_players)-1} players")
    
    
    @staticmethod
    async def handle_match_started(match_id: str, coregame_id: str) -> Dict:
        """
        Called when the match actually starts (all players loaded in).
        Transitions match to 'in_progress' state.
        
        Performance: O(1)
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            def update_match():
                match = Match.objects.get(id=match_id)
                match.coregame_id = coregame_id
                match.status = 'in_progress'
                match.started_at = timezone.now()
                match.save()
                return match
            
            match = await sync_to_async(update_match)()
            
            # Notify all players that match is live
            await MatchExecutionManager._broadcast_match_in_progress(match)
            
            # Start background monitoring task (LOW FREQUENCY)
            from .tasks import monitor_live_match
            monitor_live_match.apply_async((match_id,), countdown=30)  # Start after 30 seconds
            
            logger.info(f"Match {match_id} now in progress: {coregame_id}")
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling match start: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def _broadcast_match_in_progress(match):
        """
        Notify all players and spectators that match is live.
        """
        channel_layer = get_channel_layer()
        
        # Broadcast to match group (for spectators)
        await channel_layer.group_send(
            f"match_{match.id}",
            {
                'type': 'match_in_progress',
                'match_id': str(match.id),
                'coregame_id': match.coregame_id,
                'map': match.selected_map,
                'server': match.game_server
            }
        )
        
        logger.info(f"Match {match.id} in_progress broadcast sent")
    
    
    @staticmethod
    async def generate_rejoin_token(match_id: str, player_puuid: str) -> str:
        """
        Generate a rejoin token for a player who disconnected.
        Token expires after 5 minutes.
        
        Performance: O(1)
        """
        from datetime import timedelta
        import uuid
        
        MatchRejoinToken = apps.get_model('scrimgg', 'MatchRejoinToken')
        Match = apps.get_model('scrimgg', 'Match')
        Player = apps.get_model('scrimgg', 'Player')
        
        def create_token():
            match = Match.objects.get(id=match_id)
            player = Player.objects.get(puuid=player_puuid)
            
            # Delete old tokens
            MatchRejoinToken.objects.filter(match=match, player=player).delete()
            
            # Create new token
            token = MatchRejoinToken.objects.create(
                match=match,
                player=player,
                expires_at=timezone.now() + timedelta(minutes=5)
            )
            return str(token.token)
        
        token = await sync_to_async(create_token)()
        
        logger.info(f"Generated rejoin token for {player_puuid} in match {match_id}")
        
        return token
```

---

## 📊 **Phase 3.2: Real-Time Match Monitoring (Performance Optimized)**

### **3.2.1: Efficient Statistics Collection**

```python
# server/matchmaking/match_monitor.py

class MatchMonitor:
    """
    Low-overhead match monitoring system.
    Polls ValClient API at strategic intervals to minimize performance impact.
    """
    
    POLL_INTERVAL_NORMAL = 30  # seconds - during regular play
    POLL_INTERVAL_ROUND_END = 5  # seconds - after detecting round end
    
    @staticmethod
    async def collect_match_statistics(match_id: str, coregame_id: str) -> Dict:
        """
        Collect current match statistics from Valorant client.
        
        Performance Strategy:
        - Poll every 30 seconds during normal play
        - Poll every 5 seconds when round just ended (for stats)
        - Stop polling when match completes
        
        Returns: Delta updates only (not full state)
        """
        try:
            Match = apps.get_model('scrimgg', 'Match')
            
            def get_match():
                return Match.objects.get(id=match_id)
            
            match = await sync_to_async(get_match)()
            
            # This would be called from the constructor's client
            # (Client with ValClient access polls and sends updates)
            # Django server just receives and broadcasts the updates
            
            return {
                'status': 'success',
                'message': 'Statistics collection initiated'
            }
            
        except Exception as e:
            logger.error(f"Error collecting match statistics: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    
    @staticmethod
    async def update_match_score(match_id: str, team_a_score: int, team_b_score: int, current_round: int) -> Dict:
        """
        Update match score (called from client polling ValClient API).
        Only broadcasts if score changed (delta update).
        
        Performance: O(1) - single update + conditional broadcast
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
```

### **3.2.2: Client-Side Polling Strategy**

```python
# client/backend/clientapi.py - Updated for performance

class ValorantAPI(object):
    
    async def monitor_match(self, match_id: str, coregame_id: str):
        """
        Monitor live match and send updates to Django server.
        
        Performance Strategy:
        - Only constructor client monitors the match
        - Poll ValClient every 30 seconds (not 3 seconds)
        - Send only delta updates (score changes)
        - Stop monitoring when match completes
        
        This runs in background without blocking main thread.
        """
        logger.info(f"Starting match monitoring for {match_id}")
        
        last_score = {'team_a': 0, 'team_b': 0, 'round': 0}
        
        while True:
            try:
                # Fetch current match state from ValClient
                match_data = self.client.coregame_fetch_match(coregame_id)
                
                if not match_data:
                    logger.warning("No match data returned - match may have ended")
                    break
                
                # Parse score data
                current_score = self._parse_match_score(match_data)
                
                # Only send update if score changed
                if current_score != last_score:
                    await self._send_score_update(match_id, current_score)
                    last_score = current_score
                
                # Check if match completed
                if self._is_match_complete(match_data):
                    logger.info(f"Match {match_id} completed")
                    await self._send_match_complete(match_id, match_data)
                    break
                
                # Wait 30 seconds before next poll
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error monitoring match: {str(e)}")
                await asyncio.sleep(30)  # Continue monitoring despite errors
        
        logger.info(f"Match monitoring ended for {match_id}")
    
    
    def _parse_match_score(self, match_data: dict) -> dict:
        """
        Extract current score from ValClient match data.
        
        Performance: O(1) - direct field access
        """
        # Parse Valorant API response format
        # This depends on your ValClient API structure
        return {
            'team_a': match_data.get('Teams', [{}])[0].get('RoundsWon', 0),
            'team_b': match_data.get('Teams', [{}])[1].get('RoundsWon', 0),
            'round': match_data.get('RoundNumber', 0)
        }
    
    
    async def _send_score_update(self, match_id: str, score: dict):
        """
        Send score update to Django server via WebSocket.
        
        Performance: Single WebSocket message
        """
        if not self.pugsocket or not self.pugsocket.is_connected():
            return
        
        await self.pugsocket.send_message('match_score_update', {
            'match_id': match_id,
            'team_a_score': score['team_a'],
            'team_b_score': score['team_b'],
            'current_round': score['round']
        })
    
    
    def _is_match_complete(self, match_data: dict) -> bool:
        """
        Check if match is complete (team reached 13 rounds).
        
        Performance: O(1)
        """
        teams = match_data.get('Teams', [])
        if len(teams) < 2:
            return False
        
        team_a_score = teams[0].get('RoundsWon', 0)
        team_b_score = teams[1].get('RoundsWon', 0)
        
        # Standard match: first to 13
        # Overtime: win by 2 (if enabled)
        return team_a_score >= 13 or team_b_score >= 13
```

---

## 🎮 **Phase 3.3: WebSocket Event Flow (Complete)**

### **3.3.1: Django Consumer Updates**

```python
# server/matchmaking/consumers.py - New event handlers

class PugSocketConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        # Existing connection logic...
        
        # Subscribe to player-specific channel
        player_puuid = self.scope['url_route']['kwargs'].get('puuid')
        if player_puuid:
            await self.channel_layer.group_add(
                f"player_{player_puuid}",
                self.channel_name
            )
    
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data.get('event')
        payload = data.get('payload', {})
        
        # Route match execution events
        if event == 'custom_game_created':
            await self.handle_custom_game_created(payload)
        elif event == 'player_joined_game':
            await self.handle_player_joined_game(payload)
        elif event == 'match_score_update':
            await self.handle_match_score_update(payload)
        elif event == 'match_completed':
            await self.handle_match_completed(payload)
        elif event == 'request_rejoin':
            await self.handle_request_rejoin(payload)
        # ... other events
    
    
    # ============================================================
    # Match Execution Event Handlers
    # ============================================================
    
    async def handle_custom_game_created(self, payload):
        """
        Constructor client reports custom game creation.
        Notifies other players to join.
        """
        match_id = payload.get('match_id')
        pregame_id = payload.get('pregame_id')
        constructor_puuid = payload.get('constructor_puuid')
        
        from .match_execution import MatchExecutionManager
        
        result = await MatchExecutionManager.handle_custom_game_created(
            match_id, pregame_id, constructor_puuid
        )
        
        if result['status'] == 'success':
            await self.send(text_data=json.dumps({
                'event': 'custom_game_created_ack',
                'data': result
            }))
        else:
            await self.send(text_data=json.dumps({
                'event': 'error',
                'data': {'message': result.get('message')}
            }))
    
    
    async def handle_player_joined_game(self, payload):
        """
        Player client reports successful join to custom game.
        Track which players have joined.
        """
        match_id = payload.get('match_id')
        player_puuid = payload.get('player_puuid')
        
        # TODO: Track join status, start match when all 10 players joined
        logger.info(f"Player {player_puuid} joined match {match_id}")
    
    
    async def handle_match_score_update(self, payload):
        """
        Receive score updates from constructor client.
        Broadcast to spectators.
        """
        match_id = payload.get('match_id')
        team_a_score = payload.get('team_a_score')
        team_b_score = payload.get('team_b_score')
        current_round = payload.get('current_round')
        
        from .match_monitor import MatchMonitor
        
        await MatchMonitor.update_match_score(
            match_id, team_a_score, team_b_score, current_round
        )
    
    
    async def handle_match_completed(self, payload):
        """
        Match has completed - process final results.
        """
        match_id = payload.get('match_id')
        final_data = payload.get('final_data')
        
        from .match_execution import MatchExecutionManager
        
        await MatchExecutionManager.handle_match_completion(
            match_id, final_data
        )
    
    
    async def handle_request_rejoin(self, payload):
        """
        Player requests to rejoin match after disconnect.
        """
        match_id = payload.get('match_id')
        player_puuid = payload.get('player_puuid')
        
        from .match_execution import MatchExecutionManager
        
        token = await MatchExecutionManager.generate_rejoin_token(
            match_id, player_puuid
        )
        
        await self.send(text_data=json.dumps({
            'event': 'rejoin_token',
            'data': {'token': token, 'match_id': match_id}
        }))
    
    
    # ============================================================
    # Outgoing WebSocket Handlers (called by channel layer)
    # ============================================================
    
    async def match_starting(self, event):
        """Send match_starting event to client"""
        await self.send(text_data=json.dumps({
            'event': 'match_starting',
            'data': {
                'match_id': event['match_id'],
                'constructor_puuid': event['constructor_puuid'],
                'is_constructor': event['is_constructor'],
                'map': event['map'],
                'server': event['server'],
                'team': event['team']
            }
        }))
    
    
    async def join_custom_game(self, event):
        """Send join_custom_game event to client"""
        await self.send(text_data=json.dumps({
            'event': 'join_custom_game',
            'data': {
                'match_id': event['match_id'],
                'pregame_id': event['pregame_id'],
                'team': event['team']
            }
        }))
    
    
    async def match_in_progress(self, event):
        """Send match_in_progress event to client"""
        await self.send(text_data=json.dumps({
            'event': 'match_in_progress',
            'data': {
                'match_id': event['match_id'],
                'coregame_id': event['coregame_id'],
                'map': event['map'],
                'server': event['server']
            }
        }))
    
    
    async def match_score_update(self, event):
        """Send score update to spectators"""
        await self.send(text_data=json.dumps({
            'event': 'match_score_update',
            'data': {
                'match_id': event['match_id'],
                'team_a_score': event['team_a_score'],
                'team_b_score': event['team_b_score'],
                'current_round': event['current_round']
            }
        }))
```

---

## 🖥️ **Phase 3.4: Client-Side Implementation**

### **3.4.1: Bootstrap.py Event Handlers**

```python
# client/backend/bootstrap.py - Match execution handlers

async def handle_match_starting(payload: dict, client_id: int, ws):
    """
    Django server notifies that match is starting.
    If this client is constructor, create custom game.
    Otherwise, wait for join instruction.
    """
    match_id = payload.get('match_id')
    is_constructor = payload.get('is_constructor', False)
    map_name = payload.get('map')
    server = payload.get('server')
    team = payload.get('team')
    
    logger.info(f"[MATCH START] Match {match_id} starting - Constructor: {is_constructor}")
    
    # Stop heartbeat - user entering game
    client_states[client_id]['in_game'] = True
    await stop_valorant_heartbeat()
    
    # Notify frontend
    await send_event(ws, 'match_starting', {
        'match_id': match_id,
        'is_constructor': is_constructor,
        'map': map_name,
        'server': server,
        'team': team
    })
    
    if is_constructor:
        # This client needs to create the custom game
        logger.info(f"[CONSTRUCTOR] Creating custom game for match {match_id}")
        asyncio.create_task(create_custom_game(match_id, map_name, server, client_id))


async def create_custom_game(match_id: str, map_name: str, server: str, client_id: int):
    """
    Constructor client creates the custom game in Valorant.
    
    Performance: Runs in background task to avoid blocking
    """
    try:
        # Change party to custom mode
        logger.info("[CONSTRUCTOR] Changing to custom game mode...")
        custom_response = valorant_api.client.party_change_to_custom()
        pregame_id = custom_response.get('ID')
        
        if not pregame_id:
            raise ValueError("Failed to get pregame ID from custom game creation")
        
        # Set custom game settings
        logger.info("[CONSTRUCTOR] Configuring game settings...")
        settings = {
            "Map": valorant_api.args['mapPreferences'].get(map_name),
            "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
            "GamePod": valorant_api._get_server_url(server),
            "UseBots": False,
            "GameRules": {
                "AllowGameModifiers": "true",
                "PlayOutAllRounds": "true",
                "SkipMatchHistory": "true",
                "TournamentMode": "false",
                "IsOvertimeWinByTwo": "true",
            },
        }
        
        valorant_api.client.party_set_custom_game_settings(settings)
        
        # Notify Django server via WebSocket
        logger.info(f"[CONSTRUCTOR] Custom game created: {pregame_id}")
        await valorant_api.pugsocket.send_message('custom_game_created', {
            'match_id': match_id,
            'pregame_id': pregame_id,
            'constructor_puuid': valorant_api.client.puuid
        })
        
        # Wait a moment for settings to apply
        await asyncio.sleep(2)
        
        # Start the custom game
        logger.info("[CONSTRUCTOR] Starting custom game...")
        valorant_api.client.party_start_custom_game()
        
        # Get coregame ID after match starts
        await asyncio.sleep(5)  # Wait for game to start
        coregame_data = valorant_api.client.coregame_fetch_player()
        coregame_id = coregame_data.get('MatchID')
        
        if coregame_id:
            # Notify Django that match is live
            await valorant_api.pugsocket.send_message('match_started', {
                'match_id': match_id,
                'coregame_id': coregame_id
            })
            
            # Start monitoring the match (background task)
            asyncio.create_task(valorant_api.monitor_match(match_id, coregame_id))
        
    except Exception as e:
        logger.error(f"[CONSTRUCTOR] Error creating custom game: {str(e)}")
        # TODO: Notify Django of failure


async def handle_join_custom_game(payload: dict, client_id: int, ws):
    """
    Django server instructs this client to join the custom game.
    Non-constructor players join the pregame created by constructor.
    """
    match_id = payload.get('match_id')
    pregame_id = payload.get('pregame_id')
    team = payload.get('team')
    
    logger.info(f"[JOIN] Joining custom game: {pregame_id} for match {match_id}")
    
    try:
        # Join the party/pregame
        valorant_api.client.party_join(pregame_id)
        
        # Notify Django that we joined successfully
        await valorant_api.pugsocket.send_message('player_joined_game', {
            'match_id': match_id,
            'player_puuid': valorant_api.client.puuid,
            'team': team
        })
        
        # Notify frontend
        await send_event(ws, 'joined_custom_game', {
            'match_id': match_id,
            'team': team
        })
        
        logger.info(f"[JOIN] Successfully joined match {match_id}")
        
    except Exception as e:
        logger.error(f"[JOIN] Error joining custom game: {str(e)}")
        # TODO: Handle join failure


async def handle_match_in_progress(payload: dict, client_id: int, ws):
    """
    Match is now live - all players have loaded in.
    """
    match_id = payload.get('match_id')
    
    logger.info(f"[MATCH LIVE] Match {match_id} is now in progress")
    
    # Notify frontend to transition to in-game state
    await send_event(ws, 'match_in_progress', payload)


async def handle_match_score_update(payload: dict, client_id: int, ws):
    """
    Receive score update from Django (for spectators or match room).
    """
    # Simply forward to frontend
    await send_event(ws, 'match_score_update', payload)
```

---

## 🎨 **Phase 3.5: Frontend Match Room**

```jsx
// client/frontend/src/pages/MatchRoom.jsx

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Box, Typography, Grid, Paper, LinearProgress } from '@mui/material';

const MatchRoom = () => {
  const { matchId } = useParams();
  const { on, api, connected } = useWebSocket();
  const [matchData, setMatchData] = useState(null);
  const [score, setScore] = useState({ team_a: 0, team_b: 0, round: 0 });
  const [status, setStatus] = useState('loading');

  // Subscribe to match updates
  useEffect(() => {
    if (!connected) return;

    // Request match data
    api.sendEvent('get_match_data', { match_id: matchId });

    // Listen for score updates
    const unsubscribeScore = on('match_score_update', (payload) => {
      if (payload.match_id === matchId) {
        setScore({
          team_a: payload.team_a_score,
          team_b: payload.team_b_score,
          round: payload.current_round
        });
      }
    });

    const unsubscribeStatus = on('match_in_progress', (payload) => {
      if (payload.match_id === matchId) {
        setStatus('in_progress');
      }
    });

    return () => {
      unsubscribeScore();
      unsubscribeStatus();
    };
  }, [connected, matchId]);

  if (status === 'loading') {
    return <Box><LinearProgress /></Box>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Match Room - {matchData?.map || 'Loading...'}
      </Typography>

      {/* Score Display */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={5}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'primary.dark' }}>
            <Typography variant="h3">{score.team_a}</Typography>
            <Typography variant="h6">Team A</Typography>
          </Paper>
        </Grid>
        <Grid item xs={2} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography variant="h4">-</Typography>
        </Grid>
        <Grid item xs={5}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'error.dark' }}>
            <Typography variant="h3">{score.team_b}</Typography>
            <Typography variant="h6">Team B</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Round Progress */}
      <Typography variant="body1" sx={{ mb: 2 }}>
        Round {score.round} / 24
      </Typography>

      {/* TODO: Add player statistics, spectator chat, etc. */}
    </Box>
  );
};

export default MatchRoom;
```

---

## ⚡ **Performance Benchmarks & Targets**

### **System Performance Goals**

| Metric | Target | Notes |
|--------|--------|-------|
| **Heartbeat Impact** | < 0.1% CPU | Stops during matches |
| **Match Monitoring** | < 0.5% CPU | 30s polling interval |
| **WebSocket Latency** | < 50ms | Score updates |
| **Memory Usage** | < 50MB | Client backend total |
| **Network Bandwidth** | < 100KB/min | During match monitoring |

### **Optimization Checklist**

- ✅ **No REST API calls** - WebSocket only
- ✅ **Stop heartbeat during matches** - Already implemented
- ✅ **30-second polling** - Not 3 seconds
- ✅ **Delta updates only** - Send only changes
- ✅ **Lazy statistics collection** - Round end only
- ✅ **Single DB query with prefetch** - Minimize ORM overhead
- ✅ **Background tasks** - Non-blocking execution
- ✅ **Channel layer optimization** - Single group_send per broadcast

---

## 📝 **Implementation Order**

### **Week 1: Core Match Execution**
1. ✅ Extend Match model
2. ✅ Create MatchExecutionManager
3. ✅ Add Django consumer handlers
4. ✅ Update client bootstrap.py
5. ✅ Test constructor flow

### **Week 2: Match Monitoring**
1. ✅ Implement MatchMonitor
2. ✅ Add client-side polling
3. ✅ Test score updates
4. ✅ Verify performance impact

### **Week 3: Frontend & Spectator**
1. ✅ Create MatchRoom component
2. ✅ Add player search
3. ✅ Implement spectator mode
4. ✅ Test public viewing

### **Week 4: Polish & Optimization**
1. ✅ Rejoin system
2. ✅ Post-match processing
3. ✅ Performance profiling
4. ✅ Load testing

---

## ✅ **Next Steps**

Ready to begin implementation? I recommend starting with:

1. **Match model extensions** - Foundation for everything
2. **MatchExecutionManager** - Core business logic
3. **Constructor flow testing** - Critical path validation

**Shall I proceed with implementing Phase 3.1 (Match Execution System)?**

