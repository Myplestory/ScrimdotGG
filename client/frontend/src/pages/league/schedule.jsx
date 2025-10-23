import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Tabs,
  Tab,
  Chip,
  Avatar,
  Container,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  InputAdornment
} from '@mui/material';
import { useMode } from '../../theme';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import SearchIcon from '@mui/icons-material/Search';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { staggerIn, fadeIn, ease } from '../../animations/gsapUtils';

const LeagueSchedule = () => {
  const [theme] = useMode();
  const [selectedWeek, setSelectedWeek] = useState(6);
  const [selectedLeague, setSelectedLeague] = useState('advanced');
  const [selectedPhase, setSelectedPhase] = useState('regular');
  const [searchQuery, setSearchQuery] = useState('');
  const currentWeek = 6; // Week 7 is the current week

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const tabsRef = useRef(null);
  const matchesRef = useRef(null);

  // League structure similar to FACEIT/ESEA
  const leagues = [
    { id: 'open', name: 'Open Division', skill: 'Entry Level' },
    { id: 'intermediate', name: 'Intermediate Division', skill: 'Mid Level' },
    { id: 'advanced', name: 'Advanced Division', skill: 'High Level' },
    { id: 'premier', name: 'Premier Division', skill: 'Elite' }
  ];

  // Season phases like FACEIT/ESEA
  const phases = [
    { id: 'regular', name: 'Regular Season' },
    { id: 'playoffs', name: 'Playoffs' },
    { id: 'finals', name: 'Finals' }
  ];

  const weeks = [
    'Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 
    'Week 6', 'Week 7', 'Week 8', 'Week 9', 'Week 10',
    'Week 11', 'Week 12', 'Week 13', 'Week 14'
  ];

  // Helper to generate matches for weeks
  const generateWeekMatches = (weekNum, teams, startId) => {
    const dates = ['2025-10-22', '2025-10-23'];
    const times = ['18:00 EST', '19:00 EST', '20:00 EST'];
    const maps = ['Ascent', 'Haven', 'Bind', 'Split', 'Icebox', 'Breeze', 'TBD'];
    const statuses = weekNum < 6 ? ['completed'] : weekNum === 6 ? ['completed', 'live', 'scheduled'] : ['scheduled'];
    
    const matches = [];
    for (let i = 0; i < teams.length; i += 2) {
      if (i + 1 < teams.length) {
        const status = statuses[Math.floor(Math.random() * statuses.length)];
        matches.push({
          id: startId + i,
          homeTeam: teams[i].name,
          homeTag: teams[i].tag,
          homeHistory: teams[i].history,
          awayTeam: teams[i + 1].name,
          awayTag: teams[i + 1].tag,
          awayHistory: teams[i + 1].history,
          date: dates[Math.floor(i / 2) % dates.length],
          time: times[i % times.length],
          status: status,
          map: status === 'scheduled' ? 'TBD' : maps[Math.floor(Math.random() * (maps.length - 1))],
          ...(status === 'completed' && { score: `2-${Math.floor(Math.random() * 2)}` }),
          ...(status === 'live' && { score: `1-1` })
        });
      }
    }
    return matches;
  };

  const advancedTeams = [
    { name: 'Cloud9 Blue', tag: 'C9B', history: ['W', 'W', 'L', 'W', 'W'] },
    { name: 'Sentinels', tag: 'SEN', history: ['W', 'W', 'W', 'L', 'W'] },
    { name: '100 Thieves', tag: '100T', history: ['L', 'W', 'W', 'L', 'W'] },
    { name: 'Team Liquid', tag: 'TL', history: ['W', 'L', 'W', 'W', 'L'] },
    { name: 'XSET', tag: 'XSET', history: ['L', 'L', 'W', 'L', 'W'] },
    { name: 'OpTic Gaming', tag: 'OG', history: ['W', 'W', 'W', 'W', 'L'] },
    { name: 'FaZe Clan', tag: 'FAZE', history: ['W', 'L', 'L', 'W', 'W'] },
    { name: 'NRG', tag: 'NRG', history: ['L', 'W', 'W', 'L', 'L'] },
    { name: 'The Guard', tag: 'TGRD', history: ['W', 'L', 'W', 'L', 'W'] },
    { name: 'Evil Geniuses', tag: 'EG', history: ['L', 'L', 'W', 'W', 'L'] },
    { name: 'Version1', tag: 'V1', history: ['W', 'W', 'W', 'L', 'L'] },
    { name: 'Ghost Gaming', tag: 'GG', history: ['L', 'W', 'L', 'W', 'W'] },
  ];

  const intermediateTeams = [
    { name: 'Rebels Gaming', tag: 'RBL', history: ['W', 'L', 'W', 'W', 'L'] },
    { name: 'Phoenix Squad', tag: 'PHX', history: ['L', 'W', 'L', 'W', 'W'] },
    { name: 'Apex Legends', tag: 'APEX', history: ['W', 'W', 'L', 'L', 'W'] },
    { name: 'Titan Force', tag: 'TF', history: ['L', 'W', 'W', 'L', 'W'] },
    { name: 'Storm Surge', tag: 'SS', history: ['W', 'L', 'L', 'W', 'W'] },
    { name: 'Nova Elite', tag: 'NE', history: ['W', 'W', 'L', 'W', 'L'] },
    { name: 'Cipher Squad', tag: 'CS', history: ['L', 'W', 'W', 'W', 'L'] },
    { name: 'Vortex Gaming', tag: 'VG', history: ['W', 'L', 'W', 'L', 'W'] },
  ];

  // Schedule organized by league -> phase -> week
  const scheduleData = {
    advanced: {
      regular: Object.fromEntries(
        weeks.map((_, index) => [
          index,
          generateWeekMatches(index, advancedTeams, index * 100)
        ])
      ),
      playoffs: {
        0: [
          {
            id: 1400,
            homeTeam: 'Cloud9 Blue',
            homeTag: 'C9B',
            homeHistory: ['W', 'W', 'W', 'L', 'W'],
            awayTeam: 'Sentinels',
            awayTag: 'SEN',
            awayHistory: ['W', 'L', 'W', 'W', 'W'],
            date: '2025-11-15',
            time: '18:00 EST',
            status: 'scheduled',
            map: 'TBD',
            round: 'Quarterfinals'
          },
          {
            id: 1401,
            homeTeam: '100 Thieves',
            homeTag: '100T',
            homeHistory: ['W', 'W', 'L', 'W', 'W'],
            awayTeam: 'Team Liquid',
            awayTag: 'TL',
            awayHistory: ['L', 'W', 'W', 'W', 'L'],
            date: '2025-11-15',
            time: '19:00 EST',
            status: 'scheduled',
            map: 'TBD',
            round: 'Quarterfinals'
          }
        ]
      }
    },
    intermediate: {
      regular: Object.fromEntries(
        weeks.map((_, index) => [
          index,
          generateWeekMatches(index, intermediateTeams, index * 100 + 2000)
        ])
      )
    }
  };

  const handleTabChange = (event, newValue) => {
    setSelectedWeek(newValue);
  };

  const getStatusChip = (status) => {
    switch(status) {
      case 'completed':
        return <Chip label="Completed" color="success" size="small" />;
      case 'live':
        return <Chip label="🔴 LIVE" color="error" size="small" />;
      case 'scheduled':
        return <Chip label="Scheduled" color="default" size="small" />;
      default:
        return null;
    }
  };

  const getCurrentWeekData = () => {
    const leagueData = scheduleData[selectedLeague];
    if (!leagueData) return [];
    
    const phaseData = leagueData[selectedPhase];
    if (!phaseData) return [];
    
    let matches = phaseData[selectedWeek] || [];
    
    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      matches = matches.filter(match => 
        match.homeTeam.toLowerCase().includes(query) ||
        match.homeTag.toLowerCase().includes(query) ||
        match.awayTeam.toLowerCase().includes(query) ||
        match.awayTag.toLowerCase().includes(query)
      );
    }
    
    return matches;
  };

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    tl.from(titleRef.current, {
      opacity: 0,
      y: -30,
      duration: 0.6,
      ease: ease.aggressive,
    })
    .from(tabsRef.current, {
      opacity: 0,
      y: 20,
      duration: 0.5,
      ease: ease.smooth,
    }, '-=0.3');
    
    return tl;
  }, []);

  // Animate matches on week change
  useEffect(() => {
    if (matchesRef.current) {
      gsap.fromTo(matchesRef.current.children,
        {
          opacity: 0,
          y: 20,
        },
        {
          opacity: 1,
          y: 0,
          duration: 0.4,
          stagger: 0.08,
          ease: ease.snappy,
          clearProps: 'all',
        }
      );
    }
  }, [selectedWeek]);

  return (
    <Container maxWidth="lg" sx={{ height: '100%', overflow: 'hidden' }}>
      <Box 
        ref={containerRef}
        sx={{ 
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          backgroundColor: theme.palette.background.dark,
          padding: theme.spacing(4),
          paddingTop: theme.spacing(2),
          overflow: 'hidden'
        }}
      >
        {/* Top Row: Title + Week Navigation */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexShrink: 0 }}>
          <Typography 
            ref={titleRef}
            variant="h4" 
            sx={{ 
              color: theme.palette.secondary.main, 
              fontWeight: 700,
              letterSpacing: '0.02em',
            }}
          >
            League Schedule
          </Typography>

          {/* Week Selector */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label="Current Week"
              size="small"
              onClick={() => setSelectedWeek(currentWeek)}
              sx={{ 
                cursor: 'pointer',
                fontWeight: 600,
                backgroundColor: selectedWeek === currentWeek 
                  ? theme.palette.secondary.main 
                  : theme.palette.background.paper,
                color: selectedWeek === currentWeek 
                  ? '#fff' 
                  : theme.palette.text.secondary,
                '&:hover': {
                  backgroundColor: theme.palette.secondary.main,
                  color: '#fff'
                }
              }}
            />
            <IconButton 
              onClick={() => setSelectedWeek(prev => Math.max(0, prev - 1))}
              disabled={selectedWeek === 0}
              sx={{ 
                color: theme.palette.secondary.main,
                '&:disabled': { color: theme.palette.text.disabled }
              }}
            >
              <ChevronLeftIcon />
            </IconButton>
            <Typography variant="h6" sx={{ minWidth: 120, textAlign: 'center', fontWeight: 600 }}>
              {weeks[selectedWeek]}
            </Typography>
            <IconButton 
              onClick={() => setSelectedWeek(prev => Math.min(weeks.length - 1, prev + 1))}
              disabled={selectedWeek === weeks.length - 1}
              sx={{ 
                color: theme.palette.secondary.main,
                '&:disabled': { color: theme.palette.text.disabled }
              }}
            >
              <ChevronRightIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Bottom Row: Search + Dropdowns */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexShrink: 0 }}>
          {/* Search Function */}
          <TextField
            placeholder="Search teams..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            size="small"
            sx={{ 
              minWidth: 300,
              '& .MuiOutlinedInput-root': {
                backgroundColor: theme.palette.background.paper,
              }
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: theme.palette.text.secondary }} />
                </InputAdornment>
              ),
            }}
          />

          {/* Division and Phase Dropdowns */}
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControl sx={{ minWidth: 200 }} size="small">
              <InputLabel>Division</InputLabel>
              <Select
                value={selectedLeague}
                onChange={(e) => setSelectedLeague(e.target.value)}
                label="Division"
              >
                {leagues.map((league) => (
                  <MenuItem key={league.id} value={league.id}>
                    {league.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 200 }} size="small">
              <InputLabel>Phase</InputLabel>
              <Select
                value={selectedPhase}
                onChange={(e) => setSelectedPhase(e.target.value)}
                label="Phase"
              >
                {phases.map((phase) => (
                  <MenuItem key={phase.id} value={phase.id}>
                    {phase.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

      <Box sx={{ flex: 1, overflow: 'auto', pr: 1 }}>
      <Card 
        ref={tabsRef}
        sx={{ 
          backgroundColor: theme.palette.background.paper, 
          mb: 3,
          boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          border: `1px solid ${theme.palette.divider}`,
          transition: 'box-shadow 0.3s ease',
          '&:hover': {
            boxShadow: `0 6px 20px ${theme.palette.secondary.dark}20`,
          },
        }}
      >
        <CardContent>
          <Grid container spacing={2}>
            {getCurrentWeekData().map((match) => (
              <Grid item xs={12} key={match.id}>
                <Card sx={{ 
                  backgroundColor: theme.palette.background.default,
                  border: match.status === 'live' ? `2px solid ${theme.palette.error.main}` : `1px solid ${theme.palette.divider}`,
                  boxShadow: match.status === 'live' ? '0 0 20px rgba(255,0,0,0.3)' : '0 2px 8px rgba(0,0,0,0.3)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: match.status === 'live' ? '0 4px 24px rgba(255,0,0,0.4)' : '0 4px 12px rgba(0,0,0,0.4)'
                  }
                }}>
                  <CardContent>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} md={2}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          {getStatusChip(match.status)}
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <CalendarTodayIcon fontSize="small" color="action" />
                            <Typography variant="caption" color="text.secondary">
                              {match.date}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <AccessTimeIcon fontSize="small" color="action" />
                            <Typography variant="caption" color="text.secondary">
                              {match.time}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>

                      <Grid item xs={12} md={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          <Box sx={{ textAlign: 'right', mr: 2 }}>
                            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{match.homeTeam}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              [{match.homeTag}]
                            </Typography>
                            {match.homeHistory && (
                              <Typography 
                                variant="caption" 
                                sx={{ 
                                  display: 'block',
                                  mt: 0.5,
                                  fontWeight: 600,
                                  color: theme.palette.text.secondary
                                }}
                              >
                                {match.homeHistory.filter(r => r === 'W').length}W - {match.homeHistory.filter(r => r === 'L').length}L
                              </Typography>
                            )}
                          </Box>
                          <Avatar 
                            sx={{ 
                              width: 48, 
                              height: 48,
                              border: `2px solid ${theme.palette.divider}`,
                              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                              bgcolor: theme.palette.primary.main
                            }}
                          >
                            {match.homeTag.charAt(0)}
                          </Avatar>
                        </Box>
                      </Grid>

                      <Grid item xs={12} md={2}>
                        <Box sx={{ textAlign: 'center' }}>
                          {match.status === 'completed' || match.status === 'live' ? (
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: theme.palette.secondary.main }}>
                              {match.score}
                            </Typography>
                          ) : (
                            <Typography variant="h6" color="text.secondary">
                              VS
                            </Typography>
                          )}
                          {match.map && (
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5, mt: 1 }}>
                              <LocationOnIcon fontSize="small" color="action" />
                              <Typography variant="caption" color="text.secondary">
                                {match.map}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </Grid>

                      <Grid item xs={12} md={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar 
                            sx={{ 
                              width: 48, 
                              height: 48,
                              border: `2px solid ${theme.palette.divider}`,
                              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                              bgcolor: theme.palette.secondary.main 
                            }}
                          >
                            {match.awayTag.charAt(0)}
                          </Avatar>
                          <Box sx={{ ml: 2 }}>
                            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{match.awayTeam}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              [{match.awayTag}]
                            </Typography>
                            {match.awayHistory && (
                              <Typography 
                                variant="caption" 
                                sx={{ 
                                  display: 'block',
                                  mt: 0.5,
                                  fontWeight: 600,
                                  color: theme.palette.text.secondary
                                }}
                              >
                                {match.awayHistory.filter(r => r === 'W').length}W - {match.awayHistory.filter(r => r === 'L').length}L
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3} sx={{ pb: 6 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ 
            backgroundColor: theme.palette.background.paper,
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            border: `1px solid ${theme.palette.divider}`,
            transition: 'transform 0.2s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.4)'
            }
          }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, color: theme.palette.secondary.main }}>
                Match Times
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All match times are displayed in EST (Eastern Standard Time)
              </Typography>
              <Typography variant="body2" sx={{ mt: 2 }}>
                • Tuesday: 18:00 - 21:00 EST
              </Typography>
              <Typography variant="body2">
                • Wednesday: 18:00 - 21:00 EST
              </Typography>
              <Typography variant="body2">
                • Thursday: 18:00 - 21:00 EST
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ 
            backgroundColor: theme.palette.background.paper,
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            border: `1px solid ${theme.palette.divider}`,
            transition: 'transform 0.2s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.4)'
            }
          }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, color: theme.palette.secondary.main }}>
                Reschedule Policy
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Teams can request rescheduling up to 48 hours before match time
              </Typography>
              <Typography variant="body2" sx={{ mt: 2 }}>
                Contact: league@scrimgg.com
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      </Box>
      </Box>
    </Container>
  );
};

export default LeagueSchedule;
