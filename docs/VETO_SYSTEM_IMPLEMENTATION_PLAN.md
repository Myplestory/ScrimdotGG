# Veto System Implementation Plan

## Current System Analysis

### Backend Architecture (Already Implemented)
- **MatchManager.process_veto()**: Handles map veto logic with captain validation
- **VetoAction Model**: Records all veto actions with sequence numbers
- **Match States**: VETO_PHASE → SIDE_SELECTION → READY
- **Timeout Handling**: Celery task handles veto timeouts (30 seconds per veto)
- **WebSocket Events**: `veto_map`, `map_vetoed`, `veto_complete`, `veto_timeout`

### Frontend Architecture (Partially Implemented)
- **MapVetoSection Component**: Basic UI with timer and map list
- **Timer Display**: Shows countdown for current veto turn
- **Mock Data**: Currently using static data for preview

## Implementation Tasks

### 1. Frontend Veto Handler Implementation

#### A. WebSocket Event Handlers
```javascript
// In MatchPage.jsx - Add these event handlers
const handleVetoEvents = () => {
  // Listen for veto state updates
  on('map_vetoed', (data) => {
    setMatchData(prev => ({
      ...prev,
      vetoed_maps: [...prev.vetoed_maps, data.map_name],
      veto_turn: data.next_turn,
      veto_sequence: data.sequence_number
    }));
    setTimeLeft(30); // Reset timer for next turn
  });

  // Listen for veto completion
  on('veto_complete', (data) => {
    setMatchData(prev => ({
      ...prev,
      state: 'side_selection',
      final_map: data.final_map,
      side_selector: data.side_selector
    }));
  });

  // Listen for veto timeout
  on('veto_timeout', (data) => {
    setMatchData(prev => ({
      ...prev,
      vetoed_maps: [...prev.vetoed_maps, data.auto_vetoed_map],
      veto_turn: data.next_turn
    }));
  });
};
```

#### B. Veto Action Handler
```javascript
// In MatchPage.jsx - Add veto map function
const handleVetoMap = (mapName) => {
  if (!isCaptain || currentTurn !== myTeam) {
    return; // Only captain can veto on their turn
  }

  sendEvent('veto_map', {
    match_id: matchId,
    map_name: mapName,
    team: myTeam
  });
};
```

