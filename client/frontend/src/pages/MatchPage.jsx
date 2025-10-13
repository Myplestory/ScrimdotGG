import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { WebSocketContext } from '../contexts/WebSocketContext';
import { useTheme } from '@mui/material/styles';
import { tokens } from '../theme';
import { useMode } from '../theme';
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
  Alert,
  Avatar,
  Stack,
  IconButton,
  Tooltip
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import TimerIcon from '@mui/icons-material/Timer';
import PersonIcon from '@mui/icons-material/Person';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import SportsEsportsIcon from '@mui/icons-material/SportsEsports';
import SimpleRankGauge from '../components/SimpleRankGauge';

// Compact Player Card Component
const PlayerCard = ({ player, isCurrentUser, theme, colors, isLeftTeam = false }) => {
  // Mock recent games data (simplified)
  const recentGames = {
    totalMatches: Math.floor(Math.random() * 500) + 100, // 100-600 total matches
    winRate: Math.floor(Math.random() * 30) + 40, // 40-70% win rate
    avgKD: (Math.random() * 1.5 + 0.5).toFixed(2), // 0.5-2.0 K/D
  };

  const cardContent = (
    <>
      {/* For left team: Rank first, then content, then avatar */}
      {isLeftTeam ? (
        <>
          {/* Rank Gauge - Left side inner */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ 
              color: colors.grey[300], 
              fontWeight: 600,
              minWidth: '40px',
              textAlign: 'right'
            }}>
              {player.elo || 1000}
            </Typography>
            <SimpleRankGauge elo={player.elo} size={32} />
          </Box>
          
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25, justifyContent: 'flex-start' }}>
              <Typography 
                variant="subtitle1" 
                sx={{ 
                  color: isCurrentUser ? colors.seance[200] : colors.grey[100], 
                  fontWeight: isCurrentUser ? 700 : 600,
                  fontSize: '0.9rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  textShadow: isCurrentUser ? `0 0 8px ${colors.seance[400]}` : 'none'
                }}
              >
                {player.alias}
              </Typography>
              {player.is_captain && (
                <Chip
                  label="CAPTAIN"
                  size="small"
                  sx={{
                    bgcolor: colors.seance[500],
                    color: colors.grey[100],
                    fontWeight: 600,
                    fontSize: '0.6rem',
                    height: 18
                  }}
                />
              )}
              {isCurrentUser && (
                <Chip
                  label="YOU"
                  size="small"
                  sx={{
                    bgcolor: colors.seance[400],
                    color: colors.grey[100],
                    fontWeight: 600,
                    fontSize: '0.6rem',
                    height: 18,
                    boxShadow: `0 0 8px ${colors.seance[400]}80`
                  }}
                />
              )}
            </Box>
            
            <Typography variant="caption" sx={{ color: colors.grey[300], display: 'block', textAlign: 'left' }}>
              {recentGames.totalMatches} matches • {recentGames.winRate}% WR • {recentGames.avgKD} K/D
            </Typography>
          </Box>
          
          {/* Avatar - Left side outer */}
          <Avatar
            sx={{
              width: 36,
              height: 36,
              bgcolor: player.is_captain ? colors.seance[500] : colors.grey[600],
              border: player.is_captain ? `2px solid ${colors.seance[300]}` : 'none'
            }}
          >
            {player.is_captain ? <EmojiEventsIcon sx={{ fontSize: 18 }} /> : <PersonIcon sx={{ fontSize: 18 }} />}
          </Avatar>
        </>
      ) : (
        <>
          {/* For right team: Avatar first, then content, then rank */}
          <Avatar
            sx={{
              width: 36,
              height: 36,
              bgcolor: player.is_captain ? colors.seance[500] : colors.grey[600],
              border: player.is_captain ? `2px solid ${colors.seance[300]}` : 'none'
            }}
          >
            {player.is_captain ? <EmojiEventsIcon sx={{ fontSize: 18 }} /> : <PersonIcon sx={{ fontSize: 18 }} />}
          </Avatar>
          
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25 }}>
              <Typography 
                variant="subtitle1" 
                sx={{ 
                  color: isCurrentUser ? colors.seance[200] : colors.grey[100], 
                  fontWeight: isCurrentUser ? 700 : 600,
                  fontSize: '0.9rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  textShadow: isCurrentUser ? `0 0 8px ${colors.seance[400]}` : 'none'
                }}
              >
                {player.alias}
              </Typography>
              {player.is_captain && (
                <Chip
                  label="CAPTAIN"
                  size="small"
                  sx={{
                    bgcolor: colors.seance[500],
                    color: colors.grey[100],
                    fontWeight: 600,
                    fontSize: '0.6rem',
                    height: 18
                  }}
                />
              )}
              {isCurrentUser && (
                <Chip
                  label="YOU"
                  size="small"
                  sx={{
                    bgcolor: colors.seance[400],
                    color: colors.grey[100],
                    fontWeight: 600,
                    fontSize: '0.6rem',
                    height: 18,
                    boxShadow: `0 0 8px ${colors.seance[400]}80`
                  }}
                />
              )}
            </Box>
            
            <Typography variant="caption" sx={{ color: colors.grey[300], display: 'block' }}>
              {recentGames.totalMatches} matches • {recentGames.winRate}% WR • {recentGames.avgKD} K/D
            </Typography>
          </Box>
          
          {/* Rank Gauge - Right side outer */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ 
              color: colors.grey[300], 
              fontWeight: 600,
              minWidth: '40px',
              textAlign: 'left'
            }}>
              {player.elo || 1000}
            </Typography>
            <SimpleRankGauge elo={player.elo} size={32} />
          </Box>
        </>
      )}
    </>
  );

  return (
    <Card
      sx={{
        bgcolor: isCurrentUser ? `${colors.seance[500]}15` : colors.grey[900],
        border: `2px solid ${isCurrentUser ? colors.seance[400] : colors.grey[700]}`,
        borderRadius: '8px',
        transition: 'all 0.2s ease',
        boxShadow: isCurrentUser ? `0 0 12px ${colors.seance[400]}40` : 'none',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: isCurrentUser 
            ? `0 4px 20px ${colors.seance[400]}60` 
            : `0 4px 16px ${colors.primary[700]}80`,
          border: `2px solid ${colors.seance[400]}`,
        }
      }}
    >
      <CardContent sx={{ p: 1.5 }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 1.5,
          flexDirection: isLeftTeam ? 'row-reverse' : 'row',
          minHeight: '48px'
        }}>
          {cardContent}
        </Box>
      </CardContent>
    </Card>
  );
};

