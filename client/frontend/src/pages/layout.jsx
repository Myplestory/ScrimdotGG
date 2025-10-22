import React, { useState } from 'react';
import { styled } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import MuiDrawer from '@mui/material/Drawer';
import MuiAppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Badge from '@mui/material/Badge';
import List from '@mui/material/List';
import NotificationsIcon from '@mui/icons-material/Notifications';
import MenuIcon from '@mui/icons-material/Menu';
import MinimizeIcon from '@mui/icons-material/Minimize';
import CropSquareIcon from '@mui/icons-material/CropSquare';
import { TextField, ButtonBase } from '@mui/material';
import Autocomplete from '@mui/material/Autocomplete';
import { useNavigate } from 'react-router-dom';
import { ColorModeContext, useMode } from '../theme'; // Use your theme hook
import { useWebSocket } from '../contexts/WebSocketContext';
import { MainListItems } from '../components/listitems'; 
import { PlayerInfoCard } from '../components/home/playerinfo';
import StatusIndicator from '../components/StatusIndicator';

const drawerWidth = 175;

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  minHeight: '62px !important', // Increased by 8px for better proportions
  padding: '4px 16px !important',
  '@media (min-width: 600px)': {
    minHeight: '62px !important', // Override tablet breakpoint
  },
  '@media (min-width: 0px)': {
    minHeight: '62px !important', // Override mobile breakpoint
  },
}));

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
  zIndex: theme.zIndex.drawer + 1,
  backgroundColor: "#121212", // Match the drawer's background color
  color: theme.palette.text.primary, // Text color from theme
  transition: theme.transitions.create(['width', 'margin'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    marginLeft: drawerWidth,
    width: `calc(100% - ${drawerWidth}px)`,
    transition: theme.transitions.create(['width', 'margin'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const Drawer = styled(MuiDrawer, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
  '& .MuiDrawer-paper': {
    position: 'fixed',
    whiteSpace: 'nowrap',
    width: open ? drawerWidth : theme.spacing(5), // Adjust the drawer width based on its open/closed state
    transition: theme.transitions.create('width', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
    overflowX: 'hidden',
    backgroundColor: theme.palette.background.paper, // Dark gray background
    color: theme.palette.text.primary, // White text
  },
}));

const Layout = ({ children, setActiveComponent }) => {
  const [theme, colorMode] = useMode(); // Use your predefined theme
  const [open, setOpen] = useState(true);
  const { connected, systemStatus, queueStatus, gameState } = useWebSocket();
  const navigate = useNavigate();

  const toggleDrawer = () => {
    setOpen(!open);
  };

  const handleMinimize = () => {
    if (window.electronAPI && window.electronAPI.minimizeWindow) {
      window.electronAPI.minimizeWindow();
    }
  };

  const handleMaximize = () => {
    if (window.electronAPI && window.electronAPI.maximizeWindow) {
      window.electronAPI.maximizeWindow();
    }
  };

  const handleClose = () => {
    if (window.electronAPI && window.electronAPI.closeApp) {
      window.electronAPI.closeApp();
    }
  };

  const handleHomeClick = () => {
    navigate('/', { state: { activeComponent: 'home' } });
  };

  return (
    <Box
      sx={{
        display: 'flex',
        height: '100vh', // Ensure the Layout spans the full height of the viewport
        width: '100vw', // Ensure the Layout spans the full width of the viewport
        overflow: 'hidden', // Prevent overflow
        backgroundColor: theme.palette.primary.dark,
        color: theme.palette.text.primary,
        paddingTop: '16px', // Account for minimal DragBar height
      }}
    >
      <CssBaseline />
      {/* AppBar */}
      <AppBar position="fixed" open={open}>
      <StyledToolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={toggleDrawer}
            sx={{
              marginRight: 1,
              padding: '4px',
              ...(open && { display: 'none' }),
            }}
          >
            <MenuIcon />
          </IconButton>
          <Autocomplete
            disablePortal
            id="freesolo"
            options={[
              { label: 'Option 1', id: 1 },
              { label: 'Option 2', id: 2 },
            ]}
            sx={{
              minWidth: '200px',
              maxWidth: '20%',
              marginRight: 'auto',
              height: '40px',
              '& .MuiAutocomplete-inputRoot': {
                height: '40px',
              },
            }}
                renderInput={(params) => (
              <TextField
                {...params}
                label="Search"
                variant="outlined"
                size="small"
                InputProps={{
                  ...params.InputProps,
                  sx: {
                    backgroundColor: theme.palette.background.dark,
                    color: theme.palette.text.primary,
                    height: '32px',
                  },
                }}
              />
            )}
          />
          <IconButton 
            color="inherit" 
            sx={{ 
              padding: '4px',
              '&:hover': {
                backgroundColor: 'transparent',
                '& .MuiSvgIcon-root': {
                  filter: 'drop-shadow(0 0 8px rgba(255, 255, 255, 0.8))',
                  transform: 'scale(1.1)',
                }
              },
              transition: 'all 0.2s ease',
            }}
          >
            <Badge badgeContent={0} color="secondary">
              <NotificationsIcon sx={{ fontSize: '1.4rem' }} />
            </Badge>
          </IconButton>
          
          {/* Minimize Button */}
          <IconButton 
            color="inherit" 
            sx={{ 
              padding: '4px 8px',
              marginLeft: '8px',
              fontSize: '1.4rem',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
              },
              transition: 'all 0.2s ease',
            }}
            onClick={handleMinimize}
          >
            <MinimizeIcon sx={{ fontSize: '1.2rem' }} />
          </IconButton>

          {/* Maximize/Restore Button */}
          <IconButton 
            color="inherit" 
            sx={{ 
              padding: '4px 8px',
              marginLeft: '4px',
              fontSize: '1.4rem',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
              },
              transition: 'all 0.2s ease',
            }}
            onClick={handleMaximize}
          >
            <CropSquareIcon sx={{ fontSize: '1rem' }} />
          </IconButton>
          
          {/* Close Button */}
          <IconButton 
            color="inherit" 
            sx={{ 
              padding: '4px 8px',
              marginLeft: '4px',
              fontSize: '1.6rem',
              '&:hover': {
                backgroundColor: 'rgba(255, 0, 0, 0.3)',
                color: '#ff4444',
              },
              transition: 'all 0.2s ease',
            }}
            onClick={handleClose}
          >
            ×
          </IconButton>
        </StyledToolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer variant="permanent" open={open}>
        <StyledToolbar
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ButtonBase
            onClick={handleHomeClick} // Navigate to the home page
            sx={{
              textAlign: 'center',
              color: theme.palette.secondary.main,
              textDecoration: 'none',
            }}
          >
            <Typography variant="h6" sx={{ color: theme.palette.secondary.main }}>
              ScrimGG
            </Typography>
          </ButtonBase>
        </StyledToolbar>
        <Divider />
        <List component="nav" sx={{
            padding: 0, // Remove padding from the nav
            margin: 0,  // Remove margin
            '& .MuiListItemButton-root': {
              padding: '8px 16px', 
            },
            '& .MuiAccordion-root': {
              margin: 0, // Remove accordion margin
            },
            '& .MuiAccordionSummary-root': {
              padding: '0 16px', // Adjust accordion summary padding
            },
          }}>
          <MainListItems setActiveComponent={setActiveComponent} /> {/* Pass it to MainListItems */}
        </List>
        
        {/* Status Indicator - Bottom of Sidebar */}
        <StatusIndicator 
          connected={connected}
          systemStatus={systemStatus}
          queueStatus={queueStatus}
          gameState={gameState}
          position="bottom-left"
        />
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.palette.background.dark, // Dark blue background
          color: theme.palette.text.primary,
          overflow: 'hidden',
          height: '100%', // Fill the full height
          marginLeft: open ? `${drawerWidth}px` : 0, // Account for Drawer width
          transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
        }}
      >
        <StyledToolbar /> {/* Offset for the AppBar */}
        <Box
          sx={{
            flexGrow: 1,
            width: '100%', // Ensure full width
            height: '100%', // Ensure full height
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};


export default Layout;