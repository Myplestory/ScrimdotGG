import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { WebSocketContext } from '../contexts/WebSocketContext';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Button,
  LinearProgress,
  Chip,
  Card,
  CardContent,
  Divider,
  Alert
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import TimerIcon from '@mui/icons-material/Timer';

export default function MatchPage() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const { connected, sendEvent, on } = useContext(WebSocketContext);
  
  // Match state
  const [matchData, setMatchData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Veto state
  const [vetoPhase, setVetoPhase] = useState(false);
  const [currentTurn, setCurrentTurn] = useState(null);
  const [availableMaps, setAvailableMaps] = useState([]);
  const [vetoedMaps, setVetoedMaps] = useState([]);
  const [vetoHistory, setVetoHistory] = useState([]);
  const [vetoDeadline, setVetoDeadline] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  
  // Player info
  const [myTeam, setMyTeam] = useState(null);
  const [isCaptain, setIsCaptain] = useState(false);
  
  // Fetch match data on load
  useEffect(() => {
    if (!connected || !matchId) return;
    
    console.log('[MATCH PAGE] Fetching match data for:', matchId);
    sendEvent('get_match_data', { match_id: matchId });
  }, [connected, matchId]);
  
  // Handle match data response
  useEffect(() => {
    const handleMatchData = (data) => {
      console.log('[MATCH PAGE] Received match data:', data);
      setMatchData(data);
      setLoading(false);
      
      // Determine my team and captain status
      const myPuuid = localStorage.getItem('playerPuuid');
      const teamAPlayer = data.team_a_players?.find(p => p.puuid === myPuuid);
      const teamBPlayer = data.team_b_players?.find(p => p.puuid === myPuuid);
      
      if (teamAPlayer) {
        setMyTeam('team_a');
        setIsCaptain(data.team_a_captain === myPuuid);
      } else if (teamBPlayer) {
        setMyTeam('team_b');
        setIsCaptain(data.team_b_captain === myPuuid);
      }
      
      // Set veto state
      if (data.state === 'VETO') {
        setVetoPhase(true);
        setCurrentTurn(data.veto_turn);
        setAvailableMaps(data.remaining_maps || []);
        setVetoedMaps(data.vetoed_maps || []);
        setVetoHistory(data.veto_history || []);
        setVetoDeadline(data.veto_deadline);
      }
    };
    
    const unsubscribe = on('match_data', handleMatchData);
    return () => {
      if (typeof unsubscribe === 'function') unsubscribe();
    };
  }, [on]);
  
  // Handle veto events
  useEffect(() => {
    const handleVetoStarted = (data) => {
      console.log('[VETO] Veto started:', data);
      setVetoPhase(true);
      setCurrentTurn(data.current_turn);
      setAvailableMaps(data.available_maps);
      setVetoDeadline(data.deadline);
    };
    
    const handleMapVetoed = (data) => {
      console.log('[VETO] Map vetoed:', data);
      setVetoedMaps(prev => [...prev, data.map]);
      setAvailableMaps(data.remaining_maps);
      setCurrentTurn(data.next_turn);
      setVetoDeadline(data.deadline);
      
      // Add to history
      setVetoHistory(prev => [...prev, {
        map_name: data.map,
        team: data.vetoed_by,
        sequence_number: prev.length + 1
      }]);
    };
    
    const handleVetoTimeout = (data) => {
      console.log('[VETO] Veto timeout:', data);
      setVetoedMaps(prev => [...prev, data.auto_vetoed_map]);
      
      if (data.veto_complete) {
        setVetoPhase(false);
        if (matchData) {
          setMatchData(prev => ({
            ...prev,
            final_map: data.final_map,
            state: 'SIDE_SELECTION'
          }));
        }
      } else {
        setAvailableMaps(data.remaining_maps);
        setCurrentTurn(data.next_turn);
        setVetoDeadline(data.deadline);
      }
      
      // Add to history
      setVetoHistory(prev => [...prev, {
        map_name: data.auto_vetoed_map,
        team: currentTurn,
        was_timeout: true,
        sequence_number: prev.length + 1
      }]);
    };
    
    const handleVetoComplete = (data) => {
      console.log('[VETO] Veto complete:', data);
      setVetoPhase(false);
      
      if (matchData) {
        setMatchData(prev => ({
          ...prev,
          final_map: data.final_map,
          state: 'SIDE_SELECTION',
          side_selector: data.side_selector
        }));
      }
    };
    
    const unsubVetoStarted = on('veto_started', handleVetoStarted);
    const unsubMapVetoed = on('map_vetoed', handleMapVetoed);
    const unsubVetoTimeout = on('veto_timeout', handleVetoTimeout);
    const unsubVetoComplete = on('veto_complete', handleVetoComplete);
    
    return () => {
      if (typeof unsubVetoStarted === 'function') unsubVetoStarted();
      if (typeof unsubMapVetoed === 'function') unsubMapVetoed();
      if (typeof unsubVetoTimeout === 'function') unsubVetoTimeout();
      if (typeof unsubVetoComplete === 'function') unsubVetoComplete();
    };
  }, [on, matchData, currentTurn]);
  
  // Countdown timer
  useEffect(() => {
    if (!vetoDeadline) {
      setTimeLeft(null);
      return;
    }
    
    const updateTimer = () => {
      const deadline = new Date(vetoDeadline);
      const now = new Date();
      const diff = Math.max(0, Math.floor((deadline - now) / 1000));
      setTimeLeft(diff);
      
      if (diff === 0) {
        // Timer expired
        setTimeLeft(0);
      }
    };
    
    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    
    return () => clearInterval(interval);
  }, [vetoDeadline]);
  
  // Handle veto action
  const handleVetoMap = (mapName) => {
    if (!isCaptain) {
      console.warn('[VETO] Only captain can veto');
      return;
    }
    
    if (currentTurn !== myTeam) {
      console.warn('[VETO] Not your turn');
      return;
    }
    
    console.log('[VETO] Vetoing map:', mapName);
    sendEvent('veto_map', {
      match_id: matchId,
      map: mapName
    });
  };
  
  // Render loading state
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Loading Match...
          </Typography>
          <LinearProgress sx={{ mt: 2 }} />
        </Paper>
      </Container>
    );
  }
  
  // Render error state
  if (error || !matchData) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h5" color="error" gutterBottom>
            Match Not Found
          </Typography>
          <Typography variant="body1" sx={{ mt: 2 }}>
            {error || 'Unable to load match data'}
          </Typography>
          <Button 
            variant="contained" 
            sx={{ mt: 3 }}
            onClick={() => navigate('/queue')}
          >
            Return to Queue
          </Button>
        </Paper>
      </Container>
    );
  }
  
  return (
    <Container maxWidth="xl" sx={{ mt: 3, mb: 4 }}>
      {/* Match Header */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: '#1a1a2e' }}>
        <Grid container alignItems="center" justifyContent="space-between">
          <Grid item>
            <Typography variant="h4" sx={{ color: '#fff', fontWeight: 'bold' }}>
              Match {matchId.substring(0, 8)}
            </Typography>
            <Typography variant="body2" sx={{ color: '#aaa', mt: 0.5 }}>
              Match Quality: {(matchData.match_quality * 100).toFixed(1)}%
            </Typography>
          </Grid>
          <Grid item>
            <Chip 
              label={matchData.state.replace('_', ' ')}
              color={matchData.state === 'VETO' ? 'warning' : 'info'}
              sx={{ fontSize: '1rem', px: 2, py: 2.5 }}
            />
          </Grid>
        </Grid>
      </Paper>
      
      {/* Teams Display */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Team A */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, bgcolor: '#1e3a5f' }}>
            <Typography variant="h6" sx={{ color: '#4fc3f7', mb: 2, fontWeight: 'bold' }}>
              Team A {myTeam === 'team_a' && '(Your Team)'}
            </Typography>
            <Typography variant="body2" sx={{ color: '#aaa', mb: 2 }}>
              Avg MMR: {matchData.team_a_avg_mmr.toFixed(0)}
            </Typography>
            {matchData.team_a_players.map(player => (
              <Box
                key={player.puuid}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 1.5,
                  mb: 1,
                  bgcolor: player.puuid === matchData.team_a_captain ? '#2d4a6f' : '#1a2940',
                  borderRadius: 1,
                  border: player.puuid === localStorage.getItem('playerPuuid') ? '2px solid #4fc3f7' : 'none'
                }}
              >
                <Box>
                  <Typography variant="body1" sx={{ color: '#fff' }}>
                    {player.alias}
                    {player.puuid === matchData.team_a_captain && ' ⭐'}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#aaa' }}>
                    MMR: {player.mmr.toFixed(0)} • ELO: {player.elo}
                  </Typography>
                </Box>
                {player.is_ready && <CheckCircleIcon sx={{ color: '#4caf50' }} />}
              </Box>
            ))}
          </Paper>
        </Grid>
        
        {/* Team B */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, bgcolor: '#5f1e1e' }}>
            <Typography variant="h6" sx={{ color: '#f44336', mb: 2, fontWeight: 'bold' }}>
              Team B {myTeam === 'team_b' && '(Your Team)'}
            </Typography>
            <Typography variant="body2" sx={{ color: '#aaa', mb: 2 }}>
              Avg MMR: {matchData.team_b_avg_mmr.toFixed(0)}
            </Typography>
            {matchData.team_b_players.map(player => (
              <Box
                key={player.puuid}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 1.5,
                  mb: 1,
                  bgcolor: player.puuid === matchData.team_b_captain ? '#6f2d2d' : '#402020',
                  borderRadius: 1,
                  border: player.puuid === localStorage.getItem('playerPuuid') ? '2px solid #f44336' : 'none'
                }}
              >
                <Box>
                  <Typography variant="body1" sx={{ color: '#fff' }}>
                    {player.alias}
                    {player.puuid === matchData.team_b_captain && ' ⭐'}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#aaa' }}>
                    MMR: {player.mmr.toFixed(0)} • ELO: {player.elo}
                  </Typography>
                </Box>
                {player.is_ready && <CheckCircleIcon sx={{ color: '#4caf50' }} />}
              </Box>
            ))}
          </Paper>
        </Grid>
      </Grid>
      
      {/* Veto Phase */}
      {vetoPhase && (
        <Paper sx={{ p: 3, mb: 3, bgcolor: '#2a2a3e' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5" sx={{ color: '#fff', fontWeight: 'bold' }}>
              Map Veto Phase
            </Typography>
            {timeLeft !== null && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TimerIcon sx={{ color: timeLeft <= 10 ? '#f44336' : '#fff' }} />
                <Typography 
                  variant="h6" 
                  sx={{ 
                    color: timeLeft <= 10 ? '#f44336' : '#fff',
                    fontWeight: 'bold'
                  }}
                >
                  {timeLeft}s
                </Typography>
              </Box>
            )}
          </Box>
          
          <Alert 
            severity={currentTurn === myTeam ? 'info' : 'warning'}
            sx={{ mb: 3 }}
          >
            {currentTurn === myTeam ? (
              isCaptain ? (
                <strong>It's your turn to veto a map!</strong>
              ) : (
                <strong>Waiting for your captain to veto...</strong>
              )
            ) : (
              <strong>Opponent's turn to veto</strong>
            )}
          </Alert>
          
          {/* Available Maps */}
          <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
            Available Maps ({availableMaps.length} remaining)
          </Typography>
          <Grid container spacing={2}>
            {availableMaps.map(mapName => (
              <Grid item xs={6} sm={4} md={3} key={mapName}>
                <Card
                  sx={{
                    bgcolor: '#1a1a2e',
                    border: '2px solid #4fc3f7',
                    cursor: (isCaptain && currentTurn === myTeam) ? 'pointer' : 'default',
                    transition: 'all 0.3s',
                    '&:hover': (isCaptain && currentTurn === myTeam) ? {
                      bgcolor: '#252538',
                      transform: 'scale(1.05)',
                      borderColor: '#ff4655'
                    } : {}
                  }}
                  onClick={() => {
                    if (isCaptain && currentTurn === myTeam) {
                      handleVetoMap(mapName);
                    }
                  }}
                >
                  <CardContent>
                    <Typography 
                      variant="h6" 
                      align="center" 
                      sx={{ color: '#fff', fontWeight: 'bold' }}
                    >
                      {mapName}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          
          {/* Veto History */}
          {vetoHistory.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                Veto History
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {vetoHistory.map((veto, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      p: 1.5,
                      bgcolor: veto.team === 'team_a' ? '#1e3a5f' : '#5f1e1e',
                      borderRadius: 1
                    }}
                  >
                    <Chip
                      label={`#${veto.sequence_number}`}
                      size="small"
                      sx={{ bgcolor: '#333', color: '#fff' }}
                    />
                    <Typography sx={{ color: '#fff' }}>
                      <strong>{veto.team === 'team_a' ? 'Team A' : 'Team B'}</strong> banned
                    </Typography>
                    <Chip
                      label={veto.map_name}
                      sx={{ bgcolor: '#ff4655', color: '#fff', fontWeight: 'bold' }}
                    />
                    {veto.was_timeout && (
                      <Chip label="TIMEOUT" size="small" color="warning" />
                    )}
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </Paper>
      )}
      
      {/* Final Map Selected */}
      {matchData.final_map && !vetoPhase && (
        <Paper sx={{ p: 4, mb: 3, bgcolor: '#1a1a2e', textAlign: 'center' }}>
          <Typography variant="h4" sx={{ color: '#4fc3f7', mb: 2, fontWeight: 'bold' }}>
            Map Selected
          </Typography>
          <Typography variant="h3" sx={{ color: '#fff', fontWeight: 'bold' }}>
            {matchData.final_map}
          </Typography>
          {matchData.state === 'SIDE_SELECTION' && (
            <Typography variant="body1" sx={{ color: '#aaa', mt: 2 }}>
              Waiting for side selection...
            </Typography>
          )}
        </Paper>
      )}
      
      {/* Connection Status */}
      {!connected && (
        <Alert severity="error" sx={{ mb: 3 }}>
          WebSocket disconnected. Reconnecting...
        </Alert>
      )}
    </Container>
  );
}

