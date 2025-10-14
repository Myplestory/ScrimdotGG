import React, { useState, useEffect, Suspense } from "react";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { ColorModeContext, useMode } from "./theme";
import { Box } from "@mui/material"
import DragBar from './components/dragbar';
import AnimatedLogo from './components/AnimatedLogo';

// Pages
import LoadingScreen from './components/loadingscreen';
import AuthenticationScreen from './pages/login';
import LandingPage from './pages/landing';
import MatchPage from './pages/MatchPage';
import Layout from './pages/layout';

// Routings
import {Routes, Route, Navigate, useNavigate } from "react-router-dom"; // Make sure you are using BrowserRouter

// Logout scene
const Logout = ({ setAuthenticated }) => {
  // Add any additional logout logic here (e.g., clearing user session or tokens)
  setAuthenticated(false); // Update the authentication state to false
  console.log("Logout callback")
  return <Navigate to="/Logout" />; // Redirect the user back to the authentication screen
};

// MatchPage wrapper to handle navigation
const MatchPageWrapper = () => {
  const navigate = useNavigate();
  
  const handleSetActiveComponent = (component) => {
    if (component === 'home') {
      navigate('/landingpage');
    } else if (component === 'pug') {
      // Navigate to landing page with pug component active
      navigate('/landingpage', { state: { activeComponent: 'pug' } });
    } else if (component === 'lobby') {
      // Navigate to landing page with lobby component active
      navigate('/landingpage', { state: { activeComponent: 'lobby' } });
    }
  };

  return (
    <Layout setActiveComponent={handleSetActiveComponent}>
      <MatchPage />
    </Layout>
  );
};

function App() {
  // Grab theme, use state, and auth state
  const [theme, colorMode] = useMode();
  const [authenticated, setAuthenticated] = useState(false);
  const [appReady, setAppReady] = useState(false);

  //Loading states
  const [showLoading, setShowLoading] = useState(false);

  const navigate = useNavigate();
  
  // App initialization with extended logo display (5.5 seconds total)
  useEffect(() => {
    const initApp = async () => {
      const htmlLoader = document.getElementById('initial-loader');
      if (htmlLoader) {
        htmlLoader.classList.add('fade-out');
        setTimeout(() => htmlLoader.style.display = 'none', 500);
      }
      
      // Wait a bit for electronAPI to be available, then fade in window
      setTimeout(() => {
        console.log('🔍 Checking for electronAPI...', typeof window.electronAPI);
        if (window.electronAPI && window.electronAPI.fadeInWindow) {
          console.log('✅ Fading in window...');
          window.electronAPI.fadeInWindow();
        } else {
          console.log('❌ electronAPI not available');
        }
      }, 100);
      
      // Random spinner duration between 1-2 seconds
      const spinnerDuration = Math.random() * 1000 + 1000; // 1000-2000ms
      await new Promise(resolve => setTimeout(resolve, spinnerDuration));
      setAppReady(true);
    };
    
    initApp();
  }, []);


  const handleLogout = () => {
    setShowLoading(true);
    setTimeout(() => {
      setAuthenticated(false);
      localStorage.setItem('authenticated', 'false');
      setShowLoading(false);
      navigate("/");
    }, 1500);
  };

  const handleAuthentication = (status) => {
    setAuthenticated(status); // Update state
    localStorage.setItem('authenticated', status ? 'true' : 'false'); // Update localStorage
    if (status) {
      navigate("/landingpage"); // Navigate to landing page on successful login
    }
  };


  // Show animated logo while app initializes
  if (!appReady) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AnimatedLogo />
      </ThemeProvider>
    );
  }
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <DragBar />
      <Box sx={{ paddingTop: '0px' }}>
        {showLoading ? (
          <LoadingScreen theme={theme} />
        ) : (
          <ColorModeContext.Provider value={colorMode}>
            <div className="app">
              {!authenticated ? (
                <AuthenticationScreen onAuthentication={handleAuthentication} />
              ) : (
                <Suspense fallback={<AnimatedLogo />}>
                  <Routes>
                    <Route path="/" element={<Navigate to="/landingpage" replace />} />
                    <Route path="/Logout" element={<Logout setAuthenticated={setAuthenticated} />} />
                    <Route path="/landingpage" element={<LandingPage />} />
                    <Route path="/match/:matchId" element={
                      <MatchPageWrapper />
                    } />
                  </Routes>
                </Suspense>
              )}
            </div>
          </ColorModeContext.Provider>
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;
