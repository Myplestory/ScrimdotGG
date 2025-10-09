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
    setLoading(true);
    setShowLoading(true); // Show the loading screen immediately when logging out

    // Simulate logout process for 1.5 seconds
    setTimeout(() => {
      setAuthenticated(false);
      localStorage.setItem('authenticated', 'false');
      setLoading(false);
      setShowLoading(false); // Hide the loading screen after the delay
    }, 1500);
  };

  useEffect(() => {
    setLoading(true);
    // Check if the user is already authenticated from local storage
    const isAuthenticated = localStorage.getItem('authenticated');
    setTimeout(() => {
      if (isAuthenticated === 'true') {
      // If authenticated, update the state in the parent component
        setAuthenticated(true);
        setLoading(false);
      }
    }, 1500);
    setLoading(false);
  },[]);

  const handleAuthentication = (status) => {
    setAuthenticated(status);
    localStorage.setItem('authenticated', status.toString()); // Update local storage upon authentication status change
    if (status) {
      setLoading(true);
      setShowLoading(true); // Show the loading screen immediately 

      // Simulate logout process for 1.5 seconds
      setTimeout(() => {
      setLoading(false);
      setShowLoading(false); // Hide the loading screen after the delay
    }, 1500);
      navigate("/");
    }
  };


  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <DragBar />
      <Box sx={{ paddingTop: '0px' }}> {/* Adjust this value based on the DragBar's height */}
        {showLoading ? (
          <LoadingScreen theme={theme}/>
        ) : (
          <ColorModeContext.Provider value={colorMode}>
            {/* ... */}
            <div className="app">
              {authenticated ? (
                <>
                <main className="content">
                    <Routes>
                      <Route path="/Logout"
                        element={<Logout setAuthenticated={setAuthenticated} />}
                      />
                      <Route path="/landingpage" element={<LandingPage />} />
                    </Routes>
                  </main>
                </>
              ) : (
                <AuthenticationScreen onAuthentication={handleAuthentication} />
              )}
            </div>
          </ColorModeContext.Provider>
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;
