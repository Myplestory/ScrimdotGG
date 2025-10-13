// PugQueue.jsx - Main PUG queue screen (FACEIT-like)
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Avatar,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  IconButton,
  Badge,
  TextField,
  Container
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Timer,
  People,
  Star,
  Flag,
  TrendingUp,
  TrendingDown,
  Search,
  Add
} from '@mui/icons-material';
import { useMode } from '../theme';
import { useWebSocket } from '../contexts/WebSocketContext';
import PlayerSlot from '../components/lobby/playerslot';

const PugQueue = () => {
  const [theme, colorMode] = useMode();
  const navigate = useNavigate();
  const [queueStatus, setQueueStatus] = useState({
    in_queue: false,
    queue_type: null,
    estimated_wait: 0,
    players_in_queue: 0
  });
  const [matchFound, setMatchFound] = useState(false);
  const [matchData, setMatchData] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30);
  const [acceptedCount, setAcceptedCount] = useState(0);
  const [totalPlayers, setTotalPlayers] = useState(10);
  const [userAccepted, setUserAccepted] = useState(false);
  
  // Preview mode for testing modal design
  useEffect(() => {
    const handlePreview = () => {
      setMatchFound(true);
      setTimeLeft(30);
      setMatchData({
        match_id: 'preview-123',
        timeout_seconds: 30,
        message: 'Preview match found!'
      });
    };
    
    window.addEventListener('preview-match-modal', handlePreview);
    return () => window.removeEventListener('preview-match-modal', handlePreview);
  }, []);
  const [selectedQueueType, setSelectedQueueType] = useState('pug');
  const [selectedMaps, setSelectedMaps] = useState([]);
  const [selectedServers, setSelectedServers] = useState([]);
  const [players, setPlayers] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [activeTab, setActiveTab] = useState('maps'); // 'maps', 'match_type', 'servers'
  const [queueStartTime, setQueueStartTime] = useState(null);
  const messagesEndRef = useRef(null);

  // Use WebSocket context
  const { playerData, api, on, reconnect, connected, systemStatus } = useWebSocket();

  // Monitor WebSocket connection and reconnect if needed
  useEffect(() => {
    if (!connected) {
      console.log('WebSocket disconnected, attempting to reconnect...');
      reconnect();
    }
  }, [connected, reconnect]);

  // Set default region and servers (will be overridden by user selection)
  useEffect(() => {
    setPlayerRegion('na');
    setAvailableServers(['Virginia', 'Illinois']);
  }, []);

  // Available maps for Valorant
  const availableMaps = [
    'Ascent', 'Bind', 'Breeze', 'Fracture', 'Haven', 'Icebox', 'Lotus', 'Pearl', 'Split'
  ];

  // Available servers (will be populated based on detected region)
  const [availableServers, setAvailableServers] = useState([]);
  const [playerRegion, setPlayerRegion] = useState(null);


  // Initialize with current player
  useEffect(() => {
    if (playerData && players.length === 0) {
      setPlayers([{
        puuid: playerData.puuid,
        alias: playerData.alias,
        rank: playerData.rank,
        elo: playerData.elo,
        isLeader: true
      }]);
    }
  }, [playerData]);

  // Auto-scroll chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  // Listen for queue events
  useEffect(() => {
    const unsubscribeQueueJoined = on('queue_joined', (payload) => {
      setQueueStatus({
        in_queue: true,
        queue_type: payload.queue_type,
        estimated_wait: payload.estimated_wait,
        players_in_queue: payload.players_in_queue || 0
      });
      // Set queue start time if not already set
      if (!queueStartTime) {
        setQueueStartTime(Date.now());
      }
    });

    const unsubscribeQueueLeft = on('queue_left', () => {
      setQueueStatus({
        in_queue: false,
        queue_type: null,
        estimated_wait: 0,
        players_in_queue: 0
      });
      setQueueStartTime(null); // Reset timer when leaving queue
    });

    const unsubscribeMatchFound = on('pug_match_found', (payload) => {
      console.log('🎮 [DEBUG] pug_match_found event received:', payload);
      setMatchFound(true);
      setMatchData(payload);
      setTimeLeft(payload.accept_deadline || 30);
      setAcceptedCount(0);
      setTotalPlayers(10);
      setUserAccepted(false);
    });

    const unsubscribePlayerAccepted = on('player_accepted', (payload) => {
      console.log('🔔 [DEBUG] player_accepted event received:', payload);
      console.log('🔔 [DEBUG] Setting acceptedCount to:', payload.accepted_count || 0);
      console.log('🔔 [DEBUG] Setting totalPlayers to:', payload.total_players || 10);
      console.log('🔔 [DEBUG] Server timeout_seconds:', payload.timeout_seconds);
      setAcceptedCount(payload.accepted_count || 0);
      setTotalPlayers(payload.total_players || 10);
      
      // Sync with server time if there's a significant discrepancy (>2 seconds)
      // This handles clock drift while keeping the countdown smooth
      const serverTime = payload.timeout_seconds || 30;
      setTimeLeft(prev => {
        const diff = Math.abs(prev - serverTime);
        if (diff > 2) {
          console.log(`⏰ Syncing timer: ${prev}s -> ${serverTime}s (diff: ${diff}s)`);
          return serverTime;
        }
        return prev; // Keep local countdown if close enough
      });
    });

    const unsubscribeMatchReady = on('match_ready', (payload) => {
      // All players accepted - match ready (legacy event)
      setMatchFound(false);
      console.log('Match ready!', payload);
    });
    
    const unsubscribeMatchConfirmed = on('match_confirmed', (payload) => {
      // All players accepted - redirect to match page
      console.log('Match confirmed! Redirecting to match page...', payload);
      setMatchFound(false);
      
      // Auto-redirect to match page
      if (payload.match_id) {
        navigate(`/match/${payload.match_id}`);
      }
    });

    const unsubscribeMatchTimeout = on('match_timeout', (payload) => {
      // Match acceptance timed out - close modal
      console.log('Match acceptance timed out:', payload);
      
      // Check if user accepted before timing out
      const userDidAccept = userAccepted;
      
      setMatchFound(false);
      setMatchData(null);
      setAcceptedCount(0);
      setTotalPlayers(10);
      setUserAccepted(false);
      
      // Only remove from queue if user DIDN'T accept
      // If user accepted, they should be requeued automatically by the server
      if (!userDidAccept && queueStatus.in_queue) {
        console.log('User did not accept - leaving queue');
        api.leavePugQueue();
        setQueueStartTime(null);
      } else if (userDidAccept) {
        console.log('User accepted - staying in queue for automatic requeue');
      }
    });

    const unsubscribeLobbyMessage = on('lobby_message', (payload) => {
      setChatMessages(prev => [...prev, payload]);
    });

    return () => {
      if (typeof unsubscribeQueueJoined === 'function') unsubscribeQueueJoined();
      if (typeof unsubscribeQueueLeft === 'function') unsubscribeQueueLeft();
      if (typeof unsubscribeMatchFound === 'function') unsubscribeMatchFound();
      if (typeof unsubscribePlayerAccepted === 'function') unsubscribePlayerAccepted();
      if (typeof unsubscribeMatchReady === 'function') unsubscribeMatchReady();
      if (typeof unsubscribeMatchConfirmed === 'function') unsubscribeMatchConfirmed();
      if (typeof unsubscribeMatchTimeout === 'function') unsubscribeMatchTimeout();
      if (typeof unsubscribeLobbyMessage === 'function') unsubscribeLobbyMessage();
    };
  }, [on]);

  // Countdown timer for match acceptance
  useEffect(() => {
    if (matchFound && timeLeft > 0) {
      const timer = setTimeout(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (matchFound && timeLeft === 0) {
      // Timer expired - check if user accepted before removing from queue
      console.log('Match acceptance timer expired, closing modal');
      
      // Check if user accepted before timing out
      const userDidAccept = userAccepted;
      
      setMatchFound(false);
      setMatchData(null);
      setAcceptedCount(0);
      setTotalPlayers(10);
      setUserAccepted(false);
      
      // Only remove from queue if user DIDN'T accept
      // If user accepted, they should be requeued automatically by the server
      if (!userDidAccept && queueStatus.in_queue) {
        console.log('User did not accept - leaving queue');
        api.leavePugQueue();
        setQueueStartTime(null);
      } else if (userDidAccept) {
        console.log('User accepted - staying in queue, waiting for server requeue');
        // Don't reset queueStartTime - keep timer running
      }
      
      // Optional: Show a brief message that the match expired
      // You could add a toast notification here if desired
    }
  }, [matchFound, timeLeft]);

  const handleJoinQueue = () => {
    if (selectedMaps.length < 5) {
      return; // Should be disabled by UI
    }
    api.joinPugQueue({
      queue_type: selectedQueueType,
      preferred_maps: selectedMaps,
        preferred_servers: selectedServers
    });
  };

  const handleLeaveQueue = () => {
    api.leavePugQueue();
    setQueueStartTime(null);
  };

  const handleFindMatch = () => {
    if (queueStatus.in_queue) {
      handleLeaveQueue();
    } else {
      // Enter queue
      setQueueStartTime(Date.now());
      api.joinPugQueue({
        queue_type: selectedQueueType,
        preferred_maps: selectedMaps,
        preferred_servers: selectedServers
      });
    }
  };

  // Calculate queue time
  const getQueueTime = () => {
    if (!queueStartTime) return '0:00';
    const elapsed = Math.floor((Date.now() - queueStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Format region and queue type for title
  const getQueueTitle = () => {
    const queueType = selectedQueueType === 'pug' ? '5v5' : '5v5 Super';
    
    console.log('getQueueTitle - playerRegion:', playerRegion);
    
    if (playerRegion) {
      // Map region codes to display names
      const regionNames = {
        'na': 'North America',
        'eu': 'Europe',
        'latam': 'Latin America',
        'br': 'Brazil',
        'ap': 'Asia Pacific',
        'kr': 'Korea'
      };
      
      const regionName = regionNames[playerRegion] || 'Global';
      const title = `${regionName} ${queueType}`;
      console.log('Generated title:', title);
      return title;
    }
    
    console.log('No playerRegion, using Global');
    return `Global ${queueType}`;
  };

  // Check if current user is party leader
  const isPartyLeader = () => {
    return players.length > 0 && players[0]?.isLeader;
  };

  // Update queue timer every second when in queue
  const [, forceUpdate] = useState(0);
  useEffect(() => {
    let interval;
    if (queueStatus.in_queue && queueStartTime) {
      interval = setInterval(() => {
        // Force re-render to update timer display
        forceUpdate(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [queueStatus.in_queue, queueStartTime]);

  const sendLobbyMessage = () => {
    if (!newMessage.trim()) return;
    
    const message = {
      user: playerData?.alias || 'Unknown',
      message: newMessage.trim(),
      timestamp: new Date().toISOString(),
      type: 'lobby'
    };
    
    setChatMessages(prev => [...prev, message]);
    setNewMessage('');
  };

  const handleEmptySlotClick = (slotIndex) => {
    console.log('Empty slot clicked:', slotIndex);
    // Implement invite logic when ready
  };

  const handleAcceptMatch = () => {
    if (matchData?.match_id) {
      api.acceptMatch(matchData.match_id);
      setUserAccepted(true); // Mark that user has accepted
    }
    // Don't close modal yet - wait for server response
  };

  const handleDeclineMatch = () => {
    if (matchData?.match_id) {
      api.declineMatch(matchData.match_id);
    }
    setMatchFound(false);
    setMatchData(null);
    setAcceptedCount(0);
    setTotalPlayers(10);
    setUserAccepted(false);
    
    // Remove user from queue since they declined the match
    if (queueStatus.in_queue) {
      api.leavePugQueue();
      setQueueStartTime(null);
    }
  };

  const toggleMap = (mapName) => {
    setSelectedMaps(prev => 
      prev.includes(mapName) 
        ? prev.filter(m => m !== mapName)
        : [...prev, mapName]
    );
  };

  const toggleServer = (serverName) => {
    setSelectedServers(prev => 
      prev.includes(serverName) 
        ? prev.filter(s => s !== serverName)
        : [...prev, serverName]
    );
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Component for showing acceptance progress
  const AcceptanceProgress = () => {
    console.log('🎯 [DEBUG] AcceptanceProgress render - acceptedCount:', acceptedCount, 'totalPlayers:', totalPlayers);
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5, mb: 2 }}>
        {Array.from({ length: totalPlayers }).map((_, index) => (
          <Box
            key={index}
            sx={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: index < acceptedCount ? theme.palette.secondary.main : '#333',
              border: `2px solid ${index < acceptedCount ? theme.palette.secondary.main : '#555'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.3s ease'
            }}
          >
            <Typography
              sx={{
                fontSize: '10px',
                color: index < acceptedCount ? '#000' : '#999',
                fontWeight: 'bold'
              }}
            >
              {index < acceptedCount ? '✓' : '○'}
            </Typography>
          </Box>
        ))}
      </Box>
    );
  };

  return (
    <Container maxWidth="md" sx={{ height: '100%', overflow: 'hidden' }}>
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
        {/* Header */}
        <Typography variant="h4" align="center" gutterBottom sx={{ color: theme.palette.secondary.main }}>
          {getQueueTitle()}
        </Typography>
        

        
        
        {/* Player Cards Section */}
        <Grid container spacing={1.5} justifyContent="center" alignItems="center" sx={{ mt: -2, mb: 0, minHeight: '200px' }}>
          {Array.from({ length: 5 }).map((_, index) => {
            // Center the user's player card (index 2)
            let player = null;
            if (index === 2 && players.length > 0) {
              // Put the first player (current user) in the middle slot
              player = players[0];
            } else if (index !== 2 && players.length > index + (index > 2 ? 0 : 1)) {
              // Put other players in remaining slots
              const playerIndex = index > 2 ? index : index + 1;
              player = players[playerIndex];
            }
            
            return (
              <Grid item key={player ? player.puuid : `empty-${index}`} xs={2.4}>
                <PlayerSlot 
                  player={player} 
                  handleEmptySlotClick={handleEmptySlotClick} 
                  slotIndex={index} 
                />
              </Grid>
            );
          })}
        </Grid>


        {/* Horizontal Settings Card */}
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          mt: 4,
          mb: 0,
          px: 1.5,
          py: 1,
          backgroundColor: theme.palette.background.paper,
          borderRadius: 1,
        }}>
          {/* Left side - Toggle tabs */}
          <Box sx={{ display: 'flex', flex: 1, gap: 2 }}>
            <Button
              variant={activeTab === 'match_type' ? 'contained' : 'text'}
              onClick={() => setActiveTab('match_type')}
              size="small"
              sx={{
                color: activeTab === 'match_type' ? 'white' : theme.palette.text.secondary,
                borderBottom: activeTab === 'match_type' ? `2px solid ${theme.palette.secondary.main}` : 'none',
                borderRadius: 0,
                px: 1.5,
                py: 0.5,
                fontSize: '0.875rem',
                minHeight: 'auto',
              }}
            >
              MATCH TYPE
            </Button>
            <Button
              variant={activeTab === 'maps' ? 'contained' : 'text'}
              onClick={() => setActiveTab('maps')}
              size="small"
              sx={{
                color: activeTab === 'maps' ? 'white' : theme.palette.text.secondary,
                borderBottom: activeTab === 'maps' ? `2px solid ${theme.palette.secondary.main}` : 'none',
                borderRadius: 0,
                px: 1.5,
                py: 0.5,
                fontSize: '0.875rem',
                minHeight: 'auto',
              }}
            >
              MAPS {selectedMaps.length}/9
            </Button>
            <Button
              variant={activeTab === 'servers' ? 'contained' : 'text'}
              onClick={() => setActiveTab('servers')}
              size="small"
              sx={{
                color: activeTab === 'servers' ? 'white' : theme.palette.text.secondary,
                borderBottom: activeTab === 'servers' ? `2px solid ${theme.palette.secondary.main}` : 'none',
                borderRadius: 0,
                px: 1.5,
                py: 0.5,
                fontSize: '0.875rem',
                minHeight: 'auto',
              }}
            >
              SERVERS {selectedServers.length}/{availableServers.length}
            </Button>
          </Box>

          {/* Right side - Find Match Button */}
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button
              variant="contained"
              size="medium"
              onClick={handleFindMatch}
              disabled={selectedMaps.length < 5 || !isPartyLeader() || !connected || systemStatus.valorant.status !== 'running'}
              sx={{
                fontSize: '1rem',
                py: 0.75, 
                px: 4, 
                minWidth: '140px', // Fixed width to prevent growing
                backgroundColor: queueStatus.in_queue ? theme.palette.error.main : theme.palette.secondary.main,
                color: theme.palette.getContrastText(queueStatus.in_queue ? theme.palette.error.main : theme.palette.secondary.main),
                '&:hover': {
                  backgroundColor: queueStatus.in_queue ? theme.palette.error.dark : theme.palette.secondary.dark,
                },
                '&:disabled': {
                  backgroundColor: theme.palette.action.disabled,
                }
              }}
            >
              {queueStatus.in_queue ? `CANCEL (${getQueueTime()})` : 'FIND MATCH'}
            </Button>
          </Box>
        </Box>

        {/* Tab Content */}
        <Box sx={{ mb: 3, minHeight: 'auto', backgroundColor: theme.palette.background.paper, borderRadius: 1, px: 1.5, pt: 1, pb: 1, mt: 0 }}>
          {activeTab === 'match_type' && (
            <Box>
              <Grid container spacing={1.5}>
                <Grid item xs={6}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      border: selectedQueueType === 'pug' ? `2px solid ${theme.palette.secondary.main}` : '1px solid transparent',
                      backgroundColor: selectedQueueType === 'pug' ? theme.palette.action.hover : 'transparent',
                      '&:hover': { backgroundColor: theme.palette.action.hover },
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                    onClick={() => setSelectedQueueType('pug')}
                  >
                    <CardContent sx={{ p: 1, pb: 0.5, display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <Typography variant="h6" gutterBottom>
                        5v5 Match
                      </Typography>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          A competitive experience, with fast balanced matches.
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      border: selectedQueueType === 'scrim' ? `2px solid ${theme.palette.secondary.main}` : '1px solid transparent',
                      backgroundColor: selectedQueueType === 'scrim' ? theme.palette.action.hover : 'transparent',
                      '&:hover': { backgroundColor: theme.palette.action.hover },
                      opacity: 0.6,
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                    onClick={() => {/* setSelectedQueueType('scrim') */}}
                  >
                    <CardContent sx={{ p: 1, pb: 0.5, display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <Typography variant="h6" gutterBottom>
                        5v5 Super Match
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1, maxWidth: '70%' }}>
                          Solo, duo, trio only • 400 Elo range • Veteran matching • Vote kick • Premium matching
                        </Typography>
                        <Button variant="contained" color="success" size="small">
                          UPGRADE
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}

          {activeTab === 'maps' && (
            <Box>
              <Grid container spacing={0.25}>
                {availableMaps.map((map) => (
                  <Grid item xs={3} sm={2.4} md={1.8} key={map}>
                    <Card
                      sx={{
                        cursor: 'pointer',
                        border: selectedMaps.includes(map) ? `2px solid ${theme.palette.secondary.main}` : '1px solid transparent',
                        backgroundColor: selectedMaps.includes(map) ? theme.palette.action.hover : 'transparent',
                        '&:hover': { backgroundColor: theme.palette.action.hover }
                      }}
                      onClick={() => toggleMap(map)}
                    >
                      <CardContent sx={{ p: 0.5, '&:last-child': { pb: 0.5 }, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ fontSize: '0.75rem', textAlign: 'center' }}>
                          {map}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              <Typography variant="caption" color={selectedMaps.length < 5 ? "error" : "text.secondary"} sx={{ mt: 1, mb: 0, display: 'block' }}>
                {selectedMaps.length < 5 ? `Select at least 5 maps to queue (${5 - selectedMaps.length} more needed)` : 'Map selection complete'}
              </Typography>
            </Box>
          )}

          {activeTab === 'servers' && (
            <Box>
              <Grid container spacing={0.25}>
                {availableServers.map((server) => (
                  <Grid item xs={3} sm={2.4} md={1.8} key={server}>
                    <Card
                      sx={{
                        cursor: 'pointer',
                        border: selectedServers.includes(server) ? `2px solid ${theme.palette.secondary.main}` : '1px solid transparent',
                        backgroundColor: selectedServers.includes(server) ? theme.palette.action.hover : 'transparent',
                        '&:hover': { backgroundColor: theme.palette.action.hover }
                      }}
                      onClick={() => toggleServer(server)}
                    >
                      <CardContent sx={{ p: 0.5, '&:last-child': { pb: 0.5 }, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ fontSize: '0.75rem', textAlign: 'center' }}>
                          {server.charAt(0).toUpperCase() + server.slice(1)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, mb: 0, display: 'block' }}>
                Select preferred servers. Leave empty to allow all servers.
              </Typography>
            </Box>
          )}
        </Box>
        
        {/* Minimal spacer to control gap above chatbox */}
        <Box sx={{ height: '1px' }} />
        
        {/* Chatbox Section - Fixed height to prevent expansion */}
        <Box sx={{ 
          position: 'absolute',
          bottom: theme.spacing(2),
          left: theme.spacing(0.5),
          right: theme.spacing(0.5),
          height: '24vh',
          display: 'flex', 
          flexDirection: 'column', 
          border: '1px solid grey', 
          borderRadius: '8px', 
          overflow: 'hidden',
          backgroundColor: theme.palette.background.paper
        }}>
          {/* Messages List */}
          <List sx={{ flexGrow: 1, overflowY: 'auto', p: 1 }}>
            {chatMessages.map((message, index) => (
              <ListItem key={index} sx={{ py: 0.1, minHeight: 'auto' }}>
                <ListItemText
                  primary={
                    <Typography variant="body2" sx={{ lineHeight: 1.2 }}>
                      [{new Date(message.timestamp).toLocaleTimeString()}] <strong>{message.user}</strong>: {message.message}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
            <div ref={messagesEndRef} />
          </List>
          
          {/* Message Input */}
          <Box sx={{ display: 'flex', p: 1, borderTop: '1px solid grey' }}>
            <TextField
              variant="outlined"
              fullWidth
              size="small"
              placeholder="Type a message..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  sendLobbyMessage();
                }
              }}
            />
            <Button onClick={sendLobbyMessage} sx={{ ml: 1 }} variant="contained">
              Send
            </Button>
          </Box>
        </Box>

        {/* Match Found Dialog - ESEA Style */}
        <Dialog 
          open={matchFound} 
          maxWidth="sm"
          PaperProps={{
            sx: { 
              backgroundColor: '#1a1a1a',
              border: '2px solid #333',
              borderRadius: '8px',
              minWidth: '400px',
              maxWidth: '450px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.8)'
            }
          }}
        >
          <DialogContent sx={{ p: 2, textAlign: 'center', position: 'relative' }}>
            {/* Close button */}
            <IconButton
              onClick={handleDeclineMatch}
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                color: '#888',
                '&:hover': {
                  color: '#fff',
                  backgroundColor: 'rgba(255,255,255,0.1)'
                }
              }}
            >
              ✕
            </IconButton>
            {/* Header */}
            <Box sx={{ mb: 2 }}>
              <Typography 
                variant="h5" 
                sx={{ 
                  color: '#fff',
                  fontWeight: 'bold',
                  fontFamily: '"Source Sans Pro", sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  mb: 0.5,
                  fontSize: '20px'
                }}
              >
                Match Ready
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#ccc',
                  fontFamily: '"Source Sans Pro", sans-serif',
                  fontSize: '13px'
                }}
              >
                Confirm your match
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#ccc',
                  fontFamily: '"Source Sans Pro", sans-serif',
                  mb: 0.5,
                  fontSize: '13px'
                }}
              >
                for the <span style={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>COMPETITIVE 5v5</span>
              </Typography>
            </Box>

            {/* Show different content based on user acceptance state */}
            {!userAccepted ? (
              <>
                {/* Countdown Timer with Gauge - Only show if user hasn't accepted */}
                <Box sx={{ mb: 1.5 }}>
                  <Box
                    sx={{
                      width: '52px',
                      height: '52px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto',
                      position: 'relative',
                      background: 'linear-gradient(135deg, rgba(212, 160, 255, 0.1) 0%, rgba(212, 160, 255, 0.05) 100%)'
                    }}
                  >
                    {/* Gauge Background Circle */}
                    <svg
                      width="52"
                      height="52"
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        transform: 'rotate(-90deg)'
                      }}
                    >
                      {/* Background circle */}
                      <circle
                        cx="26"
                        cy="26"
                        r="19"
                        fill="none"
                        stroke="rgba(212, 160, 255, 0.2)"
                        strokeWidth="3"
                      />
                      {/* Progress circle */}
                      <circle
                        cx="26"
                        cy="26"
                        r="19"
                        fill="none"
                        stroke={theme.palette.secondary.main}
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 19}`}
                        strokeDashoffset={`${2 * Math.PI * 19 * (1 - (timeLeft / 30))}`}
                        style={{
                          transition: 'stroke-dashoffset 0.5s ease-in-out'
                        }}
                      />
                    </svg>
                    <Typography 
                      variant="body1" 
                      sx={{ 
                        color: theme.palette.secondary.main,
                        fontWeight: 'bold',
                        fontFamily: '"Source Sans Pro", sans-serif',
                        fontSize: '19px',
                        zIndex: 1
                      }}
                    >
                      {timeLeft}
                    </Typography>
                  </Box>
                </Box>

                {/* Action Button - Only show if user hasn't accepted */}
                <Button
                  variant="contained"
                  onClick={handleAcceptMatch}
                  autoFocus
                  sx={{
                    backgroundColor: theme.palette.secondary.main,
                    color: '#000',
                    fontWeight: 'bold',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    fontFamily: '"Source Sans Pro", sans-serif',
                    fontSize: '12px',
                    px: 3,
                    py: 1,
                    borderRadius: '4px',
                    border: 'none',
                    boxShadow: '0 3px 8px rgba(212, 160, 255, 0.3)',
                    '&:hover': {
                      backgroundColor: '#c490ff',
                      boxShadow: '0 4px 12px rgba(212, 160, 255, 0.4)',
                    },
                    '&:active': {
                      transform: 'translateY(1px)',
                    }
                  }}
                >
                  Accept
                </Button>
              </>
            ) : (
              <>
                {/* Show acceptance progress when user has accepted */}
                <AcceptanceProgress />
                
                {/* Time remaining */}
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: theme.palette.secondary.main,
                    fontFamily: '"Source Sans Pro", sans-serif',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    mt: 1
                  }}
                >
                  {timeLeft}s remaining
                </Typography>
              </>
            )}
          </DialogContent>
        </Dialog>
      </Box>
    </Container>
  );
};

export default PugQueue;
