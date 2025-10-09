import React from 'react';
import { styled } from '@mui/material/styles';
import { theme } from '../theme'

const DragBarStyled = styled('div')(({ theme }) => ({
  WebkitAppRegion: 'drag',
  backgroundColor: 'transparent',
  color: theme.palette.text.primary,
  height: '10px',
  maxHeight: '10px',
  padding: '0',
  opacity: '0',
  zIndex: '9999'
}));

const noDragStyle = {
  WebkitAppRegion: 'no-drag',
};

const CloseButton = styled('button')(({ theme }) => ({
  // ...styles for close button
}));

const DragBar = () => {
  const handleClose = () => {
    window.electronAPI.closeApp();
  };

  return (
    <DragBarStyled>
      <div></div>
      <div>
      <CloseButton onClick={handleClose} style={noDragStyle} >X</CloseButton>
      </div>
    </DragBarStyled>
  );
};

export default DragBar;