// Compact Vertical Map Veto Component
const MapVetoSection = ({ maps, vetoedMaps, currentTurn, timeLeft, onMapVeto, theme, colors, isCaptain, myTeam }) => {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const isMyTurn = currentTurn === myTeam && isCaptain;

  return (
    <Box sx={{ width: '180px', textAlign: 'center' }}>
      {/* Timer */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="body1" sx={{ color: colors.seance[300], fontWeight: 600, mb: 1, fontSize: '0.9rem' }}>
          {currentTurn ? `${currentTurn.replace('_', ' ').toUpperCase()}` : 'VETO PHASE'}
        </Typography>
        <Typography variant="body2" sx={{ color: colors.grey[300], mb: 1, fontSize: '0.8rem' }}>
          is banning a map
        </Typography>
        {timeLeft && (
          <Box sx={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            gap: 0.5,
            bgcolor: colors.primary[500],
            px: 1.5,
            py: 0.25,
            borderRadius: '12px',
            border: `1px solid ${colors.seance[400]}`
          }}>
            <TimerIcon sx={{ color: colors.seance[300], fontSize: 14 }} />
            <Typography variant="body2" sx={{ color: colors.grey[100], fontWeight: 600, fontSize: '0.8rem' }}>
              {formatTime(timeLeft)}
            </Typography>
          </Box>
        )}
      </Box>

      {/* Maps Vertical List */}
      <Stack spacing={0.5}>
        {maps.map((map) => {
          const isVetoed = vetoedMaps.includes(map);
          return (
            <Card
              key={map}
              sx={{
                position: 'relative',
                borderRadius: '6px',
                overflow: 'hidden',
                cursor: isMyTurn && !isVetoed ? 'pointer' : 'default',
                transition: 'all 0.2s ease',
                opacity: isVetoed ? 0.4 : 1,
                filter: isVetoed ? 'grayscale(100%)' : 'none',
                border: `1px solid ${isVetoed ? colors.redAccent[400] : colors.grey[700]}`,
                '&:hover': isMyTurn && !isVetoed ? {
                  transform: 'translateX(4px)',
                  boxShadow: `0 2px 8px ${colors.seance[400]}40`,
                  border: `1px solid ${colors.seance[400]}`,
                } : {}
              }}
              onClick={() => isMyTurn && !isVetoed && onMapVeto(map)}
            >
              <Box
                sx={{
                  height: 32,
                  bgcolor: colors.primary[400],
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative'
                }}
              >
                <Typography variant="body2" sx={{ color: colors.grey[100], fontWeight: 600, fontSize: '0.8rem' }}>
                  {map}
                </Typography>
                
                {isVetoed && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      bgcolor: 'rgba(0,0,0,0.6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <CancelIcon sx={{ color: colors.redAccent[300], fontSize: 18 }} />
                  </Box>
                )}
              </Box>
            </Card>
          );
        })}
      </Stack>
    </Box>
  );
};

