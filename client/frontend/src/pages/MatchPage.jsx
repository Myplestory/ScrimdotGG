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
import SideSelection from '../components/SideSelection';
import PostMatchSetup from '../components/PostMatchSetup';

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

// Compact Vertical Server Veto Component
const ServerVetoSection = ({ servers, vetoedServers, currentTurn, timeLeft, onServerVeto, theme, colors, isCaptain, myTeam }) => {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const isMyTurn = currentTurn === myTeam && isCaptain;
  
  // Debug logging
  console.log('🎮 [SERVER VETO COMPONENT] State:', {
    currentTurn,
    myTeam,
    isCaptain,
    isMyTurn,
    serversCount: servers.length,
    vetoedCount: vetoedServers.length
  });

  return (
    <Box sx={{ width: '180px', textAlign: 'center' }}>
      {/* Timer */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="body1" sx={{ color: colors.seance[300], fontWeight: 600, mb: 1, fontSize: '0.9rem' }}>
          {currentTurn ? `${currentTurn.replace('_', ' ').toUpperCase()}` : 'SERVER VETO'}
        </Typography>
        <Typography variant="body2" sx={{ color: colors.grey[300], mb: 1, fontSize: '0.8rem' }}>
          is banning a server
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

      {/* Servers Vertical List */}
      <Stack spacing={0.5}>
        {servers.map((server) => {
          const isVetoed = vetoedServers.includes(server);
          return (
            <Card
              key={server}
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
              onClick={() => isMyTurn && !isVetoed && onServerVeto(server)}
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
                  {server}
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

// Compact Vertical Map Veto Component
const MapVetoSection = ({ maps, vetoedMaps, currentTurn, timeLeft, onMapVeto, theme, colors, isCaptain, myTeam }) => {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const isMyTurn = currentTurn === myTeam && isCaptain;
  
  // Debug logging
  console.log('🎮 [VETO COMPONENT] State:', {
    currentTurn,
    myTeam,
    isCaptain,
    isMyTurn,
    mapsCount: maps.length,
    vetoedCount: vetoedMaps.length
  });

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


export default function MatchPage() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const { connected, sendEvent, on, playerData } = useContext(WebSocketContext);
  const [theme, colorMode] = useMode();
  const colors = tokens(theme.palette.mode);
  
  // Match state
  const [matchData, setMatchData] = useState(null); // Real data from backend
  const [loading, setLoading] = useState(true); // Start with loading true
  const [error, setError] = useState(null);
  
  // Server veto state
  const [serverVetoPhase, setServerVetoPhase] = useState(false);
  const [serverVetoTurn, setServerVetoTurn] = useState(null);
  const [availableServers, setAvailableServers] = useState([]);
  const [vetoedServers, setVetoedServers] = useState([]);
  const [serverVetoDeadline, setServerVetoDeadline] = useState(null);
  
  // Map veto state
  const [vetoPhase, setVetoPhase] = useState(false);
  const [currentTurn, setCurrentTurn] = useState(null);
  const [availableMaps, setAvailableMaps] = useState([]);
  const [vetoedMaps, setVetoedMaps] = useState([]);
  const [vetoHistory, setVetoHistory] = useState([]);
  const [vetoDeadline, setVetoDeadline] = useState(null);
  
  // Side selection state
  const [sideSelectionPhase, setSideSelectionPhase] = useState(false);
  const [sideSelector, setSideSelector] = useState(null);
  const [selectedSide, setSelectedSide] = useState(null);
  const [sideTimeLeft, setSideTimeLeft] = useState(null);
  // Post match setup state
  const [postMatchSetupPhase, setPostMatchSetupPhase] = useState(false);
  const [connectDeadline, setConnectDeadline] = useState(null);
  const [pregameStatus, setPregameStatus] = useState('connecting'); // 'connecting' | 'joined' | 'failed'
  const [startedAt, setStartedAt] = useState(null);

  // Fetch match data on component mount
  useEffect(() => {
    if (matchId && connected) {
      console.log('📤 [MATCH PAGE] Fetching match data for:', matchId);
      sendEvent('get_match_data', { match_id: matchId });
    }
  }, [matchId, connected, sendEvent]);


  const [timeLeft, setTimeLeft] = useState(null);
  
  // Player info
  const [myTeam, setMyTeam] = useState(null);
  const [isCaptain, setIsCaptain] = useState(false);

  // Helper functions for player data mapping
  const getCurrentUserTeam = () => {
    if (!matchData || !playerData) return null;
    
    // Find which team the current user is on
    const teamAHasUser = matchData.team_a_players?.some(p => p.puuid === playerData.puuid);
    return teamAHasUser ? 'team_a' : 'team_b';
  };
  
  const getCurrentUserCaptainStatus = () => {
    if (!matchData || !playerData) return { isCaptain: false, team: null };
    
    // Check if user is captain in team A
    const teamAPlayer = matchData.team_a_players?.find(p => p.puuid === playerData.puuid);
    if (teamAPlayer && teamAPlayer.is_captain) {
      return { isCaptain: true, team: 'team_a' };
    }
    
    // Check if user is captain in team B
    const teamBPlayer = matchData.team_b_players?.find(p => p.puuid === playerData.puuid);
    if (teamBPlayer && teamBPlayer.is_captain) {
      return { isCaptain: true, team: 'team_b' };
    }
    
    return { isCaptain: false, team: teamAPlayer ? 'team_a' : 'team_b' };
  };

  const getMyTeamPlayers = () => {
    if (!matchData) return [];
    const userTeam = getCurrentUserTeam();
    return userTeam === 'team_a' ? matchData.team_a_players : matchData.team_b_players;
  };

  const getEnemyTeamPlayers = () => {
    if (!matchData) return [];
    const userTeam = getCurrentUserTeam();
    return userTeam === 'team_a' ? matchData.team_b_players : matchData.team_a_players;
  };

  const getMatchPhase = () => {
    if (!matchData) return 'Loading...';
    
    switch (matchData.state) {
      case 'SERVER_VETO': return 'Server Ban';
      case 'VETO': return 'Map Ban';
      case 'SIDE_SELECTION': return 'Side';
      case 'READY': return 'Ready';
      default: return 'Loading...';
    }
  };

  const getMatchOdds = () => {
    if (!matchData) return { teamA: 50, teamB: 50 };
    
    // Calculate odds based on MMR difference
    const mmrDiff = matchData.team_a_avg_mmr - matchData.team_b_avg_mmr;
    const oddsA = 50 + (mmrDiff / 100); // Simple calculation
    const oddsB = 100 - oddsA;
    
    return {
      teamA: Math.max(10, Math.min(90, oddsA)),
      teamB: Math.max(10, Math.min(90, oddsB))
    };
  };
  
  // Fetch match data on load
  useEffect(() => {
    if (!connected || !matchId) return;
    
    console.log('[MATCH PAGE] Fetching match data for:', matchId);
    sendEvent('get_match_data', { match_id: matchId });
  }, [connected, matchId, sendEvent]);
  
  // WebSocket event handlers
  useEffect(() => {
    const unsubscribeMatchData = on('match_data', (payload) => {
      console.log('📥 [MATCH PAGE] Received match data:', payload);
      setMatchData(payload);
      setLoading(false);
      setError(null);
      
      // Initialize server veto state from real data
      if (payload.state === 'SERVER_VETO') {
        console.log('🎮 [MATCH PAGE] SERVER VETO PHASE DETECTED - Initializing server veto component');
        console.log('   Server veto turn:', payload.server_veto_turn);
        console.log('   Available servers:', payload.server_pool);
        console.log('   Vetoed servers:', payload.vetoed_servers);
        console.log('   Server veto deadline:', payload.server_veto_deadline);
        
        setServerVetoPhase(true);
        setServerVetoTurn(payload.server_veto_turn);
        setAvailableServers(payload.server_pool || []);
        setVetoedServers(payload.vetoed_servers || []);
        setServerVetoDeadline(payload.server_veto_deadline);
      } else if (payload.state === 'VETO') {
        console.log('🎮 [MATCH PAGE] MAP VETO PHASE DETECTED - Initializing map veto component');
        console.log('   Veto turn:', payload.veto_turn);
        console.log('   Remaining maps:', payload.remaining_maps);
        console.log('   Vetoed maps:', payload.vetoed_maps);
        console.log('   Veto deadline:', payload.veto_deadline);
        
        setVetoPhase(true);
        setCurrentTurn(payload.veto_turn);
        setAvailableMaps(payload.remaining_maps || []);
        setVetoedMaps(payload.vetoed_maps || []);
        setVetoHistory(payload.veto_history || []);
        setVetoDeadline(payload.veto_deadline);
      } else if (payload.state === 'SIDE_SELECTION') {
        console.log('🎮 [MATCH PAGE] SIDE SELECTION PHASE DETECTED - Initializing side selection component');
        console.log('   Final map:', payload.final_map);
        console.log('   Side selector:', payload.side_selector);
        
        setSideSelectionPhase(true);
        setSideSelector(payload.side_selector);
        setSelectedSide(payload.selected_side);
      } else {
        console.log('🎮 [MATCH PAGE] Match state:', payload.state, '- Veto component not initialized');
      }
    });

    const unsubscribeVetoUpdate = on('veto_update', (payload) => {
      console.log('📥 [MATCH PAGE] Veto update received:', payload);
      
      // Update vetoed maps list - add the newly vetoed map
      const newVetoedMaps = [...(vetoedMaps || [])];
      if (payload.map_name && !newVetoedMaps.includes(payload.map_name)) {
        newVetoedMaps.push(payload.map_name);
      }
      
      // Update veto state
      setAvailableMaps(payload.remaining_maps || []);
      setVetoedMaps(newVetoedMaps);
      setVetoHistory(payload.veto_history || []);
      // Handle both 'veto_turn' (from match_data) and 'next_turn' (from veto_update)
      setCurrentTurn(payload.next_turn || payload.veto_turn);
      setVetoDeadline(payload.deadline || payload.veto_deadline);
      
      // Update match data
      setMatchData(prev => ({
        ...prev,
        remaining_maps: payload.remaining_maps,
        vetoed_maps: newVetoedMaps,
        veto_history: payload.veto_history || [],
        veto_turn: payload.next_turn || payload.veto_turn,
        veto_deadline: payload.deadline || payload.veto_deadline
      }));
      
      console.log('✅ [MATCH PAGE] Veto state updated:', {
        currentTurn: payload.next_turn || payload.veto_turn,
        availableMaps: payload.remaining_maps,
        vetoedMaps: newVetoedMaps,
        myTeam,
        isCaptain,
        isMyTurn: (payload.next_turn || payload.veto_turn) === myTeam && isCaptain
      });
    });

    const unsubscribeVetoComplete = on('veto_complete', (payload) => {
      console.log('📥 [MATCH PAGE] Map veto phase completed:', payload);
      setVetoPhase(false);
      setSideSelectionPhase(true);
      setSideSelector(payload.side_selector);
      setSideTimeLeft(30);
      setMatchData(prev => ({
        ...prev,
        state: 'SIDE_SELECTION',
        final_map: payload.final_map,
        side_selector: payload.side_selector
      }));
      
      console.log('🎮 [MATCH PAGE] Transitioning to side selection phase:', {
        finalMap: payload.final_map,
        sideSelector: payload.side_selector
      });
    });

    // Server veto event handlers
    const unsubscribeServerVetoStarted = on('server_veto_started', (payload) => {
      console.log('📥 [MATCH PAGE] Server veto phase started:', payload);
      
      // Initialize server veto state
      setServerVetoPhase(true);
      setServerVetoTurn(payload.current_turn);
      setAvailableServers(payload.available_servers || []);
      setVetoedServers([]);
      setServerVetoDeadline(payload.deadline);
      
      // Update match data
      setMatchData(prev => ({
        ...prev,
        state: 'SERVER_VETO',
        server_pool: payload.available_servers,
        server_veto_turn: payload.current_turn,
        server_veto_deadline: payload.deadline
      }));
      
      console.log('🎮 [MATCH PAGE] Server veto phase initialized:', {
        currentTurn: payload.current_turn,
        availableServers: payload.available_servers,
        myTeam,
        isCaptain,
        isMyTurn: payload.current_turn === myTeam && isCaptain
      });
    });

    const unsubscribeServerVetoUpdate = on('server_veto_update', (payload) => {
      console.log('📥 [MATCH PAGE] Server veto update received:', payload);
      
      // Update vetoed servers list - add the newly vetoed server
      const newVetoedServers = [...(vetoedServers || [])];
      if (payload.server_name && !newVetoedServers.includes(payload.server_name)) {
        newVetoedServers.push(payload.server_name);
      }
      
      // Update server veto state
      setAvailableServers(payload.remaining_servers || []);
      setVetoedServers(newVetoedServers);
      setServerVetoTurn(payload.next_turn || payload.server_veto_turn);
      setServerVetoDeadline(payload.deadline || payload.server_veto_deadline);
      
      // Update match data
      setMatchData(prev => ({
        ...prev,
        server_pool: payload.remaining_servers,
        vetoed_servers: newVetoedServers,
        server_veto_turn: payload.next_turn || payload.server_veto_turn,
        server_veto_deadline: payload.deadline || payload.server_veto_deadline
      }));
      
      console.log('✅ [MATCH PAGE] Server veto state updated:', {
        currentTurn: payload.next_turn || payload.server_veto_turn,
        availableServers: payload.remaining_servers,
        vetoedServers: newVetoedServers,
        myTeam,
        isCaptain,
        isMyTurn: (payload.next_turn || payload.server_veto_turn) === myTeam && isCaptain
      });
    });

    // Handle server_vetoed events (sent by server)
    const unsubscribeServerVetoed = on('server_vetoed', (payload) => {
      console.log('📥 [MATCH PAGE] Server vetoed event received:', payload);
      
      // Update vetoed servers list - add the newly vetoed server
      const vetoedServer = payload.server_name;
      setVetoedServers(prev => {
        const newVetoedServers = [...prev];
        if (vetoedServer && !newVetoedServers.includes(vetoedServer)) {
          newVetoedServers.push(vetoedServer);
        }
        return newVetoedServers;
      });
      
      // Update server veto state
      setAvailableServers(payload.remaining_servers || []);
      setServerVetoTurn(payload.next_turn);
      setServerVetoDeadline(payload.deadline);
      
      // Update match data
      setMatchData(prev => ({
        ...prev,
        server_pool: payload.remaining_servers,
        vetoed_servers: [...(prev.vetoed_servers || []), ...(vetoedServer && !prev.vetoed_servers?.includes(vetoedServer) ? [vetoedServer] : [])],
        server_veto_turn: payload.next_turn,
        server_veto_deadline: payload.deadline
      }));
      
      console.log('✅ [MATCH PAGE] Server vetoed state updated:', {
        currentTurn: payload.next_turn,
        availableServers: payload.remaining_servers,
        vetoedServer: vetoedServer,
        myTeam,
        isCaptain,
        isMyTurn: payload.next_turn === myTeam && isCaptain
      });
    });

    const unsubscribeServerVetoComplete = on('server_veto_complete', (payload) => {
      console.log('📥 [MATCH PAGE] Server veto phase completed:', payload);
      setServerVetoPhase(false);
      setVetoPhase(true);
      setCurrentTurn(payload.current_turn);
      setAvailableMaps(payload.available_maps || []);
      setVetoedMaps([]);
      setVetoHistory([]);
      setVetoDeadline(payload.veto_deadline);
      setMatchData(prev => ({
        ...prev,
        state: 'VETO',
        final_server: payload.final_server,
        map_pool: payload.available_maps,
        veto_turn: payload.current_turn,
        veto_deadline: payload.veto_deadline
      }));
      
      console.log('🎮 [MATCH PAGE] Transitioning to map veto phase:', {
        finalServer: payload.final_server,
        availableMaps: payload.available_maps,
        currentTurn: payload.current_turn
      });
    });

    const unsubscribeSideSelected = on('side_selected', (payload) => {
      console.log('📥 [MATCH PAGE] Side selected:', payload);
      
      setSelectedSide(payload.side);
      setMatchData(prev => ({
        ...prev,
        selected_side: payload.side,
        state: payload.side_complete ? 'READY' : 'SIDE_SELECTION'
      }));
      
      if (payload.side_complete) {
        setSideSelectionPhase(false);
        setSideTimeLeft(null);
        // Begin post-match setup phase with 3-minute connect window (if server doesn't supply one)
        setPostMatchSetupPhase(true);
        const defaultDeadline = new Date(Date.now() + 3 * 60 * 1000).toISOString();
        setConnectDeadline(prev => prev || defaultDeadline);
        setPregameStatus('connecting');
        console.log('🎮 [MATCH PAGE] Side selection completed, match is ready!');
      }
    });

    const unsubscribeError = on('error', (payload) => {
      console.error('❌ [MATCH PAGE] WebSocket error:', payload);
      setError(payload.message || 'An error occurred');
      setLoading(false);
    });

    return () => {
      if (typeof unsubscribeMatchData === 'function') unsubscribeMatchData();
      if (typeof unsubscribeVetoUpdate === 'function') unsubscribeVetoUpdate();
      if (typeof unsubscribeVetoComplete === 'function') unsubscribeVetoComplete();
      if (typeof unsubscribeServerVetoStarted === 'function') unsubscribeServerVetoStarted();
      if (typeof unsubscribeServerVetoUpdate === 'function') unsubscribeServerVetoUpdate();
      if (typeof unsubscribeServerVetoed === 'function') unsubscribeServerVetoed();
      if (typeof unsubscribeServerVetoComplete === 'function') unsubscribeServerVetoComplete();
      if (typeof unsubscribeSideSelected === 'function') unsubscribeSideSelected();
      if (typeof unsubscribeError === 'function') unsubscribeError();
    };
  }, [on]);
  
  
  // Server veto countdown timer
  useEffect(() => {
    if (!serverVetoDeadline) {
      setTimeLeft(null);
      return;
    }
    
    const updateTimer = () => {
      const deadline = new Date(serverVetoDeadline);
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
  }, [serverVetoDeadline]);

  // Map veto countdown timer
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

  // Side selection countdown (fallback 30s if server deadline isn't provided yet)
  useEffect(() => {
    if (!sideSelectionPhase) return;
    // If server provides a deadline later, we can replace this with sync logic similar to veto
    if (sideTimeLeft === null) setSideTimeLeft(30);
    const interval = setInterval(() => {
      setSideTimeLeft(prev => {
        if (prev === null) return null;
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [sideSelectionPhase]);
  
  // Update captain status when match data changes
  useEffect(() => {
    if (matchData && playerData) {
      const captainStatus = getCurrentUserCaptainStatus();
      setIsCaptain(captainStatus.isCaptain);
      setMyTeam(captainStatus.team);
      
      console.log('🎮 [MATCH PAGE] Captain status updated:', {
        isCaptain: captainStatus.isCaptain,
        team: captainStatus.team,
        playerPuuid: playerData.puuid
      });
    }
  }, [matchData, playerData]);
  
  // Handle server veto action
  const handleServerVetoAction = (serverName) => {
    if (!isCaptain) {
      console.log('[SERVER VETO] Not captain, cannot veto');
      return;
    }
    
    if (serverVetoTurn !== myTeam) {
      console.log('[SERVER VETO] Not our turn');
      return;
    }
    
    console.log('[SERVER VETO] Vetoing server:', serverName);
    sendEvent('veto_server', {
      match_id: matchId,
      server_name: serverName
    });
  };

  // Handle map veto action
  const handleVetoMapAction = (mapName) => {
    if (!isCaptain) {
      console.log('[MAP VETO] Not captain, cannot veto');
      return;
    }
    
    if (currentTurn !== myTeam) {
      console.log('[MAP VETO] Not our turn');
      return;
    }
    
    console.log('[MAP VETO] Vetoing map:', mapName);
    sendEvent('veto_map', {
      match_id: matchId,
      map_name: mapName
    });
  };

  const handleSideSelection = (side) => {
    console.log('[SIDE SELECTION] Attempting to select side:', side);
    console.log('[SIDE SELECTION] Debug info:', {
      isCaptain,
      myTeam,
      sideSelector,
      canSelect: isCaptain && sideSelector === myTeam
    });
    
    if (!isCaptain) {
      console.log('[SIDE SELECTION] Not captain, cannot select side');
      return;
    }
    
    if (sideSelector !== myTeam) {
      console.log('[SIDE SELECTION] Not our turn to select side');
      console.log('[SIDE SELECTION] Expected selector:', sideSelector, 'My team:', myTeam);
      return;
    }
    
    console.log('[SIDE SELECTION] Selecting side:', side);
    sendEvent('select_side', {
      match_id: matchId,
      side: side
    });
  };
  
  // Render loading state
  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: theme.palette.background.dark
      }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h5" sx={{ color: colors.grey[100], mb: 2 }}>
            Loading Match...
          </Typography>
          <LinearProgress sx={{ width: 200 }} />
        </Box>
      </Box>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: theme.palette.background.dark
      }}>
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          <Typography variant="h6" gutterBottom>
            Error Loading Match
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            {error}
          </Typography>
          <Button 
            variant="contained" 
            onClick={() => navigate('/')}
            size="small"
          >
            Return Home
          </Button>
        </Alert>
      </Box>
    );
  }

  // No match data state
  if (!matchData) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: theme.palette.background.dark
      }}>
        <Alert severity="warning" sx={{ maxWidth: 400 }}>
          <Typography variant="h6" gutterBottom>
            Match Not Found
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            The requested match could not be found.
          </Typography>
          <Button 
            variant="contained" 
            onClick={() => navigate('/')}
            size="small"
          >
            Return Home
          </Button>
        </Alert>
      </Box>
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
              {getMatchPhase()}
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
                  width: `${getMatchOdds().teamA}%`,
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
                  width: `${getMatchOdds().teamB}%`,
                  bgcolor: colors.redAccent[400],
                  transition: 'width 0.3s ease'
                }}
              />
            </Box>
            <Typography variant="caption" sx={{ color: colors.grey[500], mt: 0.5, display: 'block' }}>
              {Math.round(getMatchOdds().teamA)}% - {Math.round(getMatchOdds().teamB)}%
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


        {/* Main Layout: My Team - Veto - Enemy Team */}
        <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', alignItems: 'flex-start', mt: 1 }}>
          {/* My Team (Left Side) */}
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
                {getCurrentUserTeam() === 'team_a' ? 'Team A' : 'Team B'}
              </Typography>

              <Stack spacing={0.75}>
                {getMyTeamPlayers()?.map((player) => (
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

          {/* Server Veto Section - Center */}
          {serverVetoPhase && (
            <Box sx={{ display: 'flex', alignItems: 'center', minHeight: '400px' }}>
              <ServerVetoSection
                servers={availableServers}
                vetoedServers={vetoedServers}
                currentTurn={serverVetoTurn}
                timeLeft={timeLeft}
                onServerVeto={handleServerVetoAction}
                theme={theme}
                colors={colors}
                isCaptain={isCaptain}
                myTeam={myTeam}
              />
            </Box>
          )}

          {/* Map Veto Section - Center */}
          {vetoPhase && (
            <Box sx={{ display: 'flex', alignItems: 'center', minHeight: '400px' }}>
              <MapVetoSection
                maps={availableMaps}
                vetoedMaps={vetoedMaps}
                currentTurn={currentTurn}
                timeLeft={timeLeft}
                onMapVeto={handleVetoMapAction}
                theme={theme}
                colors={colors}
                isCaptain={isCaptain}
                myTeam={myTeam}
              />
            </Box>
          )}

          {/* Side Selection Section - Center */}
          {sideSelectionPhase && (
            <Box sx={{ display: 'flex', alignItems: 'center', minHeight: '400px' }}>
              <SideSelection
                finalMap={matchData?.final_map}
                serverLocation="US-East" // TODO: Get from match data
                isCaptain={isCaptain}
                myTeam={myTeam}
                currentTurn={sideSelector}
                onSideSelect={handleSideSelection}
                timeLeft={sideTimeLeft}
              />
            </Box>
          )}

          {/* Post Match Setup Section - Center */}
          {postMatchSetupPhase && (
            <Box sx={{ display: 'flex', alignItems: 'center', minHeight: '400px' }}>
              <PostMatchSetup
                finalMap={matchData?.final_map}
                serverLocation="US-East" // TODO: Get from match data
                pregameStatus={pregameStatus}
                connectDeadline={connectDeadline}
                startedAt={startedAt}
                onManualConnect={() => {
                  console.log('[POST MATCH SETUP] Manual connect clicked');
                  // TODO: emit manual connect event when backend handler is ready
                  // sendEvent('manual_connect', { match_id: matchId });
                }}
              />
            </Box>
          )}

          {/* Enemy Team (Right Side) */}
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
                {getCurrentUserTeam() === 'team_a' ? 'Team B' : 'Team A'}
              </Typography>

              <Stack spacing={0.75}>
                {getEnemyTeamPlayers()?.map((player) => (
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