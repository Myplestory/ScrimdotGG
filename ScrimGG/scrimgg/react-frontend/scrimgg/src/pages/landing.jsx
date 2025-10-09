// // AuthenticationScreen.jsx
// import React, { useState } from 'react';
// import { ColorModeContext, useMode } from "../theme";
// import { Box, Button, Container, CssBaseline, Paper, Typography, Avatar, Grid, ThemeProvider } from "@mui/material";
// import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
// import { useNavigate } from 'react-router-dom';

// const LandingPage = () => {
//   const [theme, colorMode] = useMode();
//   // Mock user data, replace with actual data from your backend
//   const user = {
//     name: 'User Name',
//     avatar: '/path/to/avatar.jpg', // Replace with user's avatar path
//     elo: 1234,
//     level: 10
//   };

//   return (
//     <ThemeProvider theme={theme}>
//       <Box sx={{ display: 'flex' }}>
//         <CssBaseline />
//         {/* Sidebar, AppBar, and other components can be added here */}
//         <Box
//           component="main"
//           sx={{
//             flexGrow: 1,
//             height: '100vh',
//             overflow: 'auto',
//           }}
//         >
//           <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
//             <Grid container spacing={3}>
//               {/* Profile details */}
//               <Grid item xs={12}>
//                 <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
//                   <Typography component="h2" variant="h6" color="primary" gutterBottom>
//                     user
//                   </Typography>
//                   {/* Profile content like username, stats, etc. goes here */}
//                 </Paper>
//               </Grid>
//             </Grid>
//           </Container>
//         </Box>
//       </Box>
//     </ThemeProvider>
//   );
// };


import * as React from 'react';
import { styled, createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import MuiDrawer from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import MuiAppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Badge from '@mui/material/Badge';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Link from '@mui/material/Link';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import NotificationsIcon from '@mui/icons-material/Notifications';
import { TextField } from '@mui/material';
import Autocomplete from '@mui/material/Autocomplete';
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import { ColorModeContext, useMode } from '../theme';
import { MainListItems } from '../components/listitems';
import HomeComponent from '../components/home'
import Chart from '../components/chart';
import Lobby from '../components/lobby';

function Copyright(props) {
  return (
    <Typography variant="body2" color="text.secondary" align="center" {...props}>
      {'Copyright © '}
      <Link color="inherit" href="https://mui.com/">
        Your Website
      </Link>{' '}
      {new Date().getFullYear()}
      {'.'}
    </Typography>
  );
}

const drawerWidth = 175;

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
  zIndex: theme.zIndex.drawer + 1,
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

const Drawer = styled(MuiDrawer, { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme, open }) => ({
    '& .MuiDrawer-paper': {
      position: 'relative',
      whiteSpace: 'nowrap',
      width: drawerWidth,
      transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.enteringScreen,
      }),
      boxSizing: 'border-box',
      ...(!open && {
        overflowX: 'hidden',
        transition: theme.transitions.create('width', {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.leavingScreen,
        }),
        width: theme.spacing(7),
        [theme.breakpoints.up('sm')]: {
          width: theme.spacing(9),
        },
      }),
    },
  }),
);

const searchOptions = [
  { label: 'Option 1', id: 1 },
  { label: 'Option 2', id: 2 },
  // Add more options here
];


const LandingPage = () => {
  const [theme, colorMode] = useMode();
  const [open, setOpen] = React.useState(true);
  const [searchText, setSearchText] = React.useState('');
  const [activeComponent, setActiveComponent] = React.useState('home');

  const setActiveComponentHandler = (componentName) => {
    setActiveComponent(componentName);
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ display: 'flex', paddingTop:'-10px'}}>
        <CssBaseline />
        <AppBar position="absolute" sx={{  }} open={open}>
          <Toolbar
          >
            <IconButton
              edge="start"
              color="inherit"
              // aria-label="open drawer"
              // onClick={toggleDrawer}
              sx={{
                marginRight: '36px',
                ...(open && { display: 'none' }),
              }}
            >
              <MenuIcon />
            </IconButton>
            <Typography
              component="h1"
              variant="h6"
              color="inherit"
              noWrap
              sx={{ flexGrow: 1 }}
            >
            <Autocomplete
              disablePortal
              id="freesolo"
              filterOptions={(x) => x}
              options={searchOptions}
              sx={{ minWidth: '200px',
              maxWidth: '20%',
              height:'50%'
               }}
              renderInput={(params) => <TextField {...params} label="Search" />}
              onInputChange={(event, newInputValue) => {
                setSearchText(newInputValue);
                // Optionally, perform a search operation here
              }}
            />
            </Typography>
            <IconButton color="inherit">
              <Badge badgeContent={4} color="secondary">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Toolbar>
        </AppBar>
        <Drawer variant="permanent" sx={{
            }}
            open={open}>
          <Toolbar
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              px: [1],
            }}
          >
            <Typography
              component="h1"
              variant="h4"
              color={theme.palette.secondary.main}
              noWrap
              sx={{ flexGrow: 1, textAlign: 'center',  }}
            >
              ScrimGG
            </Typography>
          </Toolbar>
          <Divider sx = {{}}/>
          <List component="nav" sx={{ padding:'0',color:theme.palette.grey}}>
            < MainListItems setActiveComponent={setActiveComponentHandler}/>
          </List>
        </Drawer>
        <Box
          component="main"
          sx={{
            backgroundColor: (theme) =>
              theme.palette.mode === colorMode
                ? theme.palette.grey[100]
                : theme.palette.grey[900],
            flexGrow: 1,
            height: '100vh',
            overflow: 'auto',
            paddingTop: '7%',
          }}
        >
          {activeComponent === 'home' && <HomeComponent />}
          {activeComponent === 'lobby' && <Lobby />}
        </Box>
      </Box>
    </ThemeProvider>
  );
}
export default LandingPage;