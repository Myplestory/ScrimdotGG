import React from 'react';
import { styled } from '@mui/material/styles';
import { theme } from '../theme'

const DragBarStyled = styled('div')(({ theme }) => ({
  WebkitAppRegion: 'drag',
  backgroundColor: theme.palette.background.dark,
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
  width: '100%'
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
  const handleClose = () => {
    window.electronAPI.closeApp();
  };

  return (
    <DragBarStyled>
      <div></div>
      <CloseButton onClick={handleClose}>×</CloseButton>
    </DragBarStyled>
  );
};

export default DragBar;
