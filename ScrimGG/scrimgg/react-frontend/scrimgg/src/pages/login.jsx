// AuthenticationScreen.jsx
import React, { useState } from 'react';
import { ColorModeContext, useMode } from "../theme";
import { Box, Button, Container, CssBaseline, Typography } from "@mui/material";
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useNavigate } from 'react-router-dom';

function onlyLettersAndNumbers(str) {
  return /^[A-Za-z0-9]*$/.test(str);
}

const AuthenticationScreen = ({ onAuthentication }) => {
  const [username, setusername] = useState('');
  const [password, setpassword] = useState('');
  const [error, setError] = useState('');
  const [theme, colorMode] = useMode();
  // Redirect hook
  const navigate = useNavigate(); // Moved to top level

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    // Define your login endpoint
    const url = 'http://127.0.0.1:8000/login/login/';
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "username":username, "password":password }),
      });
      const data = await response.json();
      console.log(data)
      if (response.ok) {
        // Handle login success, such as storing the token and updating login state
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
        }
        if (data.entitlement_token) {
          localStorage.setItem('entitlement_token', data.entitlement_token);
        }

        console.log('Login successful:', data);
        onAuthentication(data);
        // After storing tokens
        navigate('/landingpage');
      } else {
        // Handle errors, such as displaying a message to the user
        setError(data.message || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('An error occurred during login.');
    }
    };
    

  return (
    <Container component="main" maxWidth="xs">
      <CssBaseline />
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center", // Center both horizontally and vertically
          height: "100vh", // Set the height to fill the viewport
        }}
      >
        <Typography component="h1" variant="h4" color="secondary" sx={{ fontSize: "3rem", color:theme.palette.secondary.dark}}>
          ScrimGG
        </Typography>
        <Box component="form" onSubmit={handleFormSubmit} noValidate sx={{ mt: 1, width: "75%", textAlign: "center" }}>
        <input
          type="text"
          value={username}
          onChange={(e) => setusername(e.target.value)}
          style={{ marginBottom: '10px', padding: '5px' }}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setpassword(e.target.value)}
          style={{ padding: '5px' }}
        />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2, backgroundColor: theme.palette.secondary.dark, width: '60%' }}
          >
            Authenticate
          </Button>
        </Box>
        {error && (
          <Typography component="p" variant="body2" color="error">
            {error}
          </Typography>
        )}
      </Box>
    </Container>
  );
};

export default AuthenticationScreen;