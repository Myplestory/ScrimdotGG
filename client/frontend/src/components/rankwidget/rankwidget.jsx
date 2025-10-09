import React from 'react';
import { Box, styled, Typography } from '@mui/material';
import { borderRadius } from '@mui/system';
import { Gauge, gaugeClasses } from '@mui/x-charts/Gauge';
import  getRankAndProgress  from "../../utils/rankprog";
import '../../fonts/fonts.css';


// Define a styled container for the rank and progress
const RankContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'relative', 
  borderRadius: 100,
  overflow: 'hidden',
}));

const getColorForRank = (rank) => {
  switch (rank) {
    case 'S':
      return '#629ec5'; 
    case 'G':
      return '#b82a3d'; 
    case 'A+':
      return '#e8c83c'; 
    case 'A':
      return '#e8c83c';
    case 'A-':
      return '#e8c83c';  
    case 'B+':
      return '#ababab';
    case 'B':
      return '#ababab';
    case 'B-':
      return '#ababab';
    case 'C+':
      return '#c08b12';
    case 'C':
      return '#c08b12';
    case 'C-':
      return '#c08b12';
    case 'D+':
      return '#69bc00';
    case 'D':
      return '#69bc00'
    case 'D-':
      return '#69bc00'
    default:
      return '#FFFFFF'; // White color for undefined ranks
  }
};

// Adjust your RankCharacter styled component
const RankCharacter = styled(Typography)(({ theme, rank }) => ({
  position: 'absolute',
  top: '53%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  color: getColorForRank(rank),
  fontWeight: 'bold',
  fontSize: '1rem', 
  fontFamily: "Enamela W01 Condensed Medium",
  zIndex: 1,
}));

// Styled Typography for the ELO number
const EloTypography = styled(Typography)(({ theme }) => ({
  position: 'relative', 
  bottom: '0%', 
  left: '-27%', 
  marginLeft: theme.spacing(2),
  color: '',
  fontSize: '110%',
  fontFamily: "Enamela W01 Condensed Medium",
  fontWeight: 'lighter',
}));


// Define the RankComponent
const RankComponent = ({ elo, style }) => {
  const { rank, progress } = getRankAndProgress(elo);
  // The progress value should be a number between 0 and 100
  const rankColor = getColorForRank(rank);

  return (
    <Box style={{ ...style }} sx={{ 
        position: 'relative',
        display: 'flex',
        disableShrink:'true', 
        overflow: 'hidden',
        borderRadius: '150px',
        width: '90px', 
        height: '40px',
        bgcolor: 'background.paper'
      }}>
      <Box sx={{ 
        position: 'relative',
        width: '50%', 
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transform: 'translateX(3px)'
        }}>
        <Gauge
          value={progress}
          size={100}
          thickness={5}
          startAngle={-140}
          endAngle={140}
          outerRadius={16}
          innerRadius={12}
          sx={{
            '& .MuiGauge-root': {
              margin:'-100px',
            },
            '& .MuiGauge-valueArc': {
              stroke: rankColor,
            },
            '& .MuiGauge-valueText': {
              display: 'none',
              fontSize: '50%',
            }
          }}
        />
    <RankCharacter variant="caption" rank={rank}>{rank}</RankCharacter>
    </Box>
    <Box sx={{ 
        width: '50%', // Set the width to 50% of the parent container
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center' // Center the ELO typography horizontally
      }}>
        <EloTypography variant="caption">{elo.toLocaleString()}</EloTypography>
      </Box>
    </Box>
  );
};

export default RankComponent;
