import React, { useState, useEffect } from "react";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { ColorModeContext, useMode } from "./theme";
import { Box } from "@mui/material"
import logo from './logo.svg';  
import DragBar from './components/dragbar';

// Pages
import LoadingScreen from './components/loadingscreen';
import AuthenticationScreen from './pages/login';
import LandingPage from './pages/landing'

// Routings
import {Routes, Route, Navigate, useNavigate } from "react-router-dom"; // Make sure you are using BrowserRouter

// Logout scene
const Logout = ({ setAuthenticated }) => {
  // Add any additional logout logic here (e.g., clearing user session or tokens)
  setAuthenticated(false); // Update the authentication state to false
  console.log("Logout callback")
  return <Navigate to="/Logout" />; // Redirect the user back to the authentication screen
};

function App() {
  // Grab theme, use state, and auth state
  const [theme, colorMode] = useMode();
  const [authenticated, setAuthenticated] = useState(false);

  //Loading states
  const [loading, setLoading] = useState(true);
  const [showLoading, setShowLoading] = useState(false); // Add a loading state

  const navigate = useNavigate();


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
              {!authenticated ? ( // Show login screen if not authenticated
                <AuthenticationScreen onAuthentication={handleAuthentication} />
              ) : (
                <Routes>
                  <Route path="/" element={<Navigate to="/landingpage" replace />} />
                  <Route path="/Logout" element={<Logout setAuthenticated={setAuthenticated} />} />
                  <Route path="/landingpage" element={<LandingPage />} />
                </Routes>
              )}
            </div>
          </ColorModeContext.Provider>
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;
