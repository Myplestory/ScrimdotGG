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

      {/* Side Selection Buttons - Only show for team that can select */}
      {canSelectSide ? (
        <Box sx={{ 
          display: 'flex', 
          gap: 2, 
          width: '100%',
          justifyContent: 'center'
        }}>
          <Button
            variant="contained"
            onClick={() => handleSideSelect('attack')}
            sx={{
              flex: 1,
              py: 0.75,
              px: 2,
              minHeight: 'auto',
              backgroundColor: '#ff4444',
              borderColor: '#ff4444',
              color: colors.grey[100],
              '&:hover': {
                backgroundColor: '#cc0000',
                borderColor: '#cc0000',
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
            variant="contained"
            onClick={() => handleSideSelect('defend')}
            sx={{
              flex: 1,
              py: 0.75,
              px: 2,
              minHeight: 'auto',
              backgroundColor: '#4444ff',
              borderColor: '#4444ff',
              color: colors.grey[100],
              '&:hover': {
                backgroundColor: '#0000cc',
                borderColor: '#0000cc',
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
      ) : (
        <Typography variant="body2" sx={{ 
          color: colors.grey[400],
          textAlign: 'center',
          mt: 2,
          fontStyle: 'italic'
        }}>
          {isCaptain ? 'Waiting for opponent to select...' : 'Waiting for captain to select...'}
        </Typography>
      )}

      {/* Team Selector Indicator */}
      <Typography variant="body2" sx={{ 
        color: colors.grey[300],
        textAlign: 'center',
        mt: 1,
        fontWeight: canSelectSide ? 600 : 400
      }}>
        {currentTurn === 'team_a' ? 'Team A' : 'Team B'} selecting starting side
      </Typography>
    </Box>
  );
};

export default SideSelection;
