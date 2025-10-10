import React from 'react';
import { Typography, Button } from '@mui/material';
import { styled } from '@mui/material/styles';
import Icon from '@mdi/react';
import { mdiCrown } from '@mdi/js';
import { Box, Avatar, Paper } from '@mui/material';
import RankComponent from '../rankwidget/rankwidget'; 

// Styled Components
const CustomPaper = styled(Paper)(({ theme, hasPlayer }) => ({
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '260px',
  backgroundColor: hasPlayer ? theme.palette.primary.dark : theme.palette.dark, // Use a darker color
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(1),
  boxShadow: hasPlayer
    ? 'inset 0 0 10px rgba(0, 0, 0, 0.5)' // Add a subtle dark shadow
    : 'inset 0 0 10px rgba(255, 255, 255, 0.1)', // Subtle light shadow for empty slots
  color: theme.palette.common.white, // Ensure text is readable on dark backgrounds
}));

const StyledAvatar = styled(Avatar)(({ theme }) => ({
  width: theme.spacing(14),
  height: theme.spacing(14),
  marginBottom: theme.spacing(0.5),
  border: `2px solid ${theme.palette.primary.main}`,
}));

const LeaderCrown = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: theme.spacing(2.75),
  left: '50%',
  transform: 'translateX(-50%)',
  zIndex: 10,
}));

const PlayerSlot = ({ player, handleEmptySlotClick, slotIndex }) => {
  return (
    <CustomPaper hasPlayer={!!player}>
      {/* Check if player exists */}
      {player ? (
        <>
          {player.isLeader && (
            <LeaderCrown>
              <Icon path={mdiCrown} size={0.6} color="gold" />
            </LeaderCrown>
          )}
          <Box sx={{ mt: 0.75, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <StyledAvatar src={player.profile_picture || 'https://www.mn.uio.no/geo/english/services/it/help/using-linux/bilder/bash_logo.jpg'} alt={`${player.alias}'s avatar`} />
            <Typography variant="subtitle2" fontFamily={"Francker W01 Condensed Bold"} fontWeight={'bold'} sx={{ mb: 1.5, fontSize: '0.75rem' }}>
              {player.alias || 'Unknown Player'}
            </Typography>
            <RankComponent 
              style={{ marginBottom: '20px', transform: 'translateY(0px)' }} 
              elo={player.elo || 0} 
              rank={player.rank || 'Unranked'} 
            />
          </Box>
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

export default PlayerSlot;