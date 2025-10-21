import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Chip,
  Avatar,
  LinearProgress,
  Container
} from '@mui/material';
import { useMode } from '../theme';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';

const LeagueStandings = () => {
  const [theme] = useMode();
  const [selectedDivision, setSelectedDivision] = useState(0);

  const divisions = [
    'Elite Division',
    'Premier Division', 
    'Advanced Division',
    'Open Division'
  ];

  const standingsData = {
    0: [
      { rank: 1, team: 'Cloud9 Blue', tag: 'C9B', wins: 12, losses: 2, winRate: 85.7, points: 36, streak: 'W5' },
      { rank: 2, team: 'Sentinels', tag: 'SEN', wins: 11, losses: 3, winRate: 78.6, points: 33, streak: 'W3' },
      { rank: 3, team: '100 Thieves', tag: '100T', wins: 10, losses: 4, winRate: 71.4, points: 30, streak: 'L1' },
      { rank: 4, team: 'Team Liquid', tag: 'TL', wins: 9, losses: 5, winRate: 64.3, points: 27, streak: 'W2' },
      { rank: 5, team: 'XSET', tag: 'XSET', wins: 7, losses: 7, winRate: 50.0, points: 21, streak: 'L2' },
      { rank: 6, team: 'OpTic Gaming', tag: 'OG', wins: 5, losses: 9, winRate: 35.7, points: 15, streak: 'L3' },
      { rank: 7, team: 'FaZe Clan', tag: 'FAZE', wins: 4, losses: 10, winRate: 28.6, points: 12, streak: 'W1' },
      { rank: 8, team: 'NRG', tag: 'NRG', wins: 2, losses: 12, winRate: 14.3, points: 6, streak: 'L5' },
    ],
    1: [
      { rank: 1, team: 'Rise Academy', tag: 'RISE', wins: 11, losses: 3, winRate: 78.6, points: 33, streak: 'W4' },
      { rank: 2, team: 'Ghost Gaming', tag: 'GG', wins: 10, losses: 4, winRate: 71.4, points: 30, streak: 'W2' },
      { rank: 3, team: 'Noble', tag: 'NBL', wins: 9, losses: 5, winRate: 64.3, points: 27, streak: 'L1' },
      { rank: 4, team: 'Complexity', tag: 'COL', wins: 8, losses: 6, winRate: 57.1, points: 24, streak: 'W1' },
      { rank: 5, team: 'Evil Geniuses', tag: 'EG', wins: 6, losses: 8, winRate: 42.9, points: 18, streak: 'L2' },
      { rank: 6, team: 'Immortals', tag: 'IMT', wins: 5, losses: 9, winRate: 35.7, points: 15, streak: 'W1' },
      { rank: 7, team: 'CLG', tag: 'CLG', wins: 4, losses: 10, winRate: 28.6, points: 12, streak: 'L3' },
      { rank: 8, team: 'TSM Academy', tag: 'TSMA', wins: 3, losses: 11, winRate: 21.4, points: 9, streak: 'L4' },
    ],
    2: [
      { rank: 1, team: 'Pioneers', tag: 'PIO', wins: 10, losses: 4, winRate: 71.4, points: 30, streak: 'W3' },
      { rank: 2, team: 'Challengers', tag: 'CHL', wins: 9, losses: 5, winRate: 64.3, points: 27, streak: 'W2' },
      { rank: 3, team: 'Rising Stars', tag: 'RS', wins: 8, losses: 6, winRate: 57.1, points: 24, streak: 'L1' },
      { rank: 4, team: 'Elite Force', tag: 'EF', wins: 7, losses: 7, winRate: 50.0, points: 21, streak: 'W1' },
      { rank: 5, team: 'Phoenix', tag: 'PHX', wins: 6, losses: 8, winRate: 42.9, points: 18, streak: 'L2' },
      { rank: 6, team: 'Warriors', tag: 'WAR', wins: 5, losses: 9, winRate: 35.7, points: 15, streak: 'W1' },
      { rank: 7, team: 'Thunder', tag: 'THU', wins: 4, losses: 10, winRate: 28.6, points: 12, streak: 'L3' },
      { rank: 8, team: 'Legends', tag: 'LEG', wins: 3, losses: 11, winRate: 21.4, points: 9, streak: 'L2' },
    ],
    3: [
      { rank: 1, team: 'Rookies United', tag: 'RU', wins: 9, losses: 5, winRate: 64.3, points: 27, streak: 'W4' },
      { rank: 2, team: 'New Wave', tag: 'NW', wins: 8, losses: 6, winRate: 57.1, points: 24, streak: 'W1' },
      { rank: 3, team: 'Uprising', tag: 'UP', wins: 7, losses: 7, winRate: 50.0, points: 21, streak: 'L1' },
      { rank: 4, team: 'Titans', tag: 'TIT', wins: 6, losses: 8, winRate: 42.9, points: 18, streak: 'W2' },
      { rank: 5, team: 'Storm', tag: 'STM', wins: 6, losses: 8, winRate: 42.9, points: 18, streak: 'L2' },
      { rank: 6, team: 'Velocity', tag: 'VEL', wins: 5, losses: 9, winRate: 35.7, points: 15, streak: 'L1' },
      { rank: 7, team: 'Mavericks', tag: 'MAV', wins: 4, losses: 10, winRate: 28.6, points: 12, streak: 'L3' },
      { rank: 8, team: 'Horizon', tag: 'HOR', wins: 3, losses: 11, winRate: 21.4, points: 9, streak: 'L5' },
    ],
  };

  const handleTabChange = (event, newValue) => {
    setSelectedDivision(newValue);
  };

  const getRankColor = (rank) => {
    if (rank === 1) return theme.palette.warning.main;
    if (rank === 2) return '#C0C0C0';
    if (rank === 3) return '#CD7F32';
    return theme.palette.text.primary;
  };

  const getStreakColor = (streak) => {
    return streak.startsWith('W') ? 'success' : 'error';
  };

  return (
    <Container maxWidth="xl" sx={{ height: '100%', overflow: 'hidden' }}>
      <Box sx={{ 
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: theme.palette.background.dark,
        padding: theme.spacing(3),
        overflow: 'hidden'
      }}>
        <Typography variant="h4" sx={{ mb: 3, color: theme.palette.secondary.main, flexShrink: 0 }}>
          League Divisions & Standings
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
            value={selectedDivision} 
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ 
              mb: 2,
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
            {divisions.map((division, index) => (
              <Tab key={index} label={division} />
            ))}
          </Tabs>

          <Typography variant="h5" sx={{ mb: 2, color: theme.palette.secondary.main }}>
            {divisions[selectedDivision]}
          </Typography>

          <TableContainer component={Paper} sx={{ 
            backgroundColor: theme.palette.background.default,
            boxShadow: 'none'
          }}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: theme.palette.background.dark }}>
                  <TableCell align="center" sx={{ fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.75rem' }}>Rank</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.75rem' }}>Team</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.75rem' }}>W</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.75rem' }}>L</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.75rem' }}>Win %</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.75rem' }}>Points</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.75rem' }}>Streak</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.75rem' }}>Form</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {standingsData[selectedDivision].map((team) => (
                  <TableRow 
                    key={team.rank}
                    sx={{ 
                      '&:hover': { 
                        backgroundColor: theme.palette.action.hover,
                        cursor: 'pointer',
                        transform: 'scale(1.001)',
                        transition: 'all 0.2s ease'
                      },
                      backgroundColor: team.rank <= 3 ? 'rgba(255, 215, 0, 0.05)' : 'transparent',
                      borderLeft: team.rank === 1 ? `3px solid #FFD700` : 
                                  team.rank === 2 ? `3px solid #C0C0C0` : 
                                  team.rank === 3 ? `3px solid #CD7F32` : 
                                  team.rank <= 4 ? `3px solid ${theme.palette.success.main}` : 'none'
                    }}
                  >
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                        {team.rank <= 3 && (
                          <EmojiEventsIcon 
                            sx={{ 
                              color: getRankColor(team.rank),
                              fontSize: '1.4rem',
                              filter: 'drop-shadow(0 0 4px rgba(255,215,0,0.3))'
                            }} 
                          />
                        )}
                        <Chip 
                          label={team.rank}
                          size="small"
                          sx={{
                            backgroundColor: team.rank <= 4 ? 'rgba(0,255,0,0.1)' : 'transparent',
                            color: team.rank <= 4 ? theme.palette.success.main : theme.palette.text.primary,
                            fontWeight: 'bold',
                            minWidth: '32px',
                            border: team.rank <= 4 ? `1px solid ${theme.palette.success.main}` : 'none'
                          }}
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar 
                          sx={{ 
                            width: 40, 
                            height: 40,
                            mr: 1.5,
                            border: `2px solid ${theme.palette.divider}`,
                            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                            bgcolor: theme.palette.secondary.main 
                          }}
                        >
                          {team.tag.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                            {team.team}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            [{team.tag}]
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Typography sx={{ color: 'success.main', fontWeight: 'bold' }}>
                        {team.wins}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography sx={{ color: 'error.main', fontWeight: 'bold' }}>
                        {team.losses}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography>{team.winRate.toFixed(1)}%</Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip 
                        label={team.points} 
                        size="small"
                        sx={{ 
                          fontWeight: 'bold',
                          backgroundColor: theme.palette.secondary.dark,
                          color: theme.palette.secondary.contrastText,
                          minWidth: '48px'
                        }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip 
                        label={team.streak} 
                        color={getStreakColor(team.streak)}
                        size="small"
                        sx={{
                          fontWeight: 'bold',
                          minWidth: '48px'
                        }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ width: 80 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={team.winRate} 
                          color={team.winRate >= 60 ? 'success' : team.winRate >= 40 ? 'warning' : 'error'}
                          sx={{ height: 8, borderRadius: 1 }}
                        />
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Grid container spacing={3} sx={{ mt: 2, pb: 6 }}>
        <Grid item xs={12} md={4}>
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
                Playoff Spots
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Top 4 teams advance to playoffs
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Chip label="Top 4" color="success" size="small" sx={{ mr: 1 }} />
                <Typography variant="caption" color="text.secondary">
                  Playoff Qualified
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
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
                Points System
              </Typography>
              <Typography variant="body2">Win: 3 points</Typography>
              <Typography variant="body2">Loss: 0 points</Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Tiebreaker: Head-to-head record
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
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
                Season Progress
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Week 7 of 14
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={50} 
                color="secondary"
                sx={{ height: 8, borderRadius: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      </Box>
      </Box>
    </Container>
  );
};

export default LeagueStandings;
