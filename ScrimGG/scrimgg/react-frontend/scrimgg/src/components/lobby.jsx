import React, { useState, useEffect } from 'react';
import { Box, Button, Container, Grid, Paper, Typography, Dialog, IconButton, Avatar, Chip, styled } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import { ColorModeContext, useMode } from '../theme';
import CrownIcon from '@mui/icons-material/EmojiEvents';
import PlayerRank from './rankwidget';
import RankComponent from './rankwidget';
import HorizontalBox from './selectbar';
import '../fonts/fonts.css';
import { lighten } from '@mui/material/styles';
import getRankAndProgress from "../utils/rankprog"


const CustomPaper = styled(Paper)(({ theme, hasPlayer }) => ({
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '300px',
  backgroundColor: theme.palette.primary, // Adjust to match your theme colors
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(2),
  // Add custom styling here to match the picture
  boxShadow: 'inset 0 0 10px #000',
  backgroundColor: hasPlayer ? theme.palette.primary.light : theme.palette.grey,
}));

const MapEditButton = styled(IconButton)(({ theme }) => ({
  // Add your styles for the button here
  color: theme.palette.common.white,
  marginLeft: theme.spacing(1),
}));

const MapsDisplay = styled(Box)(({ theme }) => ({
  // ... (other styles)
  backgroundColor: 'darkblue', // Example style to match ESEA client
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(1),
  color: 'white',
  // ... (add other styles to match the ESEA client)
}));

// Styled Avatar component
const StyledAvatar = styled(Avatar)(({ theme }) => ({
  width: theme.spacing(11),
  height: theme.spacing(11),
  marginBottom: theme.spacing(1),
  // Add border or other styles as needed
  border: `2px solid ${theme.palette.primary.main}`, // This adds a border around the Avatar
}));

// Styled Box for the leader crown icon
const LeaderCrown = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: theme.spacing(1),
  right: theme.spacing(1),
  // Additional styling to match your picture
}));


