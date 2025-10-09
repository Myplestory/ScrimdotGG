import React from 'react';
import { Card, CardContent, Typography, Avatar, Box } from '@mui/material';
import { styled, useTheme } from '@mui/material/styles';
import RankComponent from '../rankwidget/rankwidget'; // Adjust the path if needed

const StyledCard = styled(Card)(({ theme }) => ({
  backgroundColor: theme.palette.background.dark, // Changed to dark grey
  color: theme.palette.text.primary,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(5),
  borderRadius: theme.shape.borderRadius,
  boxShadow: '0 4px 10px rgba(0, 0, 0, 0.5)', // Subtle shadow for better contrast
  height: '100%', // Ensure the card fills the height of its container
  width: '100%', // Ensure the card fills the width of its container
}));

const StyledAvatar = styled(Avatar)(({ theme }) => ({
  width: theme.spacing(13),
  height: theme.spacing(13),
  marginBottom: theme.spacing(1),
  border: `2px solid ${theme.palette.primary.light}`,
}));

const StyledTypography = styled(Typography)(({ theme }) => ({
  marginBottom: theme.spacing(2), // Add spacing below the typography
}));

const PlayerInfoCard = ({ player }) => {
  const theme = useTheme();
  return (
    <StyledCard>
      <StyledAvatar src={player.profile_picture || 'path/to/default/avatar.png'} />
        <StyledTypography
          variant="h5" // Increased the variant for larger text
          fontWeight="bold"
          sx={{
            fontSize: '1.25rem',
            marginBottom: theme.spacing(2),
            marginTop: theme.spacing(1),
          }}
        >
          {player.alias || 'Player Name'}
        </StyledTypography>
      <Box
        sx={{
          marginTop: theme.spacing(2),
          transform: 'scale(1.25)', // Scale up the RankComponent
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <RankComponent elo={player.elo || 0} rank={player.rank || 'Unranked'} />
      </Box>
    </StyledCard>
  );
};

export default PlayerInfoCard;