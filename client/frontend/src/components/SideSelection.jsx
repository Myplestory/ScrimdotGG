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
import { mapImageUrl } from '../utils/maps';

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

  // Map image resolver is provided by utils/maps.js

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
  
  // Debug logging
  console.log('🎮 [SIDE SELECTION COMPONENT] State:', {
    currentTurn,
    myTeam,
    isCaptain,
    isMyTurn,
    canSelectSide,
    finalMap
  });

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
          backgroundImage: `url(${mapImageUrl(finalMap)})`,
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
            backgroundColor: canSelectSide ? '#ff4444' : 'transparent', // Red background when clickable
            borderColor: '#ff4444', // Red border
            color: canSelectSide ? colors.grey[100] : '#ff4444', // White text when clickable, red when not
            '&:hover': {
              backgroundColor: canSelectSide ? '#cc0000' : 'rgba(255, 68, 68, 0.1)', // Darker red on hover
              borderColor: '#cc0000',
            },
            '&:disabled': {
              borderColor: colors.grey[600],
              color: colors.grey[600],
              backgroundColor: 'transparent'
            }
          }}
        >
          <Typography variant="body1" sx={{ 
            fontWeight: 'bold',
            color: 'inherit'
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
            backgroundColor: canSelectSide ? '#4444ff' : 'transparent', // Blue background when clickable
            borderColor: '#4444ff', // Blue border
            color: canSelectSide ? colors.grey[100] : '#4444ff', // White text when clickable, blue when not
            '&:hover': {
              backgroundColor: canSelectSide ? '#0000cc' : 'rgba(68, 68, 255, 0.1)', // Darker blue on hover
              borderColor: '#0000cc',
            },
            '&:disabled': {
              borderColor: colors.grey[600],
              color: colors.grey[600],
              backgroundColor: 'transparent'
            }
          }}
        >
          <Typography variant="body1" sx={{ 
            fontWeight: 'bold',
            color: 'inherit'
          }}>
            DEFEND
          </Typography>
        </Button>
      </Box>

      {/* Team Selector Indicator */}
      <Typography variant="body2" sx={{ 
        color: colors.grey[300],
        textAlign: 'center',
        mt: 1,
        fontWeight: canSelectSide ? 600 : 400
      }}>
        {currentTurn === 'team_a' ? 'Team A' : 'Team B'} select starting side
      </Typography>

      {/* Turn Indicator (only show if can't select) */}
      {!canSelectSide && (
        <Typography variant="caption" sx={{ 
          color: colors.grey[500],
          textAlign: 'center',
          mt: 0.5,
          fontSize: '0.7rem'
        }}>
          {isCaptain ? 'Waiting for opponent...' : 'Only captains can select sides'}
        </Typography>
      )}
    </Box>
  );
};

export default SideSelection;
