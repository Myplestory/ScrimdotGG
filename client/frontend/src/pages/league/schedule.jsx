import React, { useState } from 'react';
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
  Container
} from '@mui/material';
import { useMode } from '../../theme';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LocationOnIcon from '@mui/icons-material/LocationOn';

const LeagueSchedule = () => {
  const [theme] = useMode();
  const [selectedWeek, setSelectedWeek] = useState(6);

  const weeks = [
    'Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 
    'Week 6', 'Week 7', 'Week 8', 'Week 9', 'Week 10',
    'Week 11', 'Week 12', 'Week 13', 'Week 14', 'Playoffs'
  ];

  const scheduleData = {
    0: [
      { 
        id: 1, 
        homeTeam: 'Cloud9 Blue', 
        homeTag: 'C9B',
        awayTeam: 'Sentinels', 
        awayTag: 'SEN',
        date: '2025-10-22',
        time: '18:00 EST',
        status: 'scheduled',
        map: 'TBD'
      },
      { 
        id: 2, 
        homeTeam: '100 Thieves', 
        homeTag: '100T',
        awayTeam: 'Team Liquid', 
        awayTag: 'TL',
        date: '2025-10-22',
        time: '19:00 EST',
        status: 'scheduled',
        map: 'TBD'
      },
      { 
        id: 3, 
        homeTeam: 'XSET', 
        homeTag: 'XSET',
        awayTeam: 'OpTic Gaming', 
        awayTag: 'OG',
        date: '2025-10-23',
        time: '18:00 EST',
        status: 'scheduled',
        map: 'TBD'
      },
      { 
        id: 4, 
        homeTeam: 'FaZe Clan', 
        homeTag: 'FAZE',
        awayTeam: 'NRG', 
        awayTag: 'NRG',
        date: '2025-10-23',
        time: '19:00 EST',
        status: 'scheduled',
        map: 'TBD'
      },
    ],
    6: [
      { 
        id: 13, 
        homeTeam: 'Cloud9 Blue', 
        homeTag: 'C9B',
        awayTeam: 'XSET', 
        awayTag: 'XSET',
        date: '2025-10-21',
        time: '18:00 EST',
        status: 'completed',
        score: '2-0',
        map: 'Ascent'
      },
      { 
        id: 14, 
        homeTeam: 'Sentinels', 
        homeTag: 'SEN',
        awayTeam: '100 Thieves', 
        awayTag: '100T',
        date: '2025-10-21',
        time: '19:00 EST',
        status: 'live',
        score: '1-1',
        map: 'Haven'
      },
      { 
        id: 15, 
        homeTeam: 'Team Liquid', 
        homeTag: 'TL',
        awayTeam: 'OpTic Gaming', 
        awayTag: 'OG',
        date: '2025-10-22',
        time: '18:00 EST',
        status: 'scheduled',
        map: 'Bind'
      },
      { 
        id: 16, 
        homeTeam: 'FaZe Clan', 
        homeTag: 'FAZE',
        awayTeam: 'NRG', 
        awayTag: 'NRG',
        date: '2025-10-22',
        time: '19:00 EST',
        status: 'scheduled',
        map: 'Split'
      },
    ],
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
    return scheduleData[selectedWeek] || scheduleData[0];
  };

  return (
    <Container maxWidth="lg" sx={{ height: '100%', overflow: 'hidden' }}>
      <Box sx={{ 
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: theme.palette.background.dark,
        padding: theme.spacing(3),
        overflow: 'hidden'
      }}>
        <Typography variant="h4" sx={{ mb: 3, color: theme.palette.secondary.main, flexShrink: 0 }}>
          League Schedule
        </Typography>

      <Box sx={{ flex: 1, overflow: 'auto', pr: 1 }}>
      <Card sx={{ 
        backgroundColor: theme.palette.background.paper, 
        mb: 3,
        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        border: `1px solid ${theme.palette.divider}`
      }}>
        <CardContent>
          <Tabs 
            value={selectedWeek} 
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ 
              mb: 3,
              '& .MuiTabs-indicator': {
                backgroundColor: theme.palette.secondary.main,
                height: 3
              },
              '& .MuiTab-root': {
                color: theme.palette.text.secondary,
                fontWeight: 600,
                textTransform: 'uppercase',
                fontSize: '0.875rem',
                '&.Mui-selected': {
                  color: theme.palette.secondary.main
                },
                '&:hover': {
                  color: theme.palette.secondary.light
                }
              }
            }}
          >
            {weeks.map((week, index) => (
              <Tab 
                key={index} 
                label={week}
                icon={index === 6 ? <Chip label="Current" size="small" color="secondary" /> : null}
                iconPosition="end"
              />
            ))}
          </Tabs>

          <Typography variant="h5" sx={{ mb: 2, color: theme.palette.secondary.main }}>
            {weeks[selectedWeek]}
          </Typography>

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