#### C. Enhanced MapVetoSection Component
```javascript
// Update MapVetoSection to handle real veto actions
const MapVetoSection = ({ 
  maps, 
  vetoedMaps, 
  currentTurn, 
  timeLeft, 
  onMapVeto, 
  isCaptain, 
  myTeam,
  vetoSequence 
}) => {
  const isMyTurn = currentTurn === myTeam && isCaptain;
  
  return (
    <Box sx={{ width: '180px', textAlign: 'center' }}>
      {/* Enhanced Timer with Pulse Animation */}
      <Box sx={{ 
        mb: 2,
        animation: timeLeft <= 10 ? 'pulse 1s infinite' : 'none'
      }}>
        <Typography variant="body1" sx={{ 
          color: colors.seance[300], 
          fontWeight: 600, 
          mb: 1 
        }}>
          {currentTurn ? `${currentTurn.replace('_', ' ').toUpperCase()}` : 'VETO PHASE'}
        </Typography>
        <Typography variant="body2" sx={{ 
          color: colors.grey[300], 
          mb: 1 
        }}>
          {`Ban ${Math.floor(vetoSequence / 2) + 1} of ${Math.floor(maps.length / 2)}`}
        </Typography>
        <Box sx={{ 
          display: 'inline-flex', 
          alignItems: 'center', 
          gap: 0.5,
          bgcolor: timeLeft <= 10 ? colors.redAccent[500] : colors.primary[500],
          px: 1.5,
          py: 0.25,
          borderRadius: '12px',
          border: `1px solid ${timeLeft <= 10 ? colors.redAccent[400] : colors.seance[400]}`
        }}>
          <TimerIcon sx={{ 
            color: timeLeft <= 10 ? colors.grey[100] : colors.seance[300], 
            fontSize: 14 
          }} />
          <Typography variant="body2" sx={{ 
            color: colors.grey[100], 
            fontWeight: 600, 
            fontSize: '0.8rem' 
          }}>
            {formatTime(timeLeft)}
          </Typography>
        </Box>
      </Box>

      {/* Interactive Map List */}
      <Stack spacing={0.5}>
        {maps.map((map, index) => {
          const isVetoed = vetoedMaps.includes(map);
          const canVeto = isMyTurn && !isVetoed;
          
          return (
            <Card
              key={map}
              onClick={() => canVeto && onMapVeto(map)}
              sx={{
                position: 'relative',
                borderRadius: '6px',
                overflow: 'hidden',
                cursor: canVeto ? 'pointer' : 'default',
                opacity: isVetoed ? 0.4 : 1,
                bgcolor: isVetoed ? colors.grey[800] : colors.primary[600],
                border: canVeto ? `2px solid ${colors.seance[400]}` : '1px solid transparent',
                transition: 'all 0.2s ease',
                '&:hover': canVeto ? {
                  transform: 'scale(1.02)',
                  bgcolor: colors.seance[500],
                  boxShadow: `0 0 12px ${colors.seance[400]}60`
                } : {}
              }}
            >
              <CardContent sx={{ p: 0.75 }}>
                <Typography variant="body2" sx={{ 
                  color: isVetoed ? colors.grey[500] : colors.grey[100],
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  textAlign: 'center',
                  textDecoration: isVetoed ? 'line-through' : 'none'
                }}>
                  {map}
                </Typography>
                {isVetoed && (
                  <Box sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'rgba(0,0,0,0.7)'
                  }}>
                    <Typography variant="caption" sx={{ 
                      color: colors.redAccent[400],
                      fontWeight: 700,
                      fontSize: '0.6rem'
                    }}>
                      BANNED
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          );
        })}
      </Stack>
    </Box>
  );
};
```

### 2. Snake Draft System Implementation

#### A. Veto Sequence Logic
```javascript
// In MatchPage.jsx - Add veto sequence tracking
const getVetoSequence = (vetoCount, totalMaps) => {
  // Standard BO1 snake draft: A-B-A-B-A-B (6 bans, 1 remaining)
  // For 7 maps: Team A bans, Team B bans, Team A bans, Team B bans, Team A bans, Team B bans
  const sequences = {
    7: ['team_a', 'team_b', 'team_a', 'team_b', 'team_a', 'team_b'], // 6 bans, 1 final
    5: ['team_a', 'team_b', 'team_a', 'team_b'], // 4 bans, 1 final
    3: ['team_a', 'team_b'] // 2 bans, 1 final
  };
  
  const sequence = sequences[totalMaps] || sequences[7];
  return sequence[vetoCount] || null;
};

const getVetoPhaseInfo = (vetoCount, totalMaps) => {
  const totalBans = totalMaps - 1;
  const currentBan = vetoCount + 1;
  
  return {
    currentBan,
    totalBans,
    isLastBan: currentBan === totalBans,
    progress: (currentBan / totalBans) * 100
  };
};
```

#### B. Enhanced Veto Progress Display
```javascript
// Add to MapVetoSection - Veto progress bar
<Box sx={{ mb: 2 }}>
  <Typography variant="caption" sx={{ 
    color: colors.grey[400], 
    display: 'block', 
    mb: 0.5 
  }}>
    Ban {vetoPhaseInfo.currentBan} of {vetoPhaseInfo.totalBans}
  </Typography>
  <Box sx={{ 
    width: '100%', 
    height: 4, 
    bgcolor: colors.grey[700], 
    borderRadius: 1,
    overflow: 'hidden'
  }}>
    <Box sx={{
      width: `${vetoPhaseInfo.progress}%`,
      height: '100%',
      bgcolor: colors.seance[400],
      transition: 'width 0.3s ease'
    }} />
  </Box>
</Box>
```

### 3. Side Selection Phase Implementation

