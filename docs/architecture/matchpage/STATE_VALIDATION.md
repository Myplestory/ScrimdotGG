# Match State Validation

## Overview
Implement a validation system to prevent players/parties from queuing when they are already in an active match or match confirmation phase.

## Current System Analysis

### Backend Match States (from match_manager.py)
```python
# Match states that should block queuing
ACTIVE_MATCH_STATES = [
    'confirmation_phase',    # Players accepting/declining match
    'veto_phase',           # Map veto in progress
    'side_selection',       # Side selection after veto
    'ready',               # Match ready, waiting for game creation
    'in_progress',         # Match currently being played
    'paused'               # Match paused but still active
]

# States that allow queuing
INACTIVE_MATCH_STATES = [
    'completed',           # Match finished
    'cancelled',           # Match was cancelled
    'expired'              # Match confirmation expired
]
```

### Current Queue Entry Points
1. **PugQueue.jsx** - `handleFindMatch()` function
2. **Lobby component** - Party queue functionality
3. **Backend** - `QueueManager.add_lobby_to_queue()`

## Implementation Strategy

### 1. Backend Validation Layer

#### A. Create Match State Checker Service
```python
# server/matchmaking/match_state_validator.py

class MatchStateValidator:
    """
    Service to validate if players can queue based on their current match state
    """
    
    @staticmethod
    def can_player_queue(player_puuid: str) -> Dict:
        """
        Check if a player can queue based on their current match state
        
        Returns:
        {
            'can_queue': bool,
            'reason': str,  # If can_queue is False
            'match_id': str,  # Current active match if any
            'match_state': str  # Current match state
        }
        """
        
    @staticmethod
    def can_lobby_queue(lobby_id: int) -> Dict:
        """
        Check if all players in a lobby can queue
        
        Returns:
        {
            'can_queue': bool,
            'blocked_players': List[str],  # PUUIDs of blocked players
            'reasons': Dict[str, str],     # Reasons per blocked player
            'active_matches': Dict[str, str]  # Player -> Match ID mapping
        }
        """
        
    @staticmethod
    def get_player_active_match(player_puuid: str) -> Optional[Match]:
        """Get the active match for a player, if any"""
        
    @staticmethod
    def get_active_match_states() -> List[str]:
        """Get list of match states that block queuing"""
```

#### B. Database Queries for Match State
```python
# Efficient queries to check player match status

def get_player_active_matches(player_puuid: str):
    """
    Query to find active matches for a player
    """
    return Match.objects.filter(
        Q(team_a_players__contains=[{'puuid': player_puuid}]) |
        Q(team_b_players__contains=[{'puuid': player_puuid}]),
        state__in=ACTIVE_MATCH_STATES
    ).select_related().first()

def get_lobby_players_active_matches(player_puuids: List[str]):
    """
    Batch query to check multiple players at once
    """
    return Match.objects.filter(
        Q(team_a_players__overlap=player_puuids) |
        Q(team_b_players__overlap=player_puuids),
        state__in=ACTIVE_MATCH_STATES
    ).values('id', 'state', 'team_a_players', 'team_b_players')
```

#### C. Integration with Queue Manager
```python
# server/matchmaking/queue_manager.py

class QueueManager:
    @staticmethod
    async def add_lobby_to_queue_with_validation(lobby_id: int) -> Dict:
        """
        Enhanced queue addition with match state validation
        """
        # 1. Get lobby and players
        lobby = await sync_to_async(Lobby.objects.get)(id=lobby_id)
        player_puuids = [p.puuid for p in lobby.players.all()]
        
        # 2. Validate all players can queue
        validation_result = MatchStateValidator.can_lobby_queue(lobby_id)
        
        if not validation_result['can_queue']:
            return {
                'status': 'error',
                'message': 'Some players are already in an active match',
                'blocked_players': validation_result['blocked_players'],
                'reasons': validation_result['reasons']
            }
        
        # 3. Proceed with normal queue logic
        return await QueueManager.add_lobby_to_queue(lobby_id)
```

### 2. WebSocket Consumer Integration

#### A. Enhanced Queue Event Handler
```python
# server/matchmaking/consumers.py

async def handle_find_match(self, data):
    """Enhanced find match handler with validation"""
    try:
        lobby_id = data.get('lobby_id')
        
        # Validate before queuing
        validation_result = await sync_to_async(
            MatchStateValidator.can_lobby_queue
        )(lobby_id)
        
        if not validation_result['can_queue']:
            await self.send(text_data=json.dumps({
                'event': 'queue_blocked',
                'data': {
                    'message': 'Cannot queue: players in active match',
                    'blocked_players': validation_result['blocked_players'],
                    'reasons': validation_result['reasons'],
                    'active_matches': validation_result['active_matches']
                }
            }))
            return
        
        # Proceed with normal queue logic
        result = await QueueManager.add_lobby_to_queue_with_validation(lobby_id)
        
        if result['status'] == 'success':
            await self.send(text_data=json.dumps({
                'event': 'queue_joined',
                'data': result
            }))
        else:
            await self.send(text_data=json.dumps({
                'event': 'queue_error',
                'data': result
            }))
            
    except Exception as e:
        logger.error(f"Error in find_match: {str(e)}")
        await self.send(text_data=json.dumps({
            'event': 'queue_error',
            'data': {'message': f'Failed to join queue: {str(e)}'}
        }))
```

#### B. Real-time Match State Updates
```python
# Broadcast match state changes to affect queue eligibility

async def broadcast_match_state_change(match_id: str, new_state: str):
    """
    Notify all players when match state changes
    This helps update queue button states in real-time
    """
    match = await sync_to_async(Match.objects.get)(id=match_id)
    all_players = match.get_all_player_puuids()
    
    for player_puuid in all_players:
        await channel_layer.group_send(
            f"player_{player_puuid}",
            {
                'type': 'match_state_changed',
                'match_id': match_id,
                'state': new_state,
                'can_queue': new_state in INACTIVE_MATCH_STATES
            }
        )
```

### 3. Frontend Implementation

#### A. Enhanced WebSocket Context
```javascript
// client/frontend/src/contexts/WebSocketContext.jsx

const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const [playerMatchState, setPlayerMatchState] = useState({
    inActiveMatch: false,
    matchId: null,
    matchState: null,
    canQueue: true
  });

  useEffect(() => {
    // Listen for match state changes
    const handleMatchStateChanged = (data) => {
      setPlayerMatchState({
        inActiveMatch: !data.can_queue,
        matchId: data.match_id,
        matchState: data.state,
        canQueue: data.can_queue
      });
    };

    // Listen for queue blocked events
    const handleQueueBlocked = (data) => {
      setPlayerMatchState(prev => ({
        ...prev,
        canQueue: false
      }));
      
      // Show notification to user
      showNotification({
        type: 'error',
        title: 'Cannot Queue',
        message: data.message,
        details: data.reasons
      });
    };

    on('match_state_changed', handleMatchStateChanged);
    on('queue_blocked', handleQueueBlocked);

    return () => {
      off('match_state_changed', handleMatchStateChanged);
      off('queue_blocked', handleQueueBlocked);
    };
  }, [on, off]);

  return (
    <WebSocketContext.Provider value={{
      // ... existing context values
      playerMatchState,
      canQueue: playerMatchState.canQueue
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};
```

#### B. Enhanced PugQueue Component
```javascript
// client/frontend/src/pages/PugQueue.jsx

const PugQueue = () => {
  const { sendEvent, on, off, canQueue, playerMatchState } = useContext(WebSocketContext);
  const [queueBlocked, setQueueBlocked] = useState(false);
  const [blockReason, setBlockReason] = useState('');

  // Check queue eligibility on component mount
  useEffect(() => {
    sendEvent('check_queue_eligibility', {});
  }, []);

  // Listen for queue eligibility updates
  useEffect(() => {
    const handleQueueEligibility = (data) => {
      setQueueBlocked(!data.can_queue);
      setBlockReason(data.reason || '');
    };

    on('queue_eligibility', handleQueueEligibility);
    return () => off('queue_eligibility', handleQueueEligibility);
  }, [on, off]);

  const handleFindMatch = async () => {
    // Pre-flight check
    if (!canQueue || queueBlocked) {
      showNotification({
        type: 'warning',
        title: 'Cannot Queue',
        message: blockReason || 'You are currently in an active match'
      });
      return;
    }

    // Proceed with queue logic
    sendEvent('find_match', {
      lobby_id: currentLobby?.id,
      preferences: queuePreferences
    });
  };

  return (
    <Container>
      {/* Queue Status Indicator */}
      {playerMatchState.inActiveMatch && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <AlertTitle>Active Match Detected</AlertTitle>
          You are currently in match {playerMatchState.matchId} ({playerMatchState.matchState}).
          <Button 
            variant="outlined" 
            size="small" 
            onClick={() => navigate(`/match/${playerMatchState.matchId}`)}
            sx={{ ml: 2 }}
          >
            Return to Match
          </Button>
        </Alert>
      )}

      {/* Enhanced Find Match Button */}
      <Button
        variant="contained"
        size="large"
        onClick={handleFindMatch}
        disabled={!canQueue || queueBlocked || isQueued}
        sx={{
          bgcolor: canQueue && !queueBlocked ? colors.seance[500] : colors.grey[600],
          '&:hover': {
            bgcolor: canQueue && !queueBlocked ? colors.seance[400] : colors.grey[600]
          }
        }}
      >
        {queueBlocked ? 'In Active Match' : 
         isQueued ? 'Finding Match...' : 
         'Find Match'}
      </Button>

      {/* Block Reason Display */}
      {queueBlocked && blockReason && (
        <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
          {blockReason}
        </Typography>
      )}
    </Container>
  );
};
```

