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
  const stats = player?.stats || {};
  const totalMatches = stats.total_matches ?? stats.totalMatches ?? 0;
  const winRate = stats.win_rate ?? stats.winRate ?? 0;
  const averageKDRaw = stats.average_kd ?? stats.avgKD ?? 0;
  const averageKD = Number.isFinite(averageKDRaw) ? Number(averageKDRaw) : 0;

  const statsLabel = totalMatches
    ? `${totalMatches} matches • ${winRate}% WR • ${averageKD.toFixed(2)} K/D`
    : 'No match history';

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
              {statsLabel}
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
              {statsLabel}
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
        {timeLeft !== null && (
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
        {timeLeft !== null && (
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
  const { connected, sendEvent, playerData, matchData } = useContext(WebSocketContext);
  const [theme, colorMode] = useMode();
  const colors = tokens(theme.palette.mode);
  
  // Match state
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
  const [sideSelectionDeadline, setSideSelectionDeadline] = useState(null);
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

  const [serverTimeLeft, setServerTimeLeft] = useState(null);
  const [mapTimeLeft, setMapTimeLeft] = useState(null);
  
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
      case 'MAP_VETO': return 'Map Ban';
      case 'SIDE_SELECTION': return 'Side';
      case 'READY': return 'Ready';
      default: return 'Loading...';
    }
  };

  const getMatchOdds = () => {
    if (!matchData) return { teamA: 50, teamB: 50 };
    
    const avgEloA = matchData.meta?.team_a_avg_elo ?? matchData.team_a_avg_elo ?? 0;
    const avgEloB = matchData.meta?.team_b_avg_elo ?? matchData.team_b_avg_elo ?? 0;

    if (!avgEloA && !avgEloB) {
      return { teamA: 50, teamB: 50 };
    }

    const ratingDiff = avgEloA - avgEloB;
    const oddsA = 50 + (ratingDiff / 50); // Simple sensitivity curve
    const oddsB = 100 - oddsA;
    
    return {
      teamA: Math.max(10, Math.min(90, oddsA)),
      teamB: Math.max(10, Math.min(90, oddsB)),
    };
  };
  
  // WebSocket event handlers
  // (legacy handlers removed)
  
  // Server veto countdown timer
  useEffect(() => {
    if (!serverVetoDeadline) {
      setServerTimeLeft(null);
      return;
    }
    
    const updateTimer = () => {
      const deadline = new Date(serverVetoDeadline);
      const now = new Date();
      const diff = Math.max(0, Math.floor((deadline - now) / 1000));
      setServerTimeLeft(diff);
      
      if (diff === 0) {
        // Timer expired
        setServerTimeLeft(0);
      }
    };
    
    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    
    return () => clearInterval(interval);
  }, [serverVetoDeadline]);

  // Map veto countdown timer
  useEffect(() => {
    if (!vetoDeadline) {
      setMapTimeLeft(null);
      return;
    }
    
    const updateTimer = () => {
      const deadline = new Date(vetoDeadline);
      const now = new Date();
      const diff = Math.max(0, Math.floor((deadline - now) / 1000));
      setMapTimeLeft(diff);
      
      if (diff === 0) {
        // Timer expired
        setMapTimeLeft(0);
      }
    };
    
    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    
    return () => clearInterval(interval);
  }, [vetoDeadline]);

  // Side selection countdown (uses server-supplied deadline when available)
  useEffect(() => {
    if (!sideSelectionPhase) {
      setSideTimeLeft(null);
      return;
    }

    if (!sideSelectionDeadline) {
      setSideTimeLeft(prev => (prev === null ? 30 : prev));
      return;
    }

    const updateTimer = () => {
      const deadline = new Date(sideSelectionDeadline);
      const now = new Date();
      const diff = Math.max(0, Math.floor((deadline - now) / 1000));
      setSideTimeLeft(diff);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [sideSelectionPhase, sideSelectionDeadline]);
  
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
  
  useEffect(() => {
    if (!matchData) return;

    setLoading(false);
    setError(null);

    const currentState = matchData.state;
    const draft = matchData.draft || {};
    const serversInfo = draft.servers || {};
    const mapsInfo = draft.maps || {};
    const sideInfo = draft.side || {};

    const resolvedAvailableServers =
      serversInfo.remaining ??
      serversInfo.pool ??
      matchData.available_servers ??
      matchData.server_pool ??
      [];

    const resolvedVetoedServers =
      serversInfo.vetoed ??
      matchData.vetoed_servers ??
      [];

    const resolvedServerDeadline =
      serversInfo.deadline ??
      matchData.server_veto_deadline ??
      null;

    const inServerVeto = currentState === 'SERVER_VETO';
    const inMapVeto = currentState === 'MAP_VETO';

    setServerVetoPhase(inServerVeto);
    setServerVetoTurn(serversInfo.turn ?? matchData.server_veto_turn ?? null);
    setAvailableServers(resolvedAvailableServers);
    setVetoedServers(resolvedVetoedServers);
    if (inServerVeto) {
      setServerVetoDeadline(resolvedServerDeadline);
    } else {
      setServerVetoDeadline(null);
      setServerTimeLeft(null);
    }

    const resolvedAvailableMaps =
      mapsInfo.remaining ??
      matchData.remaining_maps ??
      mapsInfo.pool ??
      matchData.available_maps ??
      matchData.map_pool ??
      [];

    const resolvedVetoedMaps =
      mapsInfo.vetoed ??
      matchData.vetoed_maps ??
      [];

    const resolvedVetoDeadline =
      mapsInfo.deadline ??
      matchData.veto_deadline ??
      null;

    const resolvedVetoHistory =
      mapsInfo.history ??
      matchData.veto_history ??
      [];

    setVetoPhase(inMapVeto);
    setCurrentTurn(mapsInfo.turn ?? matchData.veto_turn ?? null);
    setAvailableMaps(resolvedAvailableMaps);
    setVetoedMaps(resolvedVetoedMaps);
    setVetoHistory(resolvedVetoHistory);

    if (inMapVeto) {
      setVetoDeadline(prev => {
        if (!resolvedVetoDeadline) {
          return prev;
        }
        return prev === resolvedVetoDeadline ? prev : resolvedVetoDeadline;
      });
    } else {
      setVetoDeadline(null);
      setMapTimeLeft(null);
    }

    setSideSelectionPhase(currentState === 'SIDE_SELECTION');
    setSideSelector(sideInfo.selector ?? matchData.side_selector ?? null);
    setSelectedSide(sideInfo.selected ?? matchData.selected_side ?? null);
    const resolvedSideDeadline =
      sideInfo.deadline ??
      matchData.side_selection_deadline ??
      null;
    setSideSelectionDeadline(resolvedSideDeadline);

    if (currentState === 'SIDE_SELECTION') {
      // reset connection status while awaiting final selection
      setPostMatchSetupPhase(false);
      setConnectDeadline(null);
    } else if (['READY', 'CREATING', 'IN_PROGRESS'].includes(currentState)) {
      setPostMatchSetupPhase(true);
      const defaultConnectDeadline =
        resolvedSideDeadline || new Date(Date.now() + 3 * 60 * 1000).toISOString();
      setConnectDeadline(prev => prev || defaultConnectDeadline);
      setPregameStatus(prev => (prev === 'connecting' ? prev : 'connecting'));
    } else {
      setPostMatchSetupPhase(false);
      setConnectDeadline(null);
    }
  }, [matchData]);
  
  // Handle server veto action
  const handleServerVetoAction = (serverName) => {
    console.log('[SERVER VETO] Attempting veto:', {
      serverName,
      isCaptain,
      myTeam,
      serverVetoTurn,
      playerData,
      matchId
    });
    
    if (!isCaptain) {
      console.error('[SERVER VETO] ❌ Not captain, cannot veto', {
        isCaptain,
        playerData,
        matchData: matchData ? {
          team_a_captain: matchData.team_a_captain,
          team_b_captain: matchData.team_b_captain
        } : null
      });
      alert('You are not the captain! Only captains can veto.');
      return;
    }
    
    if (serverVetoTurn !== myTeam) {
      console.warn('[SERVER VETO] ⚠️  Not our turn', {
        serverVetoTurn,
        myTeam
      });
      alert(`It's not your team's turn! Current turn: ${serverVetoTurn}`);
      return;
    }
    
    console.log('[SERVER VETO] ✅ Vetoing server:', serverName);
    sendEvent('veto_server', {
      match_id: matchId,
      server_name: serverName
    });
  };

  // Handle map veto action
  const handleVetoMapAction = (mapName) => {
    console.log('[MAP VETO] Attempting veto:', {
      mapName,
      isCaptain,
      myTeam,
      currentTurn,
      playerData,
      matchId
    });
    
    if (!isCaptain) {
      console.error('[MAP VETO] ❌ Not captain, cannot veto', {
        isCaptain,
        playerData,
        matchData: matchData ? {
          team_a_captain: matchData.team_a_captain,
          team_b_captain: matchData.team_b_captain
        } : null
      });
      alert('You are not the captain! Only captains can veto.');
      return;
    }
    
    if (currentTurn !== myTeam) {
      console.warn('[MAP VETO] ⚠️  Not our turn', {
        currentTurn,
        myTeam
      });
      alert(`It's not your team's turn! Current turn: ${currentTurn}`);
      return;
    }
    
    console.log('[MAP VETO] ✅ Vetoing map:', mapName);
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
    
    console.log('[SIDE SELECTION] ✅ Selecting side:', side);
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
                timeLeft={serverTimeLeft}
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
                timeLeft={mapTimeLeft}
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