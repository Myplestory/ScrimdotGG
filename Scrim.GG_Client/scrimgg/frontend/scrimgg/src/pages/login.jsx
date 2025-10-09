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
  const [theme, colorMode] = useMode();
  const navigate = useNavigate();
  
  // Use WebSocket context
  const { connected, authenticated, api, on } = useWebSocket();

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
    });
    
    return unsubscribe;
  }, [on]);

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
        {/* Connection Status */}
        <Typography variant="body2" color={connected ? 'success.main' : 'error.main'} sx={{ mb: 2 }}>
          {connected ? '🟢 Connected to local backend' : '🔴 Not connected to backend'}
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
            disabled={!connected || loading}
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