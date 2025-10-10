import React from 'react';
import { styled } from '@mui/material/styles';
import { useLocation } from 'react-router-dom';
import { theme } from '../theme'

const DragBarStyled = styled('div')(({ theme }) => ({
  WebkitAppRegion: 'drag',
  color: theme.palette.text.primary,
  height: '30px',
  maxHeight: '30px',
  padding: '0 16px',
  opacity: '1',
  zIndex: '9999',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  width: '100%',
  border: 'none',
  outline: 'none',
  boxShadow: 'none',
  backgroundColor: 'transparent', // Fully transparent
  color: theme.palette.text.primary, // Match AppBar text color
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: '174px',
    height: '100%',
    backgroundColor: theme.palette.background.paper,
    zIndex: -1,
  },
}));

const noDragStyle = {
  WebkitAppRegion: 'no-drag',
};

const CloseButton = styled('button')(({ theme }) => ({
  WebkitAppRegion: 'no-drag',
  backgroundColor: 'transparent',
  border: 'none',
  color: theme.palette.text.secondary,
  cursor: 'pointer',
  padding: '6px 8px',
  borderRadius: '0',
  fontSize: '16px',
  fontWeight: 'normal',
  transition: 'all 0.2s ease',
  '&:hover': {
    color: theme.palette.text.primary,
    backgroundColor: 'transparent'
  },
  '&:active': {
    color: theme.palette.error.main
  }
}));


const DragBar = () => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/' || location.pathname.includes('login');
  
  const handleClose = () => {
    window.electronAPI.closeApp();
  };

  return (
    <DragBarStyled
      sx={{
        height: isAuthPage ? '30px' : '16px',
        maxHeight: isAuthPage ? '30px' : '16px',
      }}
    >
      <div></div>
      {isAuthPage && <CloseButton onClick={handleClose}>×</CloseButton>}
    </DragBarStyled>
  );
};

export default DragBar;