#### C. Lobby Component Enhancement
```javascript
// Similar validation for party/lobby queuing
const Lobby = () => {
  const { canQueue, playerMatchState } = useContext(WebSocketContext);
  
  const handlePartyQueue = () => {
    if (!canQueue) {
      showNotification({
        type: 'error',
        title: 'Cannot Queue Party',
        message: 'One or more party members are in an active match'
      });
      return;
    }
    
    // Proceed with party queue
    sendEvent('party_find_match', {
      lobby_id: lobbyId,
      party_preferences: preferences
    });
  };

  return (
    // ... lobby UI with enhanced queue button
  );
};
```

### 4. Database Optimizations

#### A. Add Database Indexes
```sql
-- Optimize match state queries
CREATE INDEX idx_match_state_players ON matches USING GIN (team_a_players, team_b_players);
CREATE INDEX idx_match_state ON matches (state);
CREATE INDEX idx_match_active_lookup ON matches (state, created_at) WHERE state IN ('confirmation_phase', 'veto_phase', 'side_selection', 'ready', 'in_progress', 'paused');
```

#### B. Redis Caching Layer
```python
# Cache active match states for faster lookups
class MatchStateCache:
    @staticmethod
    def cache_player_match_state(player_puuid: str, match_id: str, state: str):
        """Cache player's current match state"""
        redis_key = f"player_match_state:{player_puuid}"
        redis_client.setex(redis_key, 3600, json.dumps({
            'match_id': match_id,
            'state': state,
            'can_queue': state in INACTIVE_MATCH_STATES
        }))
    
    @staticmethod
    def get_player_match_state(player_puuid: str) -> Optional[Dict]:
        """Get cached player match state"""
        redis_key = f"player_match_state:{player_puuid}"
        cached = redis_client.get(redis_key)
        return json.loads(cached) if cached else None
```

### 5. Error Handling & User Experience

#### A. Notification System
```javascript
// Enhanced notification for different scenarios
const showQueueBlockedNotification = (data) => {
  const notifications = {
    'in_veto': 'You are currently in the map veto phase',
    'in_match': 'You are currently playing a match',
    'confirming': 'You have a pending match confirmation',
    'party_member_blocked': 'A party member is in an active match'
  };
  
  showNotification({
    type: 'warning',
    title: 'Cannot Queue',
    message: notifications[data.reason] || data.message,
    action: data.match_id ? {
      label: 'Go to Match',
      onClick: () => navigate(`/match/${data.match_id}`)
    } : null
  });
};
```

#### B. Graceful Degradation
```javascript
// Fallback behavior when validation fails
const handleValidationError = (error) => {
  console.warn('Queue validation failed:', error);
  
  // Still allow queue attempt but warn user
  showNotification({
    type: 'info',
    title: 'Validation Warning',
    message: 'Unable to verify match status. Proceeding with caution.'
  });
  
  // Proceed with queue but with additional server-side validation
  return true;
};
```

## Notes
Planning, prioritization, and timelines are tracked in `docs/implementation/`.

## Testing Strategy

### Unit Tests
- `MatchStateValidator` logic for all match states
- Database queries for player match lookup
- Edge cases (player in multiple matches, state transitions)

### Integration Tests
- Full queue flow with validation
- WebSocket event handling
- Frontend button state management

### User Experience Tests
- Clear error messages for blocked queue attempts
- Smooth navigation back to active matches
- Party/lobby validation with mixed player states

## Security Considerations

1. **Server-side Validation**: Never trust frontend-only validation
2. **Race Conditions**: Handle concurrent queue attempts
3. **State Consistency**: Ensure match state updates are atomic
4. **Performance**: Efficient queries to avoid DoS via repeated validation calls

This implementation ensures players cannot accidentally queue while in active matches, provides clear feedback about why queuing is blocked, and offers easy navigation back to their current match.
