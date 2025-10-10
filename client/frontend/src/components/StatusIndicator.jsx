import React from 'react';
import { Typography } from '@mui/material';

const StatusIndicator = ({ connected, systemStatus, queueStatus = { in_queue: false }, gameState = { status: 'disconnected' }, position = 'bottom-left' }) => {
  // Determine the position styling
  const positionStyles = {
    'bottom-left': {
      position: 'absolute',
      bottom: '16px',
      left: '16px',
    },
    'bottom-right': {
      position: 'absolute',
      bottom: '16px',
      right: '16px',
    }
  };

  // Get the current status text and color
  const getStatusInfo = () => {
    // First check backend connection
    if (!connected) {
      return { text: '🔴 Backend Disconnected', color: '#f44336' };
    }

    // Check if systemStatus is available
    if (!systemStatus || !systemStatus.valorant) {
      return { text: '🔍 Checking Game Status...', color: '#2196f3' };
    }

    // Check game status
    if (systemStatus.valorant.status === 'running') {
      // Game is connected, check additional states
      if (queueStatus.in_queue) {
        return { text: '🟢 In Queue', color: '#4caf50' };
      } else if (gameState.status === 'in_match') {
        return { text: '🟢 In Match', color: '#4caf50' };
      } else if (gameState.status === 'in_pregame') {
        return { text: '🟢 In Game Lobby', color: '#4caf50' };
      } else if (gameState.status === 'in_party') {
        return { text: '🟢 In Party', color: '#4caf50' };
      } else {
        return { text: '🟢 Game Connected', color: '#4caf50' };
      }
    } else if (systemStatus.valorant.status === 'riot_only') {
      return { text: '🟡 Valorant not launched', color: '#ff9800' };
    } else if (systemStatus.valorant.status === 'not_running') {
      return { text: '🔴 Riot Client Not Running', color: '#f44336' };
    } else if (systemStatus.valorant.status === 'error') {
      return { text: '🔴 Status Check Error', color: '#f44336' };
    } else {
      return { text: '🔍 Checking Game Status...', color: '#2196f3' };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <Typography 
      variant="body2" 
      sx={{ 
        ...positionStyles[position],
        fontSize: '0.75rem',
        zIndex: 1000,
      }}
    >
      <span style={{ color: statusInfo.color }}>{statusInfo.text}</span>
    </Typography>
  );
};

export default StatusIndicator;
