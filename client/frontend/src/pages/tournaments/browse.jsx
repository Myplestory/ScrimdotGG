import React, { useState, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Button,
  Chip,
  Container,
  TextField,
  InputAdornment,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Stack,
  Avatar,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import { useMode } from '../../theme';
import SearchIcon from '@mui/icons-material/Search';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import PeopleIcon from '@mui/icons-material/People';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { ease } from '../../animations/gsapUtils';

const BrowseTournaments = () => {
  const [theme] = useMode();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterFormat, setFilterFormat] = useState('all');

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const searchBarRef = useRef(null);
  const tournamentsGridRef = useRef(null);

  // Mock tournament data
  const tournaments = [
    {
      id: 1,
      name: 'Winter Championship 2025',
      status: 'open',
      format: 'Single Elimination',
      prizePool: 5000,
      entryFee: 50,
      participants: 45,
      maxParticipants: 64,
      startDate: '2025-11-15',
      organizer: 'ScrimGG Official',
      registrationDeadline: '2025-11-10',
    },
    {
      id: 2,
      name: 'Autumn Legends Cup',
      status: 'ongoing',
      format: 'Double Elimination',
      prizePool: 3000,
      entryFee: 30,
      participants: 32,
      maxParticipants: 32,
      startDate: '2025-10-20',
      organizer: 'Pro League',
      currentRound: 'Quarter Finals',
    },
    {
      id: 3,
      name: 'Rising Stars Tournament',
      status: 'open',
      format: 'Round Robin',
      prizePool: 1500,
      entryFee: 20,
      participants: 12,
      maxParticipants: 16,
      startDate: '2025-11-01',
      organizer: 'Community Events',
      registrationDeadline: '2025-10-28',
    },
    {
      id: 4,
      name: 'Halloween Spooky Cup',
      status: 'completed',
      format: 'Single Elimination',
      prizePool: 2000,
      entryFee: 25,
      participants: 32,
      maxParticipants: 32,
      startDate: '2025-10-31',
      organizer: 'Seasonal Events',
      winner: 'Team Phantom',
    },
    {
      id: 5,
      name: 'Weekly Clash #42',
      status: 'open',
      format: 'Single Elimination',
      prizePool: 500,
      entryFee: 10,
      participants: 18,
      maxParticipants: 32,
      startDate: '2025-10-25',
      organizer: 'Weekly Series',
      registrationDeadline: '2025-10-24',
    },
    {
      id: 6,
      name: 'Grand Masters Invitational',
      status: 'open',
      format: 'Double Elimination',
      prizePool: 10000,
      entryFee: 100,
      participants: 8,
      maxParticipants: 16,
      startDate: '2025-12-01',
      organizer: 'Elite Tournaments',
      registrationDeadline: '2025-11-20',
    },
  ];

  const getStatusColor = (status) => {
    switch(status) {
      case 'open': return 'success';
      case 'ongoing': return 'warning';
      case 'completed': return 'default';
      default: return 'default';
    }
  };

  const getStatusLabel = (status) => {
    switch(status) {
      case 'open': return 'Open for Registration';
      case 'ongoing': return 'In Progress';
      case 'completed': return 'Completed';
      default: return status;
    }
  };

  // Filter tournaments
  const filteredTournaments = tournaments.filter(tournament => {
    const matchesSearch = tournament.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         tournament.organizer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || tournament.status === filterStatus;
    const matchesFormat = filterFormat === 'all' || tournament.format === filterFormat;
    return matchesSearch && matchesStatus && matchesFormat;
  });

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    gsap.set([titleRef.current, searchBarRef.current], {
      opacity: 0,
      y: -20,
    });
    
    tl.to(titleRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.3,
      ease: ease.aggressive,
    })
    .to(searchBarRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.3,
      ease: ease.smooth,
    }, '-=0.15');
    
    // Animate tournament cards
    if (tournamentsGridRef.current) {
      const cards = tournamentsGridRef.current.querySelectorAll('.tournament-card');
      gsap.fromTo(cards, 
        {
          opacity: 0,
          y: 30,
        },
        {
          opacity: 1,
          y: 0,
          duration: 0.4,
          stagger: 0.08,
          ease: ease.smooth,
          delay: 0.3,
        }
      );
    }
    
    return tl;
  }, []);

  return (
    <Container maxWidth="xl" sx={{ height: '100%', overflow: 'auto', py: 4 }}>
      <Box ref={containerRef}>
        {/* Header */}
        <Box ref={titleRef} sx={{ mb: 4 }}>
          <Typography 
            variant="h3" 
            sx={{ 
              fontWeight: 700,
              background: `linear-gradient(135deg, ${theme.palette.secondary.main} 0%, ${theme.palette.secondary.light} 100%)`,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            Browse Tournaments
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Compete in tournaments, win prizes, and climb the ranks
          </Typography>
        </Box>

        {/* Search and Filters */}
        <Box ref={searchBarRef} sx={{ mb: 4 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search tournaments..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterStatus}
                  label="Status"
                  onChange={(e) => setFilterStatus(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="open">Open</MenuItem>
                  <MenuItem value="ongoing">Ongoing</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Format</InputLabel>
                <Select
                  value={filterFormat}
                  label="Format"
                  onChange={(e) => setFilterFormat(e.target.value)}
                >
                  <MenuItem value="all">All Formats</MenuItem>
                  <MenuItem value="Single Elimination">Single Elimination</MenuItem>
                  <MenuItem value="Double Elimination">Double Elimination</MenuItem>
                  <MenuItem value="Round Robin">Round Robin</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Box>

        {/* Tournament Grid */}
        <Box ref={tournamentsGridRef} sx={{ pb: 6 }}>
          <Grid container spacing={3}>
            {filteredTournaments.map((tournament) => (
              <Grid item xs={12} md={6} lg={4} key={tournament.id}>
                <Card 
                  className="tournament-card"
                  sx={{ 
                    height: '100%',
                    background: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: `0 8px 24px ${theme.palette.secondary.main}40`,
                      borderColor: theme.palette.secondary.main,
                    }
                  }}
                >
                  <CardContent>
                    {/* Tournament Header */}
                    <Box sx={{ mb: 2 }}>
                      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 1 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, flex: 1 }}>
                          {tournament.name}
                        </Typography>
                        <Chip 
                          label={getStatusLabel(tournament.status)} 
                          color={getStatusColor(tournament.status)}
                          size="small"
                        />
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        by {tournament.organizer}
                      </Typography>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    {/* Tournament Details */}
                    <Stack spacing={1.5}>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <EmojiEventsIcon fontSize="small" color="warning" />
                        <Typography variant="body2" color="text.secondary">
                          Prize Pool:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: theme.palette.warning.main }}>
                          ${tournament.prizePool.toLocaleString()}
                        </Typography>
                      </Stack>

                      <Stack direction="row" alignItems="center" spacing={1}>
                        <AttachMoneyIcon fontSize="small" color="success" />
                        <Typography variant="body2" color="text.secondary">
                          Entry Fee:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          ${tournament.entryFee}
                        </Typography>
                      </Stack>

                      <Stack direction="row" alignItems="center" spacing={1}>
                        <PeopleIcon fontSize="small" color="primary" />
                        <Typography variant="body2" color="text.secondary">
                          Participants:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {tournament.participants}/{tournament.maxParticipants}
                        </Typography>
                      </Stack>

                      <Stack direction="row" alignItems="center" spacing={1}>
                        <CalendarTodayIcon fontSize="small" color="info" />
                        <Typography variant="body2" color="text.secondary">
                          {tournament.status === 'completed' ? 'Ended:' : 'Starts:'}
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {new Date(tournament.startDate).toLocaleDateString()}
                        </Typography>
                      </Stack>

                      <Stack direction="row" alignItems="center" spacing={1}>
                        <InfoOutlinedIcon fontSize="small" />
                        <Typography variant="body2" color="text.secondary">
                          Format:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {tournament.format}
                        </Typography>
                      </Stack>

                      {tournament.status === 'ongoing' && tournament.currentRound && (
                        <Chip 
                          label={`Current: ${tournament.currentRound}`} 
                          color="warning" 
                          size="small"
                          sx={{ mt: 1 }}
                        />
                      )}

                      {tournament.status === 'completed' && tournament.winner && (
                        <Chip 
                          label={`Winner: ${tournament.winner}`} 
                          color="success" 
                          size="small"
                          icon={<EmojiEventsIcon />}
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Stack>

                    {/* Action Buttons */}
                    <Box sx={{ mt: 3 }}>
                      {tournament.status === 'open' && (
                        <Button 
                          variant="contained" 
                          fullWidth
                          sx={{
                            background: `linear-gradient(135deg, ${theme.palette.secondary.main} 0%, ${theme.palette.secondary.dark} 100%)`,
                            '&:hover': {
                              background: `linear-gradient(135deg, ${theme.palette.secondary.dark} 0%, ${theme.palette.secondary.main} 100%)`,
                            }
                          }}
                        >
                          Register Now
                        </Button>
                      )}
                      {tournament.status === 'ongoing' && (
                        <Button 
                          variant="outlined" 
                          fullWidth
                          sx={{
                            borderColor: theme.palette.error.main,
                            color: theme.palette.error.main,
                            '&:hover': {
                              borderColor: theme.palette.error.dark,
                              backgroundColor: `${theme.palette.error.main}10`,
                            }
                          }}
                        >
                          View Bracket
                        </Button>
                      )}
                      {tournament.status === 'completed' && (
                        <Button 
                          variant="outlined" 
                          fullWidth
                          sx={{
                            borderColor: theme.palette.error.main,
                            color: theme.palette.error.main,
                            '&:hover': {
                              borderColor: theme.palette.error.dark,
                              backgroundColor: `${theme.palette.error.main}10`,
                            }
                          }}
                        >
                          View Results
                        </Button>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {filteredTournaments.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary">
                No tournaments found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Try adjusting your search filters
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Container>
  );
};

export default BrowseTournaments;
