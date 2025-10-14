import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Avatar,
  useTheme
} from '@mui/material';
import { tokens } from '../theme';

const SideSelection = ({ 
  finalMap, 
  serverLocation, 
  isCaptain, 
  myTeam, 
  currentTurn, 
  onSideSelect,
  timeLeft
}) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  // Map images mapping
  const mapImages = {
    'Bind': '/maps/bind.jpg',
    'Haven': '/maps/haven.jpg', 
    'Split': '/maps/split.jpg',
    'Ascent': '/maps/ascent.jpg',
    'Icebox': '/maps/icebox.jpg',
    'Breeze': '/maps/breeze.jpg',
    'Fracture': '/maps/fracture.jpg',
    'Pearl': '/maps/pearl.jpg',
    'Lotus': '/maps/lotus.jpg',
    'Sunset': '/maps/sunset.jpg'
  };

  // Server location flags mapping
  const serverFlags = {
    'US-East': '🇺🇸',
    'US-West': '🇺🇸', 
    'EU-West': '🇪🇺',
    'EU-East': '🇪🇺',
    'Asia-Pacific': '🌏',
    'Brazil': '🇧🇷',
    'Korea': '🇰🇷',
    'Japan': '🇯🇵'
  };

  const isMyTurn = currentTurn === myTeam && isCaptain;
  const canSelectSide = isMyTurn;

  const handleSideSelect = (side) => {
    if (canSelectSide) {
      console.log(`[SIDE SELECTION] Selecting ${side} side`);
      console.log(`[SIDE SELECTION] Current turn: ${currentTurn}, My team: ${myTeam}, Is captain: ${isCaptain}`);
      onSideSelect(side);
    } else {
      console.log(`[SIDE SELECTION] Cannot select side - not captain or not my turn`);
      console.log(`[SIDE SELECTION] Current turn: ${currentTurn}, My team: ${myTeam}, Is captain: ${isCaptain}`);
    }
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      gap: 2,
      width: '100%',
      maxWidth: 400,
      mx: 'auto'
    }}>
      {/* Timer (like veto) */}
      {typeof timeLeft === 'number' && (
        <Box sx={{ mb: 1 }}>
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
            <Typography variant="body2" sx={{ color: colors.grey[100], fontWeight: 600, fontSize: '0.8rem' }}>
              {String(Math.max(0, timeLeft)).padStart(2, '0')}s
            </Typography>
          </Box>
        </Box>
      )}
      {/* Server Location Card */}
      <Card sx={{ 
        width: '100%',
        backgroundColor: colors.grey[800],
        border: `1px solid ${colors.grey[600]}`,
        borderRadius: 2
      }}>
        <CardContent sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 2,
          py: 1.5,
          px: 2
        }}>
          <Avatar sx={{ 
            width: 24, 
            height: 16, 
            fontSize: '12px',
            backgroundColor: 'transparent'
          }}>
            {serverFlags[serverLocation] || '🌍'}
          </Avatar>
          <Typography variant="body2" sx={{ 
            color: colors.grey[100],
            fontWeight: 500
          }}>
            {serverLocation || 'US-East'}
          </Typography>
        </CardContent>
      </Card>

      {/* Map Card */}
      <Card sx={{ 
        width: '100%',
        backgroundColor: colors.grey[800],
        border: `1px solid ${colors.grey[600]}`,
        borderRadius: 2,
        overflow: 'hidden'
      }}>
        <Box sx={{ 
          position: 'relative',
          height: 120,
          backgroundImage: `url(${mapImages[finalMap] || '/maps/default.jpg'})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {/* Dark overlay for better text readability */}
          <Box sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.4)'
          }} />
          
          <Typography variant="h5" sx={{ 
            color: colors.grey[100],
            fontWeight: 'bold',
            textShadow: '2px 2px 4px rgba(0,0,0,0.8)',
            zIndex: 1
          }}>
            {finalMap}
          </Typography>
        </Box>
      </Card>

      {/* Side Selection Buttons */}
      <Box sx={{ 
        display: 'flex', 
        gap: 2, 
        width: '100%',
        justifyContent: 'center'
      }}>
        <Button
          variant={canSelectSide ? "contained" : "outlined"}
          onClick={() => handleSideSelect('attack')}
          disabled={!canSelectSide}
          sx={{
            flex: 1,
            py: 0.75, // Reduced height by half (was 1.5)
            px: 2,
            minHeight: 'auto',
            backgroundColor: canSelectSide ? theme.palette.primary.main : 'transparent',
            borderColor: theme.palette.primary.main,
            color: canSelectSide ? colors.grey[900] : theme.palette.primary.main,
            '&:hover': {
              backgroundColor: canSelectSide ? theme.palette.primary.dark : 'transparent',
              borderColor: theme.palette.primary.dark,
            },
            '&:disabled': {
              borderColor: colors.grey[600],
              color: colors.grey[600]
            }
          }}
        >
          <Typography variant="body1" sx={{ 
            fontWeight: 'bold',
            color: canSelectSide ? colors.grey[900] : '#ff4444' // Red for attack
          }}>
            ATTACK
          </Typography>
        </Button>

        <Button
          variant={canSelectSide ? "contained" : "outlined"}
          onClick={() => handleSideSelect('defend')}
          disabled={!canSelectSide}
          sx={{
            flex: 1,
            py: 0.75, // Reduced height by half (was 1.5)
            px: 2,
            minHeight: 'auto',
            backgroundColor: canSelectSide ? theme.palette.secondary.main : 'transparent',
            borderColor: theme.palette.secondary.main,
            color: canSelectSide ? colors.grey[900] : theme.palette.secondary.main,
            '&:hover': {
              backgroundColor: canSelectSide ? theme.palette.secondary.dark : 'transparent',
              borderColor: theme.palette.secondary.dark,
            },
            '&:disabled': {
              borderColor: colors.grey[600],
              color: colors.grey[600]
            }
          }}
        >
          <Typography variant="body1" sx={{ 
            fontWeight: 'bold',
            color: canSelectSide ? colors.grey[900] : '#4444ff' // Blue for defend
          }}>
            DEFEND
          </Typography>
        </Button>
      </Box>

      {/* Turn Indicator */}
      {!canSelectSide && (
        <Typography variant="body2" sx={{ 
          color: colors.grey[400],
          textAlign: 'center',
          mt: 1
        }}>
          {isCaptain ? `Waiting for ${currentTurn === 'team_a' ? 'Team B' : 'Team A'} to select side...` : 'Only captains can select sides'}
        </Typography>
      )}
    </Box>
  );
};

export default SideSelection;
