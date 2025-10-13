import React, { useEffect, useState } from 'react';
import { Box, keyframes } from '@mui/material';
import { useMode } from '../theme';

const spin = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

const fadeIn = keyframes`
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
`;

export default function AnimatedLogo() {
  const [showSpinner, setShowSpinner] = useState(false);
  const [theme, colorMode] = useMode();
  
  useEffect(() => {
    // Show purple spinner immediately (after window fade-in)
    const spinnerTimer = setTimeout(() => setShowSpinner(true), 100);
    
    return () => {
      clearTimeout(spinnerTimer);
    };
  }, []);
  
  return (
    <Box
      sx={{
        backgroundColor: 'transparent',
        height: "100vh",
        width: "100vw",
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: 0,
        padding: 0,
      }}
    >
      {/* Purple Spinner - Centered */}
      {showSpinner && (
        <Box
          sx={{
            width: 60,
            height: 60,
            border: `3px solid rgba(212, 160, 255, 0.1)`,
            borderTopColor: theme.palette.secondary.main,
            borderRadius: '50%',
            animation: `${spin} 1s linear infinite, ${fadeIn} 0.3s ease-out`,
          }}
        />
      )}
    </Box>
  );
}