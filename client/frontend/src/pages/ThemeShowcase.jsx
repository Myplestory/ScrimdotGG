import React from 'react';
import { Box, Paper, Typography, Button, Grid } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import '../valorant-theme.css';

/**
 * Valorant Theme Showcase Component
 * Use this as a reference for styling your components
 * Navigate to /theme-showcase to see this in action
 */

const ThemeShowcase = () => {
  const theme = useTheme();

  return (
    <Box sx={{ 
      p: 4, 
      bgcolor: theme.palette.background.default,
      minHeight: '100vh'
    }}>
      <Typography variant="h3" className="val-text-primary" gutterBottom>
        🎨 Valorant Theme Showcase
      </Typography>
      
      <div className="val-divider-red" />

      {/* Color Swatches */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Color Palette
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: '#0f0f0f', border: '1px solid #282828' }}>
              <Typography className="val-text-primary">#0f0f0f</Typography>
              <Typography className="val-text-secondary">Primary BG</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: '#151515', border: '1px solid #282828' }}>
              <Typography className="val-text-primary">#151515</Typography>
              <Typography className="val-text-secondary">Card BG</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: '#FF4655', border: '1px solid #FF4655' }}>
              <Typography sx={{ color: 'white', fontWeight: 600 }}>#FF4655</Typography>
              <Typography sx={{ color: 'white' }}>Valorant Red</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: '#1ac996', border: '1px solid #1ac996' }}>
              <Typography sx={{ color: 'white', fontWeight: 600 }}>#1ac996</Typography>
              <Typography sx={{ color: 'white' }}>Success Green</Typography>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Buttons */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Buttons
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <button className="val-button-primary">Primary Action</button>
          <button className="val-button-secondary">Secondary Action</button>
          <button className="val-button-ghost">Ghost Button</button>
          <Button variant="contained" color="secondary">MUI Contained</Button>
          <Button variant="outlined" color="secondary">MUI Outlined</Button>
        </Box>
      </Box>

      {/* Cards */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Cards
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <div className="val-card" style={{ padding: '16px' }}>
              <Typography variant="h6" className="val-text-primary">Basic Card</Typography>
              <Typography className="val-text-secondary">
                Standard card with dark background
              </Typography>
            </div>
          </Grid>
          <Grid item xs={12} md={4}>
            <div className="val-card val-hover-glow" style={{ padding: '16px' }}>
              <Typography variant="h6" className="val-text-primary">Hover Card</Typography>
              <Typography className="val-text-secondary">
                Card with glow on hover
              </Typography>
            </div>
          </Grid>
          <Grid item xs={12} md={4}>
            <div className="val-card-active" style={{ padding: '16px' }}>
              <Typography variant="h6" className="val-text-primary">Active Card</Typography>
              <Typography className="val-text-secondary">
                Card in active state
              </Typography>
            </div>
          </Grid>
        </Grid>
      </Box>

      {/* Badges */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Badges
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <span className="val-badge val-badge-primary">LIVE</span>
          <span className="val-badge val-badge-primary">RADIANT</span>
          <span className="val-badge val-badge-success">ONLINE</span>
          <span className="val-badge val-badge-success">WIN</span>
          <span className="val-badge val-badge-neutral">UNRANKED</span>
          <span className="val-badge val-badge-neutral">IDLE</span>
        </Box>
      </Box>

      {/* Glow Effects */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Glow Effects
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Paper className="val-glow-sm" sx={{ 
              p: 3, 
              bgcolor: theme.palette.background.paper,
              textAlign: 'center'
            }}>
              <Typography className="val-text-primary">Small Glow</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper className="val-glow-md" sx={{ 
              p: 3, 
              bgcolor: theme.palette.background.paper,
              textAlign: 'center'
            }}>
              <Typography className="val-text-primary">Medium Glow</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper className="val-glow-lg" sx={{ 
              p: 3, 
              bgcolor: theme.palette.background.paper,
              textAlign: 'center'
            }}>
              <Typography className="val-text-primary">Large Glow</Typography>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Typography */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Typography
        </Typography>
        <Paper sx={{ p: 3, bgcolor: theme.palette.background.paper }}>
          <Typography variant="h4" className="val-text-primary" gutterBottom>
            Heading 4 - Primary
          </Typography>
          <Typography variant="h6" className="val-text-primary" gutterBottom>
            Heading 6 - Primary
          </Typography>
          <Typography variant="body1" className="val-text-secondary" gutterBottom>
            Body text - Secondary color for descriptions
          </Typography>
          <Typography variant="body2" className="val-text-muted" gutterBottom>
            Small text - Muted color for subtle information
          </Typography>
          <Typography variant="body1" className="val-text-accent">
            Accent text - Red highlight for important info
          </Typography>
        </Paper>
      </Box>

      {/* Input Fields */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Input Fields
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 400 }}>
          <input 
            type="text" 
            className="val-input" 
            placeholder="Enter your username"
          />
          <input 
            type="email" 
            className="val-input" 
            placeholder="Enter your email"
          />
          <input 
            type="password" 
            className="val-input" 
            placeholder="Enter your password"
          />
        </Box>
      </Box>

      {/* Progress Bar */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Progress Bars
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <div>
            <Typography className="val-text-secondary" gutterBottom>25% Progress</Typography>
            <div className="val-progress">
              <div className="val-progress-bar" style={{ width: '25%' }} />
            </div>
          </div>
          <div>
            <Typography className="val-text-secondary" gutterBottom>50% Progress</Typography>
            <div className="val-progress">
              <div className="val-progress-bar" style={{ width: '50%' }} />
            </div>
          </div>
          <div>
            <Typography className="val-text-secondary" gutterBottom>75% Progress</Typography>
            <div className="val-progress">
              <div className="val-progress-bar" style={{ width: '75%' }} />
            </div>
          </div>
        </Box>
      </Box>

      {/* Dividers */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Dividers
        </Typography>
        <Typography className="val-text-secondary">Standard Divider</Typography>
        <div className="val-divider" />
        <Typography className="val-text-secondary">Red Accent Divider</Typography>
        <div className="val-divider-red" />
      </Box>

      {/* Gradients */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Gradient Backgrounds
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <div className="val-gradient-bg" style={{ padding: '32px', borderRadius: '8px' }}>
              <Typography className="val-text-primary" align="center">
                Subtle Gradient
              </Typography>
            </div>
          </Grid>
          <Grid item xs={12} md={4}>
            <div className="val-gradient-red" style={{ padding: '32px', borderRadius: '8px' }}>
              <Typography style={{ color: 'white', fontWeight: 600 }} align="center">
                Red Gradient
              </Typography>
            </div>
          </Grid>
          <Grid item xs={12} md={4}>
            <div className="val-gradient-subtle" style={{ padding: '32px', borderRadius: '8px' }}>
              <Typography className="val-text-primary" align="center">
                Card Gradient
              </Typography>
            </div>
          </Grid>
        </Grid>
      </Box>

      {/* Animations */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" className="val-text-primary" gutterBottom>
          Animations
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper className="val-pulse" sx={{ 
              p: 3, 
              bgcolor: theme.palette.secondary.main,
              textAlign: 'center'
            }}>
              <Typography style={{ color: 'white', fontWeight: 600 }}>
                Pulse Animation
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper className="val-glow-pulse" sx={{ 
              p: 3, 
              bgcolor: theme.palette.background.paper,
              textAlign: 'center'
            }}>
              <Typography className="val-text-primary">
                Glow Pulse Animation
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Box>

    </Box>
  );
};

export default ThemeShowcase;
