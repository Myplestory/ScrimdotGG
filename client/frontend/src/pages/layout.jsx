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
import { TextField, ButtonBase } from '@mui/material';
import Autocomplete from '@mui/material/Autocomplete';
import { ColorModeContext, useMode } from '../theme'; // Use your theme hook
import { MainListItems } from '../components/listitems'; 
import { PlayerInfoCard } from '../components/home/playerinfo';

const drawerWidth = 175;

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  minHeight: '48px !important', // 3/4 of MUI's default 64px height
  padding: '4px 16px !important',
  '@media (min-width: 600px)': {
    minHeight: '48px !important', // Override tablet breakpoint
  },
  '@media (min-width: 0px)': {
    minHeight: '48px !important', // Override mobile breakpoint
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

  const toggleDrawer = () => {
    setOpen(!open);
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
        paddingTop: '30px', // Account for DragBar height
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
          <IconButton color="inherit" sx={{ padding: '4px' }}>
            <Badge badgeContent={4} color="secondary">
              <NotificationsIcon sx={{ fontSize: '1.2rem' }} />
            </Badge>
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
            onClick={() => setActiveComponent('home')} // Redirect to the home page
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