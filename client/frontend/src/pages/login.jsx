// AuthenticationScreen.jsx
import React, { useState, useEffect } from 'react';
import { ColorModeContext, useMode } from "../theme";
import { Box, Button, Container, CssBaseline, Typography, CircularProgress, FormControl, InputLabel, Select, MenuItem } from "@mui/material";
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../contexts/WebSocketContext';

function onlyLettersAndNumbers(str) {
  return /^[A-Za-z0-9]*$/.test(str);
}

const AuthenticationScreen = ({ onAuthentication }) => {
  const [username, setusername] = useState('');
  const [password, setpassword] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('na');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [authTimeout, setAuthTimeout] = useState(null);
  const [theme, colorMode] = useMode();
  const navigate = useNavigate();
  
  // Use WebSocket context
  const { connected, authenticated, systemStatus, api, on } = useWebSocket();

  // Listen for authentication success
  useEffect(() => {
    if (authenticated) {
      console.log('✅ Authentication successful');
      onAuthentication(true);
      setLoading(false);
    }
  }, [authenticated, onAuthentication]);

  // Register event listener for authentication errors
  useEffect(() => {
    const unsubscribe = on('authentication_error', (payload) => {
      setError(payload.message || 'Authentication failed');
      setLoading(false);
      
      // Clear any existing timeout
      if (authTimeout) {
        clearTimeout(authTimeout);
      }
      
      // Set timeout for retry if specified
      if (payload.timeout) {
        const timeoutId = setTimeout(() => {
          setError('');
          setLoading(false);
        }, payload.timeout * 1000);
        setAuthTimeout(timeoutId);
      }
    });
    
    return () => {
      unsubscribe();
      if (authTimeout) {
        clearTimeout(authTimeout);
      }
    };
  }, [on, authTimeout]);

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!connected) {
      setError('Not connected to local backend. Make sure it is running.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    // Send authentication request via WebSocket with selected region
    api.authenticate({ region: selectedRegion });
  };
  
      
    
  return (
    <Box
      sx={{
        backgroundColor: theme.palette.background.dark, // Dark background
        height: "calc(100vh - 30px)", // Subtract DragBar height from total height
        width: "100vw", // Full width
        display: "flex",
        alignItems: "center", // Center vertically
        justifyContent: "center", // Center horizontally
        margin: 0, // Ensure no margin
        padding: 0, // No padding
        marginTop: "30px", // Account for DragBar height
      }}
    >
      <CssBaseline />
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        <Typography
          component="h1"
          variant="h4"
          sx={{
            fontSize: "3rem",
            color: theme.palette.secondary.dark,
            marginBottom: "0.5rem",
          }}
        >
          ScrimGG
        </Typography>
        
        <Box
          component="form"
          onSubmit={handleLogin}
          noValidate
          sx={{ width: "100%" }}
        >
          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={
              !connected || 
              loading || 
              systemStatus.valorant.status === 'not_running' ||
              systemStatus.valorant.status === 'riot_only' ||
              systemStatus.valorant.status === 'checking' ||
              systemStatus.valorant.status === 'error'
            }
            sx={{
              backgroundColor: theme.palette.secondary.dark,
              width: '60%',
              margin: "auto",
              mb: 2
            }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Authenticate'}
          </Button>
          
          <FormControl sx={{ mb: 2, width: '66.67%' }}>
            <InputLabel id="region-select-label">Region</InputLabel>
            <Select
              labelId="region-select-label"
              id="region-select"
              value={selectedRegion}
              label="Region"
              onChange={(e) => setSelectedRegion(e.target.value)}
              size="small"
              sx={{ 
                backgroundColor: theme.palette.background.paper,
                height: '32px',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: theme.palette.divider,
                },
                '& .MuiSelect-select': {
                  padding: '6px 14px',
                  height: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  textAlign: 'center',
                  justifyContent: 'center'
                }
              }}
            >
              <MenuItem value="na">North America</MenuItem>
              <MenuItem value="eu">Europe</MenuItem>
              <MenuItem value="latam">Latin America</MenuItem>
              <MenuItem value="br">Brazil</MenuItem>
              <MenuItem value="ap">Asia Pacific</MenuItem>
              <MenuItem value="kr">Korea</MenuItem>
            </Select>
          </FormControl>
        </Box>
        {error && (
          <Typography component="p" variant="body2" color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}
      </Box>
      
      {/* Status Indicator - Bottom Left Corner */}
      <Typography 
        variant="body2" 
        sx={{ 
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          fontSize: '0.75rem'
        }}
      >
        {!connected ? (
          <span style={{ color: '#f44336' }}>🔴 Backend Disconnected</span>
        ) : systemStatus.valorant.status === 'running' ? (
          <span style={{ color: '#4caf50' }}>🟢 Game Connected</span>
        ) : systemStatus.valorant.status === 'riot_only' ? (
          <span style={{ color: '#ff9800' }}>🟡 Please Launch Valorant</span>
        ) : systemStatus.valorant.status === 'not_running' ? (
          <span style={{ color: '#f44336' }}>🔴 Riot Client Not Running</span>
        ) : systemStatus.valorant.status === 'error' ? (
          <span style={{ color: '#f44336' }}>🔴 Status Check Error</span>
        ) : (
          <span style={{ color: '#2196f3' }}>🔍 Checking Game Status...</span>
        )}
      </Typography>
    </Box>
  );
};

export default AuthenticationScreen;