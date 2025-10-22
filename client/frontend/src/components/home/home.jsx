import React, { useState, useEffect } from 'react';
import { Grid, Paper, Box, Typography, Link, CircularProgress, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import Chart from '../chart';
import { useMode } from '../../theme';
import PlayerInfoCard from '../home/playerinfo';
import { useWebSocket } from '../../contexts/WebSocketContext';

function Copyright(props) {
  return (
    <Typography variant="body2" color="text.secondary" align="center" {...props}>
      {'Copyright © '}
      <Link color="inherit" href="https://mui.com/">
        Your Website
      </Link>{' '}
      {new Date().getFullYear()}
      {'.'}
    </Typography>
  );
}

const HomeComponent = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [theme, colorMode] = useMode();
  const navigate = useNavigate();
  
  // Use WebSocket context
  const { playerData, api, on } = useWebSocket();

  useEffect(() => {
    // Request player data if not already loaded
    if (!playerData) {
      console.log('Fetching player data...');
      api.getPlayerData();
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Update loading state when player data is received
    if (playerData) {
      setLoading(false);
    }
  }, [playerData]);

  // Listen for errors
  useEffect(() => {
    const unsubscribe = on('error', (payload) => {
      setError(payload.message || 'An error occurred');
      setLoading(false);
    });
    
    return unsubscribe;
  }, [on]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
        backgroundColor: theme.palette.background.dark,
        padding: theme.spacing(3),
        boxSizing: 'border-box',
      }}
    >
      <Grid container spacing={3}>
        {/* Chart Section */}
        <Grid item xs={12} md={8} lg={9}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 240,
              width: '100%',
              transition: 'transform 0.3s ease, box-shadow 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: `0 8px 24px ${theme.palette.secondary.dark}20`,
              },
            }}
          >
            <Chart />
          </Paper>
        </Grid>

        {/* Player Info Card */}
        <Grid item xs={12} md={4} lg={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '70vh',
              backgroundColor: theme.palette.background.paper,
              boxShadow: '0 4px 10px rgba(0, 0, 0, 0.3)',
              borderRadius: '12px',
              transition: 'transform 0.3s ease, box-shadow 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: `0 8px 24px ${theme.palette.secondary.dark}20`,
              },
            }}
          >
            {playerData ? (
              <PlayerInfoCard player={playerData} />
            ) : (
              <Typography color="error">{error || 'No player data available'}</Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Test Button for MatchPage Preview */}
        <Grid item xs={12}>
          <Paper 
            sx={{ 
              p: 2, 
              textAlign: 'center',
              transition: 'transform 0.3s ease, box-shadow 0.3s ease',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: `0 6px 20px ${theme.palette.secondary.dark}15`,
              },
            }}
          >
            <Typography variant="h6" gutterBottom>
              🎮 Development Preview
            </Typography>
            <Button 
              variant="contained" 
              color="secondary"
              onClick={() => navigate('/match/test-preview')}
              sx={{ 
                mt: 1,
                transition: 'transform 0.2s ease',
                '&:hover': {
                  transform: 'scale(1.05)',
                },
              }}
            >
              Preview MatchPage Design
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Footer */}
      <Copyright sx={{ pt: 4 }} />
    </Box>
  );
};

export default HomeComponent;

