import React, { useState, useRef } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Card, 
  CardContent,
  Grid,
  Alert,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Paper,
  Container,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  Tooltip
} from '@mui/material';
import { useMode } from '../../theme';
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { staggerIn, fadeIn, scaleIn, ease } from '../../animations/gsapUtils';

const LeagueCreateTeam = () => {
  const [theme] = useMode();
  const [teamName, setTeamName] = useState('');
  const [teamTag, setTeamTag] = useState('');
  const [teamLogo, setTeamLogo] = useState(null);
  const [teamLogoPreview, setTeamLogoPreview] = useState('');
  const [teamMembers, setTeamMembers] = useState([]);
  const [newMemberName, setNewMemberName] = useState('');
  const [newMemberPrimaryRole, setNewMemberPrimaryRole] = useState('Duelist');
  const [newMemberSecondaryRole, setNewMemberSecondaryRole] = useState('');
  const [newMemberTertiaryRole, setNewMemberTertiaryRole] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const teamInfoCardRef = useRef(null);
  const rosterCardRef = useRef(null);
  const buttonsRef = useRef(null);

  const availableRoles = ['Duelist', 'Controller', 'Initiator', 'Sentinel', 'Fill'];

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    tl.from(titleRef.current, {
      opacity: 0,
      y: -30,
      duration: 0.6,
      ease: ease.aggressive,
    })
    .from([teamInfoCardRef.current, rosterCardRef.current], {
      opacity: 0,
      y: 40,
      duration: 0.7,
      stagger: 0.15,
      ease: ease.smooth,
    }, '-=0.3')
    .from(buttonsRef.current, {
      opacity: 0,
      y: 20,
      duration: 0.5,
      ease: ease.snappy,
    }, '-=0.4');
    
    return tl;
  }, []);

  const handleLogoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        setError('Image size must be less than 5MB');
        return;
      }
      if (!file.type.startsWith('image/')) {
        setError('Please upload an image file');
        return;
      }
      setTeamLogo(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setTeamLogoPreview(reader.result);
      };
      reader.readAsDataURL(file);
      setError('');
    }
  };

  const handleAddMember = () => {
    if (!newMemberName.trim()) {
      setError('Player name cannot be empty');
      return;
    }
    
    if (teamMembers.length >= 7) {
      setError('Maximum 7 players allowed (5 starters + 2 substitutes)');
      return;
    }

    if (teamMembers.some(m => m.name.toLowerCase() === newMemberName.toLowerCase())) {
      setError('Player already added to the team');
      return;
    }

    setTeamMembers([...teamMembers, { 
      name: newMemberName, 
      primaryRole: newMemberPrimaryRole,
      secondaryRole: newMemberSecondaryRole || null,
      tertiaryRole: newMemberTertiaryRole || null
    }]);
    setNewMemberName('');
    setNewMemberPrimaryRole('Duelist');
    setNewMemberSecondaryRole('');
    setNewMemberTertiaryRole('');
    setError('');
  };

  const handleRemoveMember = (index) => {
    const newMembers = teamMembers.filter((_, i) => i !== index);
    setTeamMembers(newMembers);
  };

  const handleRoleChange = (index, roleType, newRole) => {
    const updatedMembers = teamMembers.map((member, i) => {
      if (i === index) {
        return { ...member, [roleType]: newRole || null };
      }
      return member;
    });
    setTeamMembers(updatedMembers);
  };

  const handleCreateTeam = () => {
    setError('');
    setSuccess('');

    if (!teamName.trim()) {
      setError('Team name is required');
      return;
    }

    if (!teamTag.trim()) {
      setError('Team tag is required');
      return;
    }

    if (teamTag.length > 4) {
      setError('Team tag must be 4 characters or less');
      return;
    }

    if (teamMembers.length < 5) {
      setError('Minimum 5 players required to create a team');
      return;
    }

    setSuccess('Team created successfully! Proceed to registration and payment.');
    
    setTimeout(() => {
      setTeamName('');
      setTeamTag('');
      setTeamLogo(null);
      setTeamLogoPreview('');
      setTeamMembers([]);
      setSuccess('');
    }, 3000);
  };

  return (
    <Container maxWidth="lg" sx={{ height: '100%', py: 0 }}>
      <Box 
        ref={containerRef}
        sx={{ 
          height: '100%',
          overflow: 'auto',
          backgroundColor: theme.palette.background.dark,
          padding: theme.spacing(4),
          paddingTop: theme.spacing(2)
        }}
      >
        <Typography 
          ref={titleRef}
          variant="h4" 
          sx={{ 
            mb: 2, 
            color: theme.palette.secondary.main,
            fontWeight: 700,
            letterSpacing: '0.02em',
          }}
        >
          Create Your League Team
        </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mt: -8 }}>
        <Grid item xs={12} md={6}>
          <Card 
            ref={teamInfoCardRef}
            sx={{ 
              backgroundColor: theme.palette.background.paper,
              boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
              border: `1px solid ${theme.palette.divider}`,
              transition: 'transform 0.3s ease, box-shadow 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: `0 8px 24px ${theme.palette.secondary.dark}25`,
              },
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography 
                variant="h6" 
                sx={{ 
                  mb: 3, 
                  color: theme.palette.secondary.main,
                  fontWeight: 600,
                }}
              >
                Team Information
              </Typography>
              
              <TextField
                fullWidth
                label="Team Name"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                sx={{ 
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    transition: 'all 0.3s ease',
                    '&:hover fieldset': {
                      borderColor: theme.palette.secondary.main,
                    },
                  },
                }}
                placeholder="e.g., Cloud9 Blue"
              />

              <TextField
                fullWidth
                label="Team Tag"
                value={teamTag}
                onChange={(e) => setTeamTag(e.target.value.toUpperCase())}
                inputProps={{ maxLength: 4 }}
                helperText="Maximum 4 characters"
                placeholder="e.g., C9B"
                sx={{ 
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    transition: 'all 0.3s ease',
                    '&:hover fieldset': {
                      borderColor: theme.palette.secondary.main,
                    },
                  },
                }}
              />

              <Box>
                <Typography variant="body2" sx={{ mb: 2, fontWeight: 600 }}>
                  Team Logo
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  {teamLogoPreview ? (
                    <Box
                      component="img"
                      src={teamLogoPreview}
                      alt="Team Logo Preview"
                      sx={{
                        width: 80,
                        height: 80,
                        borderRadius: 1,
                        objectFit: 'cover',
                        border: `2px solid ${theme.palette.divider}`,
                        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                        transition: 'transform 0.3s ease',
                        '&:hover': {
                          transform: 'scale(1.1)',
                        },
                      }}
                    />
                  ) : (
                    <Box
                      sx={{
                        width: 80,
                        height: 80,
                        borderRadius: 1,
                        border: `2px dashed ${theme.palette.divider}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundColor: theme.palette.background.default
                      }}
                    >
                      <Typography variant="caption" color="text.secondary">
                        No Logo
                      </Typography>
                    </Box>
                  )}
                  <Box>
                    <Button
                      variant="outlined"
                      component="label"
                      size="small"
                      color="secondary"
                      sx={{ 
                        mb: 1,
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          transform: 'translateX(4px)',
                        },
                      }}
                    >
                      Upload Logo
                      <input
                        type="file"
                        hidden
                        accept="image/*"
                        onChange={handleLogoUpload}
                      />
                    </Button>
                    <Typography variant="caption" display="block" color="text.secondary">
                      Max 5MB, JPG/PNG
                    </Typography>
                  </Box>
                </Box>
              </Box>

              <Box sx={{ mt: 4, p: 2, backgroundColor: theme.palette.background.default, borderRadius: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600, mb: 1 }}>
                  Team Requirements:
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  • Minimum 5 players (starters)
                </Typography>
                <Typography variant="caption" display="block">
                  • Maximum 7 players (5 starters + 2 substitutes)
                </Typography>
                <Typography variant="caption" display="block">
                  • Each player must have at least a primary role
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1.5, fontStyle: 'italic', color: theme.palette.secondary.light }}>
                  💡 Tip: Set role preferences (Primary → Secondary → Tertiary) for flexible team compositions
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card 
            ref={rosterCardRef}
            sx={{ 
              backgroundColor: theme.palette.background.paper,
              boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
              border: `1px solid ${theme.palette.divider}`,
              transition: 'transform 0.3s ease, box-shadow 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: `0 8px 24px ${theme.palette.secondary.dark}25`,
              },
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography 
                variant="h6" 
                sx={{ 
                  mb: 3, 
                  color: theme.palette.secondary.main,
                  fontWeight: 600,
                }}
              >
                Team Roster ({teamMembers.length}/7)
              </Typography>

              <Box sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  label="Player Name"
                  value={newMemberName}
                  onChange={(e) => setNewMemberName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddMember()}
                  placeholder="Enter player name or tag"
                  size="small"
                  sx={{
                    mb: 1.5,
                    '& .MuiOutlinedInput-root': {
                      transition: 'all 0.3s ease',
                      '&:hover fieldset': {
                        borderColor: theme.palette.secondary.main,
                      },
                    },
                  }}
                />
                
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1, fontWeight: 600 }}>
                  Role Preferences (Primary → Secondary → Tertiary)
                </Typography>
                
                <Stack direction="row" spacing={1} alignItems="center">
                  <FormControl size="small" sx={{ flex: 1 }}>
                    <InputLabel>Primary</InputLabel>
                    <Select
                      value={newMemberPrimaryRole}
                      label="Primary"
                      onChange={(e) => setNewMemberPrimaryRole(e.target.value)}
                    >
                      {availableRoles.map((role) => (
                        <MenuItem key={role} value={role}>{role}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <SwapVertIcon sx={{ color: theme.palette.text.disabled, fontSize: '1rem' }} />
                  
                  <FormControl size="small" sx={{ flex: 1 }}>
                    <InputLabel>Secondary</InputLabel>
                    <Select
                      value={newMemberSecondaryRole}
                      label="Secondary"
                      onChange={(e) => setNewMemberSecondaryRole(e.target.value)}
                    >
                      <MenuItem value="">None</MenuItem>
                      {availableRoles.filter(r => r !== newMemberPrimaryRole).map((role) => (
                        <MenuItem key={role} value={role}>{role}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <SwapVertIcon sx={{ color: theme.palette.text.disabled, fontSize: '1rem' }} />
                  
                  <FormControl size="small" sx={{ flex: 1 }}>
                    <InputLabel>Tertiary</InputLabel>
                    <Select
                      value={newMemberTertiaryRole}
                      label="Tertiary"
                      onChange={(e) => setNewMemberTertiaryRole(e.target.value)}
                    >
                      <MenuItem value="">None</MenuItem>
                      {availableRoles.filter(r => r !== newMemberPrimaryRole && r !== newMemberSecondaryRole).map((role) => (
                        <MenuItem key={role} value={role}>{role}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <IconButton 
                    color="secondary" 
                    onClick={handleAddMember}
                    disabled={teamMembers.length >= 7}
                    sx={{
                      transition: 'transform 0.2s ease',
                      '&:hover': {
                        transform: 'scale(1.1) rotate(90deg)',
                      },
                    }}
                  >
                    <AddCircleOutlineIcon />
                  </IconButton>
                </Stack>
              </Box>

              <Paper 
                sx={{ 
                  maxHeight: 300, 
                  overflow: 'auto',
                  backgroundColor: theme.palette.background.default,
                  border: `1px solid ${theme.palette.divider}`,
                }}
              >
                <List>
                  {teamMembers.length === 0 ? (
                    <ListItem>
                      <ListItemText 
                        primary="No players added yet"
                        secondary="Add at least 5 players to create your team"
                      />
                    </ListItem>
                  ) : (
                    teamMembers.map((member, index) => (
                      <ListItem 
                        key={index} 
                        divider
                        sx={{
                          transition: 'background-color 0.2s ease',
                          '&:hover': {
                            backgroundColor: theme.palette.action.hover,
                          },
                          flexDirection: 'column',
                          alignItems: 'flex-start',
                          py: 2,
                        }}
                      >
                        <Box sx={{ display: 'flex', width: '100%', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {member.name}
                          </Typography>
                          <IconButton 
                            edge="end" 
                            onClick={() => handleRemoveMember(index)}
                            size="small"
                            sx={{
                              transition: 'transform 0.2s ease',
                              '&:hover': {
                                transform: 'scale(1.2)',
                                color: '#ff4655',
                              },
                            }}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                        
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block', fontWeight: 600 }}>
                          Role Preferences
                        </Typography>
                        
                        <Stack direction="row" spacing={1} sx={{ width: '100%' }}>
                          <FormControl size="small" sx={{ flex: 1 }}>
                            <InputLabel>Primary</InputLabel>
                            <Select
                              value={member.primaryRole}
                              label="Primary"
                              onChange={(e) => handleRoleChange(index, 'primaryRole', e.target.value)}
                              variant="standard"
                            >
                              {availableRoles.map((role) => (
                                <MenuItem key={role} value={role}>{role}</MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                          
                          <SwapVertIcon sx={{ color: theme.palette.text.disabled, fontSize: '0.9rem', mt: 2 }} />
                          
                          <FormControl size="small" sx={{ flex: 1 }}>
                            <InputLabel>Secondary</InputLabel>
                            <Select
                              value={member.secondaryRole || ''}
                              label="Secondary"
                              onChange={(e) => handleRoleChange(index, 'secondaryRole', e.target.value)}
                              variant="standard"
                            >
                              <MenuItem value="">None</MenuItem>
                              {availableRoles.filter(r => r !== member.primaryRole).map((role) => (
                                <MenuItem key={role} value={role}>{role}</MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                          
                          <SwapVertIcon sx={{ color: theme.palette.text.disabled, fontSize: '0.9rem', mt: 2 }} />
                          
                          <FormControl size="small" sx={{ flex: 1 }}>
                            <InputLabel>Tertiary</InputLabel>
                            <Select
                              value={member.tertiaryRole || ''}
                              label="Tertiary"
                              onChange={(e) => handleRoleChange(index, 'tertiaryRole', e.target.value)}
                              variant="standard"
                            >
                              <MenuItem value="">None</MenuItem>
                              {availableRoles.filter(r => r !== member.primaryRole && r !== member.secondaryRole).map((role) => (
                                <MenuItem key={role} value={role}>{role}</MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Stack>
                        
                        <Box sx={{ mt: 1.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          <Chip 
                            label={member.primaryRole} 
                            size="small" 
                            color="secondary"
                            sx={{ fontWeight: 600 }}
                          />
                          {member.secondaryRole && (
                            <Chip 
                              label={member.secondaryRole} 
                              size="small" 
                              variant="outlined"
                              color="secondary"
                            />
                          )}
                          {member.tertiaryRole && (
                            <Chip 
                              label={member.tertiaryRole} 
                              size="small" 
                              variant="outlined"
                              sx={{ opacity: 0.7 }}
                            />
                          )}
                        </Box>
                      </ListItem>
                    ))
                  )}
                </List>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Box 
            ref={buttonsRef}
            sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}
          >
            <Button 
              variant="outlined"
              color="secondary"
              onClick={() => {
                setTeamName('');
                setTeamTag('');
                setTeamLogo(null);
                setTeamLogoPreview('');
                setTeamMembers([]);
                setError('');
                setSuccess('');
              }}
              sx={{
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 4px 12px ${theme.palette.secondary.dark}30`,
                },
              }}
            >
              Reset
            </Button>
            <Button 
              variant="contained" 
              color="secondary"
              onClick={handleCreateTeam}
              disabled={teamMembers.length < 5 || !teamName || !teamTag}
              sx={{
                px: 4,
                fontWeight: 600,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 6px 16px ${theme.palette.secondary.dark}40`,
                },
                '&:disabled': {
                  backgroundColor: theme.palette.action.disabledBackground,
                },
              }}
            >
              Create Team
            </Button>
          </Box>
        </Grid>
      </Grid>
      </Box>
    </Container>
  );
};

export default LeagueCreateTeam;
