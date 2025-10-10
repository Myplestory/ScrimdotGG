// PugQueue.jsx - Main PUG queue screen (FACEIT-like)
import React, { useState, useEffect, useRef } from 'react';
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
  const [queueStatus, setQueueStatus] = useState({
    in_queue: false,
    queue_type: null,
    estimated_wait: 0,
    players_in_queue: 0
  });
  const [matchFound, setMatchFound] = useState(false);
  const [matchData, setMatchData] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30);
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
  const { playerData, api, on, reconnect, connected } = useWebSocket();

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
      setMatchFound(true);
      setMatchData(payload);
      setTimeLeft(payload.accept_deadline || 30);
    });

    const unsubscribeLobbyMessage = on('lobby_message', (payload) => {
      setChatMessages(prev => [...prev, payload]);
    });

    return () => {
      unsubscribeQueueJoined();
      unsubscribeQueueLeft();
      unsubscribeMatchFound();
      unsubscribeLobbyMessage();
    };
  }, [on]);

  // Countdown timer for match acceptance
  useEffect(() => {
    if (matchFound && timeLeft > 0) {
      const timer = setTimeout(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
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
  useEffect(() => {
    let interval;
    if (queueStatus.in_queue && queueStartTime) {
      interval = setInterval(() => {
        // Force re-render to update timer display
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
    }
    setMatchFound(false);
  };

  const handleDeclineMatch = () => {
    if (matchData?.match_id) {
      api.declineMatch(matchData.match_id);
    }
    setMatchFound(false);
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

  return (
    <Container maxWidth="md" sx={{ height: '100%', overflow: 'hidden' }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          backgroundColor: theme.palette.background.dark,
          padding: theme.spacing(2),
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Header */}
        <Typography variant="h4" align="center" gutterBottom sx={{ color: theme.palette.secondary.main }}>
          {getQueueTitle()}
        </Typography>
        
        
        {/* Player Cards Section */}
        <Grid container spacing={1.5} justifyContent="center" alignItems="center" sx={{ mt: -2, mb: 1 }}>
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
              <Grid item key={player ? player.puuid : `empty-${index}`} xs>
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
          mt: 2,
          mb: 1,
          p: 1.5,
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

          {/* Right side - Connection Status and Find Match Button */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* Connection Status Indicator */}
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: connected ? theme.palette.success.main : theme.palette.error.main,
                cursor: !connected ? 'pointer' : 'default'
              }}
              title={connected ? 'Connected to backend' : 'Disconnected - Click to reconnect'}
              onClick={() => {
                if (!connected) {
                  console.log('Manual reconnect triggered');
                  reconnect();
                }
              }}
            />
            
            <Button
              variant="contained"
              size="medium"
              onClick={handleFindMatch}
              disabled={selectedMaps.length < 5 || !isPartyLeader() || !connected}
              sx={{
                fontSize: '1rem',
                py: 0.75, 
                px: 4, 
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
              {queueStatus.in_queue ? `CANCEL QUEUE (${getQueueTime()})` : 'FIND MATCH'}
            </Button>
          </Box>
        </Box>

        {/* Tab Content */}
        <Box sx={{ mb: 0.5, minHeight: 'auto', backgroundColor: theme.palette.background.paper, borderRadius: 1, p: 1.5, pb: 1 }}>
          {activeTab === 'match_type' && (
            <Box>
              <Typography variant="h6" sx={{ mb: 1.5 }}>
                Match Type
              </Typography>
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
              <Typography variant="h6" sx={{ mb: 1.5 }}>
                Map Selection
              </Typography>
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
              <Typography variant="h6" sx={{ mb: 1.5 }}>
                Server Selection
              </Typography>
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
          bottom: theme.spacing(1),
          left: theme.spacing(2),
          right: theme.spacing(2),
          height: activeTab === 'servers' ? '25vh' : '20vh',
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

        {/* Match Found Dialog */}
        <Dialog 
          open={matchFound} 
          maxWidth="md" 
          fullWidth
          PaperProps={{
            sx: { backgroundColor: theme.palette.background.paper }
          }}
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Star sx={{ mr: 1, color: theme.palette.secondary.main }} />
              Match Found!
            </Box>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {formatTime(timeLeft)}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Accept the match to continue
              </Typography>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Paper sx={{ p: 2, backgroundColor: theme.palette.action.hover }}>
                  <Typography variant="h6" color="primary" gutterBottom>
                    Team A
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average ELO: {matchData?.average_elo || 'Unknown'}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6}>
                <Paper sx={{ p: 2, backgroundColor: theme.palette.action.hover }}>
                  <Typography variant="h6" color="error" gutterBottom>
                    Team B
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average ELO: {matchData?.average_elo || 'Unknown'}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Players in match: {matchData?.players?.length || 10}
              </Typography>
            </Box>
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button
              variant="outlined"
              color="error"
              onClick={handleDeclineMatch}
              sx={{ mr: 1 }}
            >
              Decline
            </Button>
            <Button
              variant="contained"
              color="success"
              onClick={handleAcceptMatch}
              autoFocus
            >
              Accept Match
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Container>
  );
};

export default PugQueue;