// Mock data for preview (remove in production)
const MOCK_MATCH_DATA = {
  match_id: "76d0a036-8c22-4206-b783-8bc5fa258c76",
  state: "veto_phase",
  team_a_players: [
    {
      puuid: "player1-52f0666e-4d7a-5b84-9e1a-a35286de3d27",
      alias: "bakkyzzz",
      elo: 1862,
      mmr: 1300,
      team: "team_a",
      is_captain: true,
      is_ready: false,
      joined_pregame: false
    },
    {
      puuid: "player2-uuid-here", 
      alias: "tadomekarlz",
      elo: 1520,
      mmr: 1220,
      team: "team_a",
      is_captain: false,
      is_ready: false,
      joined_pregame: false
    },
    {
      puuid: "player3-uuid-here",
      alias: "DomikYTx", 
      elo: 1531,
      mmr: 1350,
      team: "team_a",
      is_captain: false,
      is_ready: false,
      joined_pregame: false
    },
    {
      puuid: "player4-uuid-here",
      alias: "61gn",
      elo: 1648,
      mmr: 1150,
      team: "team_a",
      is_captain: false,
      is_ready: false,
      joined_pregame: false
    },
    {
      puuid: "player5-uuid-here",
      alias: "R1_EDDIE",
      elo: 1641,
      mmr: 1420,
      team: "team_a",
      is_captain: false,
      is_ready: false,
      joined_pregame: false
    }
  ],
  team_b_players: [
    {
      puuid: "player6-uuid-here",
      alias: "1mpulsV",
      elo: 1782,
      mmr: 1310,
      team: "team_b",
      is_captain: true,
      is_ready: false,
      joined_pregame: false
    },
    {
      puuid: "player7-uuid-here",
      alias: "sairo",
      elo: 1686,
      mmr: 1190,
      team: "team_b",
      is_captain: false,
      is_ready: false,
      joined_pregame: false
    },
    {
      puuid: "player8-uuid-here",
      alias: "n0matter",
      elo: 1631,
      mmr: 1380,
      team: "team_b",
      is_captain: false,
      is_ready: false,
      joined_pregame: false
    },
    {
      puuid: "player9-uuid-here",
      alias: "adriannr",
      elo: 1749,
      mmr: 1240,
      team: "team_b",
      is_captain: false,
      is_ready: false,
      joined_pregame: false
    },
    {
      puuid: "player10-uuid-here",
      alias: "gennt10",
      elo: 1375,
      mmr: 1480,
      team: "team_b",
      is_captain: false,
      is_ready: false,
      joined_pregame: false
    }
  ],
  team_a_captain: "player1-uuid-here",
  team_b_captain: "player6-uuid-here",
  team_a_lobbies: ["lobby-uuid-1", "lobby-uuid-2"],
  team_b_lobbies: ["lobby-uuid-3", "lobby-uuid-4"],
  map_pool: ["Bind", "Haven", "Split", "Ascent", "Icebox", "Breeze", "Fracture"],
  vetoed_maps: ["Bind", "Haven"],
  remaining_maps: ["Split", "Ascent", "Icebox", "Breeze", "Fracture"],
  final_map: null,
  veto_turn: "team_a",
  veto_deadline: new Date(Date.now() + 30000).toISOString(), // 30 seconds from now
  veto_history: [
    {
      action_type: "ban",
      map_name: "Bind",
      team: "team_a",
      was_timeout: false,
      sequence_number: 1
    },
    {
      action_type: "ban", 
      map_name: "Haven",
      team: "team_b",
      was_timeout: false,
      sequence_number: 2
    }
  ],
  side_selector: null,
  selected_side: null,
  match_quality: 0.85,
  team_a_avg_mmr: 1288.0,
  team_b_avg_mmr: 1320.0
};

