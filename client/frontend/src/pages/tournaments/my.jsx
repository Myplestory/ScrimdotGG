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
  Tabs,
  Tab,
  Stack,
  LinearProgress,
  Divider
} from '@mui/material';
import { useMode } from '../../theme';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { ease } from '../../animations/gsapUtils';

const MyTournaments = () => {
  const [theme] = useMode();
  const [activeTab, setActiveTab] = useState(0);

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const statsRef = useRef(null);
  const tabsRef = useRef(null);
  const tournamentsRef = useRef(null);

  // Mock data for user's tournaments
  const myTournaments = {
    active: [
      {
        id: 1,
        name: 'Winter Championship 2025',
        status: 'registered',
        prizePool: 5000,
        entryFee: 50,
        startDate: '2025-11-15',
        currentRound: 'Waiting to Start',
        myTeam: 'Team Phoenix',
        seed: 12,
      },
      {
        id: 2,
        name: 'Autumn Legends Cup',
        status: 'playing',
        prizePool: 3000,
        entryFee: 30,
        startDate: '2025-10-20',
        currentRound: 'Round of 16',
        myTeam: 'Team Phoenix',
        wins: 2,
        losses: 0,
        nextMatch: '2025-10-22 18:00',
      },
    ],
    completed: [
      {
        id: 3,
        name: 'Halloween Spooky Cup',
        status: 'completed',
        prizePool: 2000,
        entryFee: 25,
        endDate: '2025-10-31',
        myTeam: 'Team Phoenix',
        placement: 3,
        prizeWon: 200,
        record: '4-2',
      },
      {
        id: 4,
        name: 'Weekly Clash #40',
        status: 'completed',
        prizePool: 500,
        entryFee: 10,
        endDate: '2025-10-10',
        myTeam: 'Team Phoenix',
        placement: 1,
        prizeWon: 300,
        record: '5-0',
      },
    ],
  };

  // User stats
  const userStats = {
    totalTournaments: 6,
    totalWinnings: 850,
    averagePlacement: 2.3,
    winRate: 73.5,
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'registered': return 'info';
      case 'playing': return 'success';
      case 'completed': return 'default';
      default: return 'default';
    }
  };

  const getPlacementMedal = (placement) => {
    if (placement === 1) return '🥇';
    if (placement === 2) return '🥈';
    if (placement === 3) return '🥉';
    return `#${placement}`;
  };

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    gsap.set([titleRef.current, statsRef.current, tabsRef.current], {
      opacity: 0,
      y: -20,
    });
    
    tl.to(titleRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.3,
      ease: ease.aggressive,
    })
    .to(statsRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.3,
      ease: ease.smooth,
    }, '-=0.15')
    .to(tabsRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.3,
      ease: ease.smooth,
    }, '-=0.15');
    
    return tl;
  }, []);

  const currentTournaments = activeTab === 0 ? myTournaments.active : myTournaments.completed;

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
            My Tournaments
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Track your tournament progress and history
          </Typography>
        </Box>

        {/* Stats Cards */}
        <Box ref={statsRef} sx={{ mb: 4 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: theme.palette.background.paper, border: `1px solid ${theme.palette.divider}` }}>
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="body2" color="text.secondary">
                      Total Tournaments
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {userStats.totalTournaments}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: theme.palette.background.paper, border: `1px solid ${theme.palette.divider}` }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                    <AttachMoneyIcon color="success" />
                    <Typography variant="body2" color="text.secondary">
                      Total Winnings
                    </Typography>
                  </Stack>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.success.main }}>
                    ${userStats.totalWinnings}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: theme.palette.background.paper, border: `1px solid ${theme.palette.divider}` }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                    <EmojiEventsIcon color="warning" />
                    <Typography variant="body2" color="text.secondary">
                      Avg. Placement
                    </Typography>
                  </Stack>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.warning.main }}>
                    {userStats.averagePlacement}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: theme.palette.background.paper, border: `1px solid ${theme.palette.divider}` }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                    <TrendingUpIcon color="primary" />
                    <Typography variant="body2" color="text.secondary">
                      Win Rate
                    </Typography>
                  </Stack>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
                    {userStats.winRate}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        {/* Tabs */}
        <Box ref={tabsRef} sx={{ mb: 3 }}>
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange}
            sx={{
              '& .MuiTab-root': {
                color: theme.palette.error.main,
                '&.Mui-selected': {
                  color: theme.palette.error.main,
                }
              },
              '& .MuiTabs-indicator': {
                backgroundColor: theme.palette.error.main,
              }
            }}
          >
            <Tab label="Active Tournaments" />
            <Tab label="Completed Tournaments" />
          </Tabs>
        </Box>

        {/* Tournaments List */}
        <Box ref={tournamentsRef} sx={{ pb: 6 }}>
          <Grid container spacing={3}>
            {currentTournaments.map((tournament) => (
              <Grid item xs={12} key={tournament.id}>
                <Card 
                  sx={{ 
                    background: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      borderColor: theme.palette.secondary.main,
                      boxShadow: `0 4px 12px ${theme.palette.secondary.main}40`,
                    }
                  }}
                >
                  <CardContent>
                    <Grid container spacing={3} alignItems="center">
                      {/* Tournament Info */}
                      <Grid item xs={12} md={6}>
                        <Stack spacing={1}>
                          <Stack direction="row" alignItems="center" spacing={2}>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {tournament.name}
                            </Typography>
                            <Chip 
                              label={tournament.status === 'registered' ? 'Registered' : tournament.status === 'playing' ? 'In Progress' : 'Completed'} 
                              color={getStatusColor(tournament.status)}
                              size="small"
                            />
                          </Stack>
                          <Typography variant="body2" color="text.secondary">
                            Team: {tournament.myTeam}
                          </Typography>
                        </Stack>
                      </Grid>

                      {/* Stats */}
                      <Grid item xs={12} md={6}>
                        <Grid container spacing={2}>
                          {tournament.status === 'completed' ? (
                            <>
                              <Grid item xs={4}>
                                <Stack>
                                  <Typography variant="body2" color="text.secondary">
                                    Placement
                                  </Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                    {getPlacementMedal(tournament.placement)}
                                  </Typography>
                                </Stack>
                              </Grid>
                              <Grid item xs={4}>
                                <Stack>
                                  <Typography variant="body2" color="text.secondary">
                                    Prize Won
                                  </Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 600, color: theme.palette.success.main }}>
                                    ${tournament.prizeWon}
                                  </Typography>
                                </Stack>
                              </Grid>
                              <Grid item xs={4}>
                                <Stack>
                                  <Typography variant="body2" color="text.secondary">
                                    Record
                                  </Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                    {tournament.record}
                                  </Typography>
                                </Stack>
                              </Grid>
                            </>
                          ) : (
                            <>
                              <Grid item xs={6}>
                                <Stack>
                                  <Typography variant="body2" color="text.secondary">
                                    Prize Pool
                                  </Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 600, color: theme.palette.warning.main }}>
                                    ${tournament.prizePool.toLocaleString()}
                                  </Typography>
                                </Stack>
                              </Grid>
                              <Grid item xs={6}>
                                <Stack>
                                  <Typography variant="body2" color="text.secondary">
                                    Current Round
                                  </Typography>
                                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                                    {tournament.currentRound}
                                  </Typography>
                                </Stack>
                              </Grid>
                            </>
                          )}
                        </Grid>
                      </Grid>

                      {/* Actions */}
                      <Grid item xs={12}>
                        <Divider sx={{ my: 1 }} />
                        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                          {tournament.status === 'playing' && (
                            <>
                              <Button 
                                variant="contained" 
                                size="small"
                                sx={{
                                  background: `linear-gradient(135deg, ${theme.palette.error.main} 0%, ${theme.palette.error.dark} 100%)`,
                                  '&:hover': {
                                    background: `linear-gradient(135deg, ${theme.palette.error.dark} 0%, ${theme.palette.error.main} 100%)`,
                                  }
                                }}
                              >
                                View Bracket
                              </Button>
                              {tournament.nextMatch && (
                                <Chip 
                                  label={`Next Match: ${new Date(tournament.nextMatch).toLocaleString()}`} 
                                  color="warning"
                                  size="small"
                                />
                              )}
                            </>
                          )}
                          {tournament.status === 'registered' && (
                            <Button 
                              variant="outlined" 
                              size="small"
                              sx={{
                                borderColor: theme.palette.error.main,
                                color: theme.palette.error.main,
                                '&:hover': {
                                  borderColor: theme.palette.error.dark,
                                  backgroundColor: `${theme.palette.error.main}10`,
                                }
                              }}
                            >
                              View Details
                            </Button>
                          )}
                          {tournament.status === 'completed' && (
                            <Button 
                              variant="outlined" 
                              size="small"
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
                        </Stack>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {currentTournaments.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary">
                No {activeTab === 0 ? 'active' : 'completed'} tournaments
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {activeTab === 0 ? 'Register for a tournament to get started' : 'Complete tournaments to see your history'}
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Container>
  );
};

export default MyTournaments;