#### A. Side Selection UI Component
```javascript
// New component for side selection phase
const SideSelectionSection = ({ 
  sideSelector, 
  timeLeft, 
  onSideSelect, 
  isCaptain, 
  myTeam 
}) => {
  const canSelect = sideSelector === myTeam && isCaptain;
  
  return (
    <Box sx={{ width: '200px', textAlign: 'center' }}>
      <Typography variant="h6" sx={{ 
        color: colors.seance[300], 
        fontWeight: 600, 
        mb: 2 
      }}>
        {sideSelector.replace('_', ' ').toUpperCase()} CHOOSES SIDE
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button
          variant={canSelect ? "contained" : "outlined"}
          disabled={!canSelect}
          onClick={() => onSideSelect('attack')}
          sx={{
            bgcolor: canSelect ? colors.seance[500] : 'transparent',
            color: colors.grey[100],
            '&:hover': {
              bgcolor: colors.seance[400]
            }
          }}
        >
          Attack First
        </Button>
        <Button
          variant={canSelect ? "contained" : "outlined"}
          disabled={!canSelect}
          onClick={() => onSideSelect('defense')}
          sx={{
            bgcolor: canSelect ? colors.seance[500] : 'transparent',
            color: colors.grey[100],
            '&:hover': {
              bgcolor: colors.seance[400]
            }
          }}
        >
          Defend First
        </Button>
      </Box>
    </Box>
  );
};
```

### 4. Backend Integration Points

#### A. WebSocket Event Routing (Already Implemented)
- `handle_veto_map()` in consumers.py ✅
- `MatchManager.process_veto()` ✅ 
- Timeout handling via Celery tasks ✅

#### B. Required Frontend WebSocket Events
- **Outgoing**: `veto_map`, `select_side`, `get_match_data`
- **Incoming**: `map_vetoed`, `veto_complete`, `veto_timeout`, `side_selected`, `match_data`

### 5. Testing Strategy

#### A. Unit Tests
- [ ] Veto sequence validation
- [ ] Captain permission checks
- [ ] Timeout handling
- [ ] Snake draft logic

#### B. Integration Tests
- [ ] Full veto flow (7 maps → 1 final)
- [ ] Side selection after veto
- [ ] Timeout auto-veto
- [ ] Multiple concurrent matches

#### C. User Experience Tests
- [ ] Timer synchronization
- [ ] Visual feedback for veto actions
- [ ] Error handling for invalid actions
- [ ] Mobile responsiveness

### 6. Implementation Priority

1. **HIGH**: Complete veto event handlers in frontend ✅ (Timer already implemented)
2. **HIGH**: Implement interactive map veto functionality
3. **MEDIUM**: Add side selection phase UI
4. **MEDIUM**: Enhanced veto progress visualization
5. **LOW**: Advanced animations and sound effects

### 7. Technical Considerations

#### A. State Management
- Use React state for real-time veto updates
- Sync with backend via WebSocket events
- Handle reconnection scenarios

#### B. Error Handling
- Invalid veto attempts (not captain, not your turn)
- Network disconnections during veto
- Timeout edge cases

#### C. Performance
- Minimize re-renders during veto updates
- Efficient map list rendering
- Smooth timer animations

## Next Steps

1. **Implement interactive veto handlers** in MatchPage.jsx
2. **Test veto flow** with real backend connection
3. **Add side selection phase** UI component
4. **Enhance visual feedback** for better UX
5. **Add comprehensive error handling**

## Files to Modify

### Frontend
- `client/frontend/src/pages/MatchPage.jsx` - Add veto handlers and state management
- `client/frontend/src/components/SimpleRankGauge.jsx` - Already completed ✅

### Backend (Already Implemented)
- `server/matchmaking/consumers.py` - Veto event handlers ✅
- `server/matchmaking/match_manager.py` - Veto logic ✅
- `server/matchmaking/tasks.py` - Timeout handling ✅

The system architecture is already robust and well-implemented. The main task is connecting the frontend UI to the existing backend veto system through proper WebSocket event handling.
