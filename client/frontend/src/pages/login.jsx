// AuthenticationScreen.jsx
import React, { useState, useEffect } from 'react';
import { ColorModeContext, useMode } from "../theme";
import { Box, Button, Container, CssBaseline, Typography, CircularProgress } from "@mui/material";
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../contexts/WebSocketContext';

function onlyLettersAndNumbers(str) {
  return /^[A-Za-z0-9]*$/.test(str);
}

const AuthenticationScreen = ({ onAuthentication }) => {
  const [username, setusername] = useState('');
  const [password, setpassword] = useState('');
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
    
    // Send authentication request via WebSocket
    api.authenticate();
  };
  
      
    
  return (
    <Box
      sx={{
        backgroundColor: theme.palette.background.dark, // Dark background
        minHeight: "100vh", // Full height
        width: "100vw", // Full width
        display: "flex",
        alignItems: "center", // Center vertically
        justifyContent: "center", // Center horizontally
        margin: 0, // Ensure no margin
        padding: 0, // Ensure no padding
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
            marginBottom: "2rem",
          }}
        >
          ScrimGG
        </Typography>
        {/* Combined Game Status */}
        <Typography variant="body2" sx={{ mb: 2 }}>
          {!connected ? (
            <span style={{ color: '#f44336' }}>🔴 Backend Disconnected</span>
          ) : systemStatus.valorant.status === 'running' ? (
            <span style={{ color: '#4caf50' }}>🟢 Game Connected</span>
          ) : systemStatus.valorant.status === 'not_running' ? (
            <span style={{ color: '#ff9800' }}>⚠️ Valorant Not Running</span>
          ) : (
            <span style={{ color: '#2196f3' }}>🔍 Checking Game Status...</span>
          )}
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
            disabled={!connected || loading || systemStatus.valorant.status === 'not_running'}
            sx={{
              backgroundColor: theme.palette.secondary.dark,
              width: '60%',
              margin: "auto",
            }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Authenticate'}
          </Button>
        </Box>
        {error && (
          <Typography component="p" variant="body2" color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default AuthenticationScreen;