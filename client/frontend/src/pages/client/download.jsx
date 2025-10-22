import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
  Alert,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import DownloadIcon from '@mui/icons-material/Download';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WindowsIcon from '@mui/icons-material/Window';
import AppleIcon from '@mui/icons-material/Apple';
import UpdateIcon from '@mui/icons-material/Update';
import SecurityIcon from '@mui/icons-material/Security';
import SpeedIcon from '@mui/icons-material/Speed';
import GroupsIcon from '@mui/icons-material/Groups';

const Download = () => {
  const theme = useTheme();
  const [downloading, setDownloading] = useState(false);

  const currentVersion = '2.1.4';
  const releaseDate = 'October 15, 2025';

  const features = [
    {
      icon: <SpeedIcon sx={{ color: theme.palette.secondary.main }} />,
      title: 'Fast & Lightweight',
      description: 'Optimized performance with minimal resource usage',
    },
    {
      icon: <SecurityIcon sx={{ color: theme.palette.secondary.main }} />,
      title: 'Secure & Private',
      description: 'Industry-standard encryption and data protection',
    },
    {
      icon: <GroupsIcon sx={{ color: theme.palette.secondary.main }} />,
      title: 'Seamless Integration',
      description: 'Direct integration with Valorant and Riot Games',
    },
    {
      icon: <UpdateIcon sx={{ color: theme.palette.secondary.main }} />,
      title: 'Auto-Updates',
      description: 'Always stay up to date with automatic updates',
    },
  ];

  const systemRequirements = {
    windows: {
      minimum: [
        'Windows 10 or later (64-bit)',
        '4 GB RAM',
        '500 MB available disk space',
        'Internet connection required',
      ],
      recommended: [
        'Windows 11 (64-bit)',
        '8 GB RAM or more',
        '1 GB available disk space',
        'Broadband internet connection',
      ],
    },
    mac: {
      minimum: [
        'macOS 11 (Big Sur) or later',
        '4 GB RAM',
        '500 MB available disk space',
        'Internet connection required',
      ],
      recommended: [
        'macOS 13 (Ventura) or later',
        '8 GB RAM or more',
        '1 GB available disk space',
        'Broadband internet connection',
      ],
    },
  };

  const handleDownload = (platform) => {
    setDownloading(true);
    // TODO: Implement actual download logic
    console.log(`Downloading for ${platform}...`);
    setTimeout(() => {
      setDownloading(false);
      alert(`Download started for ${platform}!`);
    }, 1500);
  };

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        overflow: 'auto',
        p: 4,
        backgroundColor: theme.palette.background.default,
      }}
    >
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold', mb: 2 }}>
          Download ScrimGG Client
        </Typography>
        <Typography variant="h6" sx={{ color: theme.palette.text.secondary, mb: 1 }}>
          Version {currentVersion}
        </Typography>
        <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
          Released on {releaseDate}
        </Typography>
      </Box>

      {/* Download Buttons */}
      <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', mb: 6 }}>
        <Paper
          sx={{
            p: 4,
            backgroundColor: theme.palette.background.paper,
            border: `2px solid ${theme.palette.divider}`,
            width: 300,
            textAlign: 'center',
            transition: 'all 0.3s',
            '&:hover': {
              borderColor: theme.palette.secondary.main,
              transform: 'translateY(-4px)',
              boxShadow: `0 8px 24px ${theme.palette.secondary.main}33`,
            },
          }}
        >
          <WindowsIcon sx={{ fontSize: 60, color: theme.palette.secondary.main, mb: 2 }} />
          <Typography variant="h5" sx={{ color: theme.palette.text.primary, fontWeight: 'bold', mb: 1 }}>
            Windows
          </Typography>
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mb: 3 }}>
            Windows 10 or later
          </Typography>
          <Button
            variant="contained"
            color="secondary"
            fullWidth
            size="large"
            startIcon={<DownloadIcon />}
            onClick={() => handleDownload('Windows')}
            disabled={downloading}
            sx={{
              py: 1.5,
              fontWeight: 'bold',
              textTransform: 'none',
            }}
          >
            Download for Windows
          </Button>
          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block', mt: 2 }}>
            ScrimGG-Setup-{currentVersion}.exe • ~85 MB
          </Typography>
        </Paper>

        <Paper
          sx={{
            p: 4,
            backgroundColor: theme.palette.background.paper,
            border: `2px solid ${theme.palette.divider}`,
            width: 300,
            textAlign: 'center',
            transition: 'all 0.3s',
            '&:hover': {
              borderColor: theme.palette.secondary.main,
              transform: 'translateY(-4px)',
              boxShadow: `0 8px 24px ${theme.palette.secondary.main}33`,
            },
          }}
        >
          <AppleIcon sx={{ fontSize: 60, color: theme.palette.secondary.main, mb: 2 }} />
          <Typography variant="h5" sx={{ color: theme.palette.text.primary, fontWeight: 'bold', mb: 1 }}>
            macOS
          </Typography>
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mb: 3 }}>
            macOS 11 or later
          </Typography>
          <Button
            variant="outlined"
            color="secondary"
            fullWidth
            size="large"
            startIcon={<DownloadIcon />}
            onClick={() => handleDownload('macOS')}
            disabled={downloading}
            sx={{
              py: 1.5,
              fontWeight: 'bold',
              textTransform: 'none',
              borderWidth: 2,
              '&:hover': {
                borderWidth: 2,
              },
            }}
          >
            Download for macOS
          </Button>
          <Typography variant="caption" sx={{ color: theme.palette.text.secondary, display: 'block', mt: 2 }}>
            ScrimGG-{currentVersion}.dmg • ~92 MB
          </Typography>
        </Paper>
      </Box>

      {/* Features */}
      <Box sx={{ mb: 6, maxWidth: 1200, mx: 'auto' }}>
        <Typography variant="h5" sx={{ color: theme.palette.text.primary, fontWeight: 'bold', mb: 3, textAlign: 'center' }}>
          Why use the ScrimGG Client?
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
          {features.map((feature, index) => (
            <Paper
              key={index}
              sx={{
                p: 3,
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {feature.icon}
                <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 'bold', ml: 2 }}>
                  {feature.title}
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                {feature.description}
              </Typography>
            </Paper>
          ))}
        </Box>
      </Box>

      {/* System Requirements */}
      <Box sx={{ maxWidth: 1200, mx: 'auto', mb: 6 }}>
        <Typography variant="h5" sx={{ color: theme.palette.text.primary, fontWeight: 'bold', mb: 3, textAlign: 'center' }}>
          System Requirements
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
          {/* Windows Requirements */}
          <Paper
            sx={{
              p: 3,
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <WindowsIcon sx={{ fontSize: 32, color: theme.palette.secondary.main, mr: 2 }} />
              <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 'bold' }}>
                Windows
              </Typography>
            </Box>
            
            <Typography variant="subtitle2" sx={{ color: theme.palette.secondary.main, mb: 1, fontWeight: 'bold' }}>
              Minimum Requirements
            </Typography>
            <List dense>
              {systemRequirements.windows.minimum.map((req, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <CheckCircleIcon sx={{ fontSize: 16, color: theme.palette.text.secondary }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={req}
                    primaryTypographyProps={{
                      variant: 'body2',
                      sx: { color: theme.palette.text.secondary },
                    }}
                  />
                </ListItem>
              ))}
            </List>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" sx={{ color: theme.palette.secondary.main, mb: 1, fontWeight: 'bold' }}>
              Recommended
            </Typography>
            <List dense>
              {systemRequirements.windows.recommended.map((req, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <CheckCircleIcon sx={{ fontSize: 16, color: theme.palette.secondary.main }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={req}
                    primaryTypographyProps={{
                      variant: 'body2',
                      sx: { color: theme.palette.text.secondary },
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* macOS Requirements */}
          <Paper
            sx={{
              p: 3,
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <AppleIcon sx={{ fontSize: 32, color: theme.palette.secondary.main, mr: 2 }} />
              <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 'bold' }}>
                macOS
              </Typography>
            </Box>
            
            <Typography variant="subtitle2" sx={{ color: theme.palette.secondary.main, mb: 1, fontWeight: 'bold' }}>
              Minimum Requirements
            </Typography>
            <List dense>
              {systemRequirements.mac.minimum.map((req, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <CheckCircleIcon sx={{ fontSize: 16, color: theme.palette.text.secondary }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={req}
                    primaryTypographyProps={{
                      variant: 'body2',
                      sx: { color: theme.palette.text.secondary },
                    }}
                  />
                </ListItem>
              ))}
            </List>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" sx={{ color: theme.palette.secondary.main, mb: 1, fontWeight: 'bold' }}>
              Recommended
            </Typography>
            <List dense>
              {systemRequirements.mac.recommended.map((req, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <CheckCircleIcon sx={{ fontSize: 16, color: theme.palette.secondary.main }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={req}
                    primaryTypographyProps={{
                      variant: 'body2',
                      sx: { color: theme.palette.text.secondary },
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      </Box>

      {/* Installation Note */}
      <Alert
        severity="info"
        sx={{
          maxWidth: 1200,
          mx: 'auto',
          mb: 6,
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.info.main}`,
        }}
      >
        <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
          Installation Instructions
        </Typography>
        <Typography variant="body2">
          1. Download the installer for your operating system<br />
          2. Run the installer and follow the on-screen instructions<br />
          3. Launch ScrimGG and log in with your Riot Games account<br />
          4. The client will automatically check for updates on startup
        </Typography>
      </Alert>
    </Box>
  );
};

export default Download;
