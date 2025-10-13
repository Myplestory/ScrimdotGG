import React from 'react';
import { Box, Typography } from '@mui/material';
import { Gauge } from '@mui/x-charts/Gauge';
import getRankAndProgress from '../utils/rankprog';

const SimpleRankGauge = ({ elo, size = 36 }) => {
  const { rank, progress } = getRankAndProgress(elo);
  
  const getColorForRank = (rank) => {
    switch (rank) {
      case 'S': return '#7bb3d9'; // Brighter blue
      case 'G': return '#d63851'; // Brighter red
      case 'A+':
      case 'A':
      case 'A-': return '#f5d842'; // Brighter yellow
      case 'B+':
      case 'B':
      case 'B-': return '#c5c5c5'; // Brighter silver
      case 'C+':
      case 'C':
      case 'C-': return '#d4a017'; // Brighter bronze
      case 'D+':
      case 'D':
      case 'D-': return '#7dd321'; // Brighter green
      default: return '#FFFFFF';
    }
  };

  const rankColor = getColorForRank(rank);

  return (
    <Box sx={{ 
      position: 'relative', 
      width: size, 
      height: size,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Gauge
        value={progress}
        size={size}
        thickness={3}
        startAngle={-140}
        endAngle={140}
        outerRadius={size / 2 - 2}
        innerRadius={size / 2 - 5}
        sx={{
          '& .MuiGauge-valueArc': {
            stroke: rankColor,
            strokeWidth: 3,
            opacity: 1,
          },
          '& .MuiGauge-referenceArc': {
            stroke: 'rgba(255, 255, 255, 0.1)',
            strokeWidth: 3,
          },
          '& .MuiGauge-valueText': {
            display: 'none',
          }
        }}
      />
      <Typography
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: rankColor,
          fontWeight: 'bold',
          fontSize: '0.8rem',
          fontFamily: "Enamela W01 Condensed Medium",
          zIndex: 1,
          textShadow: `0 0 4px ${rankColor}40`,
          lineHeight: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {rank}
      </Typography>
    </Box>
  );
};

export default SimpleRankGauge;