const Lobby = () => {
  const [lobbyid, setlobbyid] = useState([]);
  const [players, setPlayers] = useState([]); 
  const [selectedMaps, setSelectedMaps] = useState([]);
  const [selectedServers, setSelectedServers] = useState([]);
  const [isMapSelectionOpen, setIsMapSelectionOpen] = useState(false);

  useEffect(() => {
    // Define the function inside the effect
    const url = `http://127.0.0.1:8000/lobby/create/`; // Adjust port as necessary
    const fetchLobbyData = async () => {
      try {
        const response = await fetch(url, {
          method: 'POST', // or 'POST', depending on your backend setup
          headers: {
            'Content-Type': 'application/json',
            // Include other headers as required, like authentication tokens
          },
        });
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        console.log(data);
        console.log(data.players);
        console.log(data.players[0]);
        setPlayers(data.players);
        setlobbyid(data.id)
      } catch (error) {
        console.error('Failed to fetch lobby data:', error);
      }
    };

    fetchLobbyData();
  }, []);

  // Function to open map selection dialog
  const handleOpenMapSelection = () => {
    setIsMapSelectionOpen(true);
  };

  // Function to close map selection dialog
  const handleCloseMapSelection = () => {
    setIsMapSelectionOpen(false);
  };

  // Determine the leader after players state is set
  const leader = players.find(player => player?.isLeader);
  const handleInviteClick = (slot) => {
    console.log(`Invite for slot ${slot}`);
  };

  const handleEmptySlotClick = (slotIndex) => {
    console.log('Handle empty slot click');
    const url = `http://127.0.0.1:8000/lobby/invite/`; 
    const inviteplayer = async () => {
      try {
        const response = await fetch(url, {
          method: 'POST', 
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        console.log(data);
        console.log(data.players);
        console.log(data.players[0]);
        setPlayers(data.players);
      } catch (error) {
        console.error('Failed to fetch lobby data:', error);
      }
    }; 
  };

  const handlePlayClick = async () => {
    const lobbyData = {
      lobby: lobbyid,
      players: players, 
      selectedMaps: selectedMaps,
      selectedServers: selectedServers, 
    };
    const url = 'http://127.0.0.1:8000/matchmaking/queueup/';
    try {
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          // Include other headers as required, like authentication tokens
        },
        body: JSON.stringify(lobbyData),
      });
  
      if (!response.ok) {
        throw new Error('Failed to start game:', response.statusText);
      }
  
      const result = await response.json();
      console.log('Game started successfully:', result);
      // Handle any post-success actions here, e.g., navigating to a game page
    } catch (error) {
      console.error('Error starting game:', error);
    }
  };
  
  const handleMapDeselect = (mapToRemove) => {
    setSelectedMaps(selectedMaps.filter(map => map !== mapToRemove));
  };

  

  const PlayerSlot = ({ player, handleEmptySlotClick, slotIndex }) => {
    return (
      <CustomPaper hasPlayer={!!player}>
        {/* Check if player exists */}
        {player ? (
          <>
            {player.isLeader && <LeaderCrown><CrownIcon style={{ color: 'gold' }} /></LeaderCrown>}
            <StyledAvatar src={player.image || 'path/to/default/avatar'}/>
            <Typography variant="subtitle1" fontFamily={"Francker W01 Condensed Bold"} fontWeight={'bold'}>{player.alias}</Typography>
            <RankComponent style={{ marginBottom: '20px', transform: 'translateY(40px)' }} elo={player.elo} rank={player.rank} />
          </>
        ) : (
          <>
            <Typography variant="subtitle1"></Typography>
            <Button
              variant="contained"
              onClick={() => handleEmptySlotClick(slotIndex)}
              sx={{ mt: 2 }}
            >
              +
            </Button>
          </>
        )}
      </CustomPaper>
    );
  };

  // Dynamically determine the middle index based on the number of players
  const middleIndex = Math.max(0, Math.ceil((5 - players.length) / 2));

  const SelectedMapsDisplay = () => {
    return (
      <MapsDisplay onClick={handleOpenMapSelection}>
        {selectedMaps.length > 0 ? (
          selectedMaps.map((map, index) => (
            <Chip key={index} label={map} onDelete={() => handleMapDeselect(map)} />
          ))
        ) : (
          <Typography variant="body2" color="textSecondary">
            Select maps
          </Typography>
        )}
        <MapEditButton size="small" onClick={handleOpenMapSelection}>
          <EditIcon fontSize="inherit" />
        </MapEditButton>
      </MapsDisplay>
    );
  };

  const middlePlayerRank = players.length > 2 ? players[Math.floor(players.length / 2)].rank : null;
  const middlePlayerRankColor = middlePlayerRank ? getRankAndProgress(middlePlayerRank) : null;

  return (
    <Container maxWidth="md">
      <Typography variant="h4" align="center" gutterBottom>
        {leader ? `${leader.alias}'s Team` : 'Team'}
      </Typography>
      <Grid container spacing={2} justifyContent="center" alignItems="center">
        {Array.from({ length: 5 }).map((_, index) => {
          // Determine if the current index is within the range of filled slots
          const shouldFillSlot = index >= middleIndex && index < middleIndex + players.length;
          const player = shouldFillSlot ? players[index - middleIndex] : null;
          return <Grid item key={index} xs><PlayerSlot player={player} handleEmptySlotClick={handleEmptySlotClick} /></Grid>;
        })}
      </Grid>
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        mt: 4,
      }}>
      <Box sx={{ 
        display: 'flex', 
        flex:'1'}}>
        <HorizontalBox padding='10px' selectedMaps={selectedMaps}
        setSelectedMaps={setSelectedMaps}
        selectedServers={selectedServers}
        setSelectedServers={setSelectedServers} />
        </Box>
      <Box>
      <Button
        variant="contained"
        size="large"
        onClick={handlePlayClick}
        sx={{
          ml: 2,
          fontSize: '1.25rem',
          py: 1, 
          px: 6, 
          bgcolor: middlePlayerRankColor, // use the color from the middle player's rank
          color: (theme) => theme.palette.getContrastText(middlePlayerRankColor || theme.palette.primary.main),
          '&:hover': {
            bgcolor: middlePlayerRankColor ? lighten(middlePlayerRankColor, 0.2) : null,
          }
        }}
      >
    Play
  </Button>
      </Box>
      </Box>
    </Container>
  );
};
export default Lobby;