export default function MatchPage() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const { connected, sendEvent, on, playerData } = useContext(WebSocketContext);
  const [theme, colorMode] = useMode();
  const colors = tokens(theme.palette.mode);
  
  // Match state
  const [matchData, setMatchData] = useState(MOCK_MATCH_DATA); // Use mock data
  const [loading, setLoading] = useState(false); // Set to false for preview
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
  }, [connected, matchId, sendEvent]);
  
  // Handle match data response
  useEffect(() => {
    const handleMatchData = (data) => {
      console.log('[MATCH PAGE] Received match data:', data);
      setMatchData(data);
      setLoading(false);
      
      // Determine user's team and captain status
      // Note: playerData will be available from WebSocket context
      // This useEffect handles match data from server, team detection happens in render
      
      // Set veto state if in veto phase
      if (data.state === 'veto_phase') {
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
      console.log('[VETO] Not captain, cannot veto');
      return;
    }
    
    if (currentTurn !== myTeam) {
      console.log('[VETO] Not our turn');
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
            {error || 'The requested match could not be found.'}
          </Typography>
          <Button 
            variant="contained" 
            sx={{ mt: 3 }} 
            onClick={() => navigate('/')}
          >
            Return Home
          </Button>
        </Paper>
      </Container>
    );
  }
  
  // Get current user's team and captain status
  const currentUserPuuid = playerData?.puuid;
  const currentUser = [...(matchData.team_a_players || []), ...(matchData.team_b_players || [])]
    .find(p => p.puuid === currentUserPuuid);
  const myTeamPlayers = currentUser?.team === 'team_a' ? matchData.team_a_players : matchData.team_b_players;
  const enemyTeamPlayers = currentUser?.team === 'team_a' ? matchData.team_b_players : matchData.team_a_players;

  return (
    <Container maxWidth="lg" sx={{ height: '100%', overflow: 'hidden' }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          backgroundColor: theme.palette.background.dark,
          padding: `${theme.spacing(1)} 0 ${theme.spacing(2)} 0`,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Match Header - Faceit Style */}
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 3, mt: 1 }}>
          {/* Team A Captain */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar
              sx={{
                width: 48,
                height: 48,
                bgcolor: colors.seance[500],
                border: `2px solid ${colors.seance[300]}`
              }}
            >
              <EmojiEventsIcon sx={{ fontSize: 24 }} />
            </Avatar>
            <Typography variant="h6" sx={{ color: colors.grey[100], fontWeight: 600 }}>
              {matchData.team_a_players?.find(p => p.is_captain)?.alias || 'team_captain'}
            </Typography>
          </Box>

          {/* Match Info Center */}
          <Box sx={{ mx: 6, textAlign: 'center', minWidth: 200 }}>
            <Typography variant="body1" sx={{ color: colors.grey[300], fontWeight: 600, mb: 0.5 }}>
              5v5 NA
            </Typography>
            <Typography variant="h5" sx={{ color: colors.seance[300], fontWeight: 700, mb: 0.5 }}>
              {matchData.state === 'veto_phase' ? 'BAN' : 'READY'}
            </Typography>
            <Typography variant="body2" sx={{ color: colors.grey[400], mb: 1 }}>
              Best of 1
            </Typography>
            
            {/* Match Odds Bar */}
            <Box sx={{ position: 'relative', width: '100%', height: 8, bgcolor: colors.grey[700], borderRadius: 1, overflow: 'hidden' }}>
              <Box
                sx={{
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  height: '100%',
                  width: `${((matchData.team_a_avg_mmr || 1300) / ((matchData.team_a_avg_mmr || 1300) + (matchData.team_b_avg_mmr || 1300))) * 100}%`,
                  bgcolor: colors.seance[400],
                  transition: 'width 0.3s ease'
                }}
              />
              <Box
                sx={{
                  position: 'absolute',
                  right: 0,
                  top: 0,
                  height: '100%',
                  width: `${((matchData.team_b_avg_mmr || 1300) / ((matchData.team_a_avg_mmr || 1300) + (matchData.team_b_avg_mmr || 1300))) * 100}%`,
                  bgcolor: colors.redAccent[400],
                  transition: 'width 0.3s ease'
                }}
              />
            </Box>
            <Typography variant="caption" sx={{ color: colors.grey[500], mt: 0.5, display: 'block' }}>
              {Math.round(((matchData.team_a_avg_mmr || 1300) / ((matchData.team_a_avg_mmr || 1300) + (matchData.team_b_avg_mmr || 1300))) * 100)}% - {Math.round(((matchData.team_b_avg_mmr || 1300) / ((matchData.team_a_avg_mmr || 1300) + (matchData.team_b_avg_mmr || 1300))) * 100)}%
            </Typography>
          </Box>

          {/* Team B Captain */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexDirection: 'row-reverse' }}>
            <Avatar
              sx={{
                width: 48,
                height: 48,
                bgcolor: colors.seance[500],
                border: `2px solid ${colors.seance[300]}`
              }}
            >
              <EmojiEventsIcon sx={{ fontSize: 24 }} />
            </Avatar>
            <Typography variant="h6" sx={{ color: colors.grey[100], fontWeight: 600 }}>
              {matchData.team_b_players?.find(p => p.is_captain)?.alias || 'team_captain'}
            </Typography>
          </Box>
        </Box>


        {/* Main Layout: Team A - Veto - Team B */}
        <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', alignItems: 'flex-start', mt: 1 }}>
          {/* Team A (Left Side) */}
          <Box sx={{ width: '380px' }}>
            <Paper sx={{ 
              p: 2, 
              bgcolor: colors.grey[800],
              borderRadius: '12px',
              border: `1px solid ${colors.grey[600]}`,
              position: 'relative'
            }}>
              
              <Typography variant="h5" sx={{ 
                color: colors.grey[100], 
                fontWeight: 600, 
                mb: 1.5
              }}>
                Team A
              </Typography>

              <Stack spacing={0.75}>
                {matchData.team_a_players?.map((player) => (
                  <PlayerCard 
                    key={player.puuid}
                    player={player} 
                    isCurrentUser={player.puuid === currentUserPuuid}
                    theme={theme}
                    colors={colors}
                    isLeftTeam={true}
                  />
                ))}
              </Stack>
            </Paper>
          </Box>

          {/* Map Veto Section - Center */}
          {matchData.state === 'veto_phase' && (
            <Box sx={{ display: 'flex', alignItems: 'center', minHeight: '400px' }}>
              <MapVetoSection
                maps={matchData.map_pool || []}
                vetoedMaps={matchData.vetoed_maps || []}
                currentTurn={matchData.veto_turn}
                timeLeft={timeLeft}
                onMapVeto={handleVetoMap}
                theme={theme}
                colors={colors}
                isCaptain={isCaptain}
                myTeam={myTeam}
              />
            </Box>
          )}

          {/* Team B (Right Side) */}
          <Box sx={{ width: '380px' }}>
            <Paper sx={{ 
              p: 2, 
              bgcolor: colors.grey[800],
              borderRadius: '12px',
              border: `1px solid ${colors.grey[600]}`,
              position: 'relative'
            }}>
              
              <Typography variant="h5" sx={{ 
                color: colors.grey[100], 
                fontWeight: 600, 
                mb: 1.5,
                textAlign: 'right' 
              }}>
                Team B
              </Typography>

              <Stack spacing={0.75}>
                {matchData.team_b_players?.map((player) => (
                  <PlayerCard 
                    key={player.puuid}
                    player={player} 
                    isCurrentUser={player.puuid === currentUserPuuid}
                    theme={theme}
                    colors={colors}
                    isLeftTeam={false}
                  />
                ))}
              </Stack>
            </Paper>
          </Box>
        </Box>
        
        {/* Connection Status */}
        {!connected && (
          <Alert severity="error" sx={{ mb: 3 }}>
            WebSocket disconnected. Reconnecting...
          </Alert>
        )}
      </Box>
    </Container>
  );
}