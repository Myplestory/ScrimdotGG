// AuthenticationScreen.jsx
import React, { useState, useEffect, useRef } from 'react';
import { ColorModeContext, useMode } from "../theme";
import { Box, Button, Container, CssBaseline, Typography, CircularProgress, FormControl, InputLabel, Select, MenuItem } from "@mui/material";
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../contexts/WebSocketContext';
import StatusIndicator from '../components/StatusIndicator';
import { gsap } from 'gsap';
import { usePageEnter } from '../animations/useGSAP';
import { fadeIn, scaleIn, slideIn, ease } from '../animations/gsapUtils';

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
  
  // Background videos - randomly cycle through them
  const backgrounds = [
    '/backgrounds/valorant-1.mp4',
    '/backgrounds/valorant-2.mp4',
    '/backgrounds/valorant-3.mp4',
    '/backgrounds/valorant-4.mp4',
    '/backgrounds/valorant-5.mp4',
    '/backgrounds/valorant-6.mp4',
    '/backgrounds/valorant-7.mp4',
  ];
  const [selectedBackground, setSelectedBackground] = useState(() => 
    backgrounds[Math.floor(Math.random() * backgrounds.length)]
  );
  const videoRef = useRef(null);
  
  // Change to random background when video/gif completes
  const handleVideoEnd = () => {
    const currentIndex = backgrounds.indexOf(selectedBackground);
    let newIndex;
    // Make sure we pick a different one
    do {
      newIndex = Math.floor(Math.random() * backgrounds.length);
    } while (newIndex === currentIndex && backgrounds.length > 1);
    
    setSelectedBackground(backgrounds[newIndex]);
  };
  
  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const formRef = useRef(null);
  const buttonRef = useRef(null);
  
  // Use WebSocket context
  const { connected, authenticated, systemStatus, api, on } = useWebSocket();

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    // Set initial states
    gsap.set(titleRef.current, {
      opacity: 0,
      y: -30,
      scale: 0.9,
    });
    
    gsap.set(formRef.current, {
      opacity: 0,
      y: 20,
    });
    
    // Title animation - faster and punchier
    tl.to(titleRef.current, {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.5,
      ease: ease.aggressive,
    })
    // Form container - quick fade in
    .to(formRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.4,
      ease: ease.smooth,
    }, '-=0.2');
    
    return tl;
  }, []);

  // Button hover effect
  useEffect(() => {
    if (!buttonRef.current) return;
    
    const button = buttonRef.current;
    
    const handleMouseEnter = () => {
      gsap.to(button, {
        scale: 1.05,
        duration: 0.3,
        ease: ease.snappy,
      });
    };
    
    const handleMouseLeave = () => {
      gsap.to(button, {
        scale: 1,
        duration: 0.3,
        ease: ease.snappy,
      });
    };
    
    button.addEventListener('mouseenter', handleMouseEnter);
    button.addEventListener('mouseleave', handleMouseLeave);
    
    return () => {
      button.removeEventListener('mouseenter', handleMouseEnter);
      button.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [loading, connected, systemStatus]);

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
      ref={containerRef}
      sx={{
        backgroundColor: theme.palette.background.dark,
        height: "calc(100vh - 30px)",
        width: "100vw",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        margin: 0,
        padding: 0,
        marginTop: "30px",
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <CssBaseline />
      
      {/* Background Video/GIF */}
      <Box
        component="video"
        ref={videoRef}
        key={selectedBackground}
        autoPlay
        muted
        onEnded={handleVideoEnd}
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'brightness(0.3)',
          pointerEvents: 'none',
        }}
      >
        <source src={selectedBackground} type="video/mp4" />
      </Box>
      
      {/* Dark overlay for better contrast */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `linear-gradient(135deg, ${theme.palette.background.dark}dd 0%, ${theme.palette.background.dark}aa 50%, ${theme.palette.background.dark}dd 100%)`,
          pointerEvents: 'none',
        }}
      />
      
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          zIndex: 1,
        }}
      >
        <Typography
          ref={titleRef}
          component="h1"
          variant="h4"
          sx={{
            fontSize: "4rem",
            fontWeight: 900,
            background: `linear-gradient(135deg, ${theme.palette.secondary.main} 0%, ${theme.palette.secondary.light} 100%)`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            marginBottom: "3rem",
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
          }}
        >
          ScrimGG
        </Typography>
        
        <Box
          ref={formRef}
          component="form"
          onSubmit={handleLogin}
          noValidate
          sx={{ 
            width: "100%",
            minWidth: '400px',
            backgroundColor: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: '16px',
            padding: '40px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
          }}
        >
          <Button
            ref={buttonRef}
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
              background: `linear-gradient(135deg, ${theme.palette.secondary.dark} 0%, ${theme.palette.secondary.main} 100%)`,
              width: '100%',
              margin: "auto",
              mb: 3,
              py: 2,
              fontSize: '1.1rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.15em',
              transition: 'all 0.3s ease',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
              '&:hover': {
                background: `linear-gradient(135deg, ${theme.palette.secondary.main} 0%, ${theme.palette.secondary.light} 100%)`,
                boxShadow: '0 6px 16px rgba(0, 0, 0, 0.4)',
                transform: 'translateY(-2px)',
              },
              '&:active': {
                transform: 'translateY(0)',
              },
              '&:disabled': {
                background: theme.palette.action.disabledBackground,
                color: theme.palette.action.disabled,
                boxShadow: 'none',
              },
            }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Authenticate'}
          </Button>
          
          <FormControl sx={{ mb: 0, width: '100%' }}>
            <InputLabel 
              id="region-select-label"
              sx={{
                color: theme.palette.text.secondary,
                '&.Mui-focused': {
                  color: theme.palette.secondary.main,
                },
              }}
            >
              Region
            </InputLabel>
            <Select
              labelId="region-select-label"
              id="region-select"
              value={selectedRegion}
              label="Region"
              onChange={(e) => setSelectedRegion(e.target.value)}
              size="small"
              sx={{ 
                backgroundColor: theme.palette.background.default + '80',
                height: '56px',
                borderRadius: '8px',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: theme.palette.divider,
                  borderWidth: '2px',
                  transition: 'all 0.3s ease',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: theme.palette.secondary.main,
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: theme.palette.secondary.main,
                },
                '& .MuiSelect-select': {
                  padding: '16px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  textAlign: 'left',
                  fontWeight: 500,
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
          <Typography 
            component="p" 
            variant="body2" 
            sx={{ 
              mt: 2,
              color: '#ff4655',
              fontWeight: 500,
            }}
          >
            {error}
          </Typography>
        )}
      </Box>
      
      {/* Status Indicator - Bottom Left Corner */}
      <StatusIndicator 
        connected={connected}
        systemStatus={systemStatus}
        position="bottom-left"
      />
    </Box>
  );
};

export default AuthenticationScreen;