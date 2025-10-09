// src/components/Lobby/Lobby.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Box, Button, Container, Grid, Typography, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, TextField, List, ListItem, ListItemText } from '@mui/material';
import { styled } from '@mui/material/styles';
import { lighten } from '@mui/material/styles';
import { useWebSocket } from '../../contexts/WebSocketContext';

// Component imports
import '../../fonts/fonts.css';
import PlayerSlot from './playerslot';
import HorizontalBox from '../selectbar/selectbar';
import getRankAndProgress from '../../utils/rankprog'; 

const Lobby = () => {
  const [players, setPlayers] = useState([]); 
  const [currentPuuid, setCurrentPuuid] = useState(null);
  const [currentPlayer, setCurrentPlayer] = useState(null);
  const [selectedMaps, setSelectedMaps] = useState([]);
  const [selectedServers, setSelectedServers] = useState([]);
  const [isMapSelectionOpen, setIsMapSelectionOpen] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef(null);
  const [error, setError] = useState(null);

  // match found vars
  const [matchFound, setMatchFound] = useState(false);
  const [timeLeft, setTimeLeft] = useState(30);
  const [acceptedPlayers, setAcceptedPlayers] = useState(0);

  // Use WebSocket context
  const { lobbyData, chatMessages, queueStatus, matchData, api, on, playerData } = useWebSocket();
  
  // Extract lobby ID from lobby data
  const lobbyid = lobbyData?.id || null;

  // Determine the leader after players state is set
  const leader = players.find(player => player?.isLeader);

  // Sync lobby data from WebSocket to local state
  useEffect(() => {
    if (lobbyData) {
      const lobbyLeader = lobbyData.lobby_leader;
      const updatedPlayers = (lobbyData.players || []).map(player => ({
        ...player,
        isLeader: lobbyLeader && player.puuid === lobbyLeader.puuid,
      }));
      setPlayers(updatedPlayers);
      console.log('Lobby updated:', lobbyData);
    }
  }, [lobbyData]);

  // Set current player PUUID from player data
  useEffect(() => {
    if (playerData?.puuid) {
      setCurrentPuuid(playerData.puuid);
    }
  }, [playerData]);

  // Set current player from players list
  useEffect(() => {
    if (players.length > 0 && currentPuuid) {
      const player = players.find(p => p.puuid === currentPuuid);
      setCurrentPlayer(player || null);
    }
  }, [players, currentPuuid]);

  // Create lobby on mount
  useEffect(() => {
    console.log('Creating lobby...');
    api.createLobby();
  }, []); 

  // Listen for match found
  useEffect(() => {
    if (matchData?.requires_acceptance) {
      setMatchFound(true);
      // Calculate remaining time
      const deadline = new Date(matchData.acceptance_deadline);
      const now = new Date();
      const remaining = Math.max(0, Math.floor((deadline - now) / 1000));
      setTimeLeft(remaining);
    }
  }, [matchData]);

  // Countdown timer for match acceptance
  useEffect(() => {
    if (matchFound && timeLeft > 0) {
      const timer = setTimeout(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0 && matchFound) {
      // Auto-decline if time runs out
      handleDecline();
    }
  }, [matchFound, timeLeft]);

  // Auto-scroll chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  // Handle sending lobby message
  const sendLobbyMessage = () => {
    if (!newMessage.trim()) return;
    if (!lobbyid) {
      console.error("Lobby ID is missing! Cannot send the message.");
      return;
    }
    
    // Send via WebSocket
    api.sendLobbyMessage(newMessage.trim(), lobbyid);
    setNewMessage('');
  };

  const handlePlayClick = () => {
    if (!lobbyid) {
      setError('No lobby ID');
      return;
    }
    
    if (selectedMaps.length === 0 || selectedServers.length === 0) {
      setError('Please select at least one map and one server');
      return;
    }
    
    console.log('Queueing lobby with preferences:', { selectedMaps, selectedServers });
    api.queueLobby(selectedMaps, selectedServers);
  };

  const handleClose = () => setMatchFound(false);
  
  const handleAccept = () => {
    console.log('Match accepted.');
    if (matchData?.match_id) {
      api.acceptMatch(matchData.match_id);
    }
    setMatchFound(false);
  };

  const handleDecline = () => {
    console.log('Match declined.');
    if (matchData?.match_id) {
      api.declineMatch(matchData.match_id);
    }
    setMatchFound(false);
  };

  const handleEmptySlotClick = (slotIndex) => {
    console.log('Empty slot clicked:', slotIndex);
    // Implement invite logic when ready
  };

  const handleMapDeselect = (mapToRemove) => {
    setSelectedMaps(selectedMaps.filter(map => map !== mapToRemove));
  };

  // Dynamically determine the middle index based on the number of players
  const middleIndex = Math.max(0, Math.ceil((5 - players.length) / 2));

  const middlePlayerRank = players.length > 2 ? players[Math.floor(players.length / 2)].rank : null;
  const middlePlayerRankColor = middlePlayerRank ? getRankAndProgress(middlePlayerRank) : null;

  return (
    <Container maxWidth="md">
      <Typography variant="h4" align="center" gutterBottom sx={{ pt: 1 }}>
        {leader ? `${leader.alias}'s Team` : 'Team'}
      </Typography>
      
      {/* Queue Status Indicator */}
      {queueStatus.in_queue && (
        <Typography variant="body2" align="center" color="primary" sx={{ mb: 1 }}>
          🔍 In Queue... Estimated wait: {queueStatus.estimated_wait}s
        </Typography>
      )}
      
      <Grid container spacing={2} justifyContent="center" alignItems="center"   
        sx={{
          mt: -2, 
          mb: 1,
        }}>
        {Array.from({ length: 5 }).map((_, index) => {
          // Determine if the current index is within the range of filled slots
          const shouldFillSlot = index >= middleIndex && index < middleIndex + players.length;
          const player = shouldFillSlot ? players[index - middleIndex] : null;
          return (
            <Grid item key={player ? player.puuid : `empty-${index}`} xs>
              <PlayerSlot player={player} handleEmptySlotClick={handleEmptySlotClick} slotIndex={index} />
            </Grid>
          );
        })}
      </Grid>
      
      {/* Match Found Dialog */}
      <Dialog open={matchFound} onClose={handleClose}>
        <DialogTitle>Match Found!</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Map: {matchData?.map || 'Unknown'}<br />
            Server: {matchData?.server || 'Unknown'}<br />
            <strong>You have {timeLeft} seconds to accept the match.</strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDecline} color="error">
            Decline
          </Button>
          <Button onClick={handleAccept} variant="contained" color="success" autoFocus>
            Accept Match
          </Button>
        </DialogActions>
      </Dialog>
      
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        mt: 4,
        mt: 1,
        mb: 1,
      }}>
        <Box sx={{ 
          display: 'flex', 
          flex: '1'
        }}>
          <HorizontalBox 
            padding='10px' 
            selectedMaps={selectedMaps}
            setSelectedMaps={setSelectedMaps}
            selectedServers={selectedServers}
            setSelectedServers={setSelectedServers} 
          />
        </Box>
        <Box>
          <Button
            variant="contained"
            size="large"
            onClick={handlePlayClick}
            disabled={queueStatus.in_queue}
            sx={{
              ml: 2,
              fontSize: '1.25rem',
              py: 1, 
              px: 6, 
              bgcolor: middlePlayerRankColor,
              color: (theme) => theme.palette.getContrastText(middlePlayerRankColor || theme.palette.primary.main),
              '&:hover': {
                bgcolor: middlePlayerRankColor ? lighten(middlePlayerRankColor, 0.2) : null,
              }
            }}
          >
            {queueStatus.in_queue ? 'In Queue...' : 'Q'}
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Typography color="error" align="center" sx={{ mt: 1 }}>
          {error}
        </Typography>
      )}
      
      {/* Chatbox Section */}
      <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', height: '25vh', border: '1px solid grey', borderRadius: '8px', overflow: 'hidden', mt: 1, }}>
        {/* Messages List */}
        <List sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
          {chatMessages
            .filter(msg => msg.type === 'lobby')
            .map((message, index) => (
            <ListItem key={index}>
              <ListItemText
                primary={
                  <Typography variant="body2">
                    [{new Date(message.timestamp).toLocaleTimeString()}] <strong>{message.user}</strong>: {message.message}
                  </Typography>
                }
                sx={{
                  margin: -1,
                }}
              />
            </ListItem>
          ))}
          {/* Auto-scroll target */}
          <div ref={messagesEndRef} />
        </List>
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
    </Container>
  );
};

export default Lobby;
