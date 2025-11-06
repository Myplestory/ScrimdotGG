import React, { useState, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Container,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Stack,
  Avatar,
  Button,
  TextField,
  InputAdornment,
  MenuItem,
  Select,
  FormControl,
  InputLabel
} from '@mui/material';
import { useMode } from '../../theme';
import SearchIcon from '@mui/icons-material/Search';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { ease } from '../../animations/gsapUtils';

const TournamentHistory = () => {
  const [theme] = useMode();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPlacement, setFilterPlacement] = useState('all');

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const statsRef = useRef(null);
  const tableRef = useRef(null);

  // Mock historical data
  const history = [
    {
      id: 1,
      name: 'Halloween Spooky Cup',
      date: '2025-10-31',
      placement: 3,
      participants: 32,
      record: '4-2',
      prizeWon: 200,
      entryFee: 25,
      format: 'Single Elimination',
    },
    {
      id: 2,
      name: 'Weekly Clash #40',
      date: '2025-10-10',
      placement: 1,
      participants: 32,
      record: '5-0',
      prizeWon: 300,
      entryFee: 10,
      format: 'Single Elimination',
    },
    {
      id: 3,
      name: 'Summer Championship',
      date: '2025-08-15',
      placement: 5,
      participants: 64,
      record: '3-2',
      prizeWon: 50,
      entryFee: 50,
      format: 'Double Elimination',
    },
    {
      id: 4,
      name: 'Weekly Clash #38',
      date: '2025-09-25',
      placement: 2,
      participants: 16,
      record: '4-1',
      prizeWon: 150,
      entryFee: 10,
      format: 'Single Elimination',
    },
    {
      id: 5,
      name: 'Spring Invitational',
      date: '2025-04-20',
      placement: 8,
      participants: 32,
      record: '2-2',
      prizeWon: 0,
      entryFee: 30,
      format: 'Round Robin',
    },
    {
      id: 6,
      name: 'New Year Cup',
      date: '2025-01-01',
      placement: 1,
      participants: 16,
      record: '4-0',
      prizeWon: 400,
      entryFee: 20,
      format: 'Double Elimination',
    },
  ];

  // Calculate stats
  const totalTournaments = history.length;
  const totalWinnings = history.reduce((sum, t) => sum + t.prizeWon, 0);
  const totalSpent = history.reduce((sum, t) => sum + t.entryFee, 0);
  const netProfit = totalWinnings - totalSpent;
  const averagePlacement = (history.reduce((sum, t) => sum + t.placement, 0) / totalTournaments).toFixed(1);
  const wins = history.reduce((sum, t) => sum + parseInt(t.record.split('-')[0]), 0);
  const losses = history.reduce((sum, t) => sum + parseInt(t.record.split('-')[1]), 0);
  const winRate = ((wins / (wins + losses)) * 100).toFixed(1);
  const firstPlaceFinishes = history.filter(t => t.placement === 1).length;

  const getPlacementMedal = (placement) => {
    if (placement === 1) return '🥇';
    if (placement === 2) return '🥈';
    if (placement === 3) return '🥉';
    return `#${placement}`;
  };

  const getPlacementColor = (placement) => {
    if (placement === 1) return theme.palette.warning.main;
    if (placement === 2) return '#C0C0C0';
    if (placement === 3) return '#CD7F32';
    return theme.palette.text.primary;
  };

  // Filter history
  const filteredHistory = history.filter(tournament => {
    const matchesSearch = tournament.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPlacement = filterPlacement === 'all' || 
      (filterPlacement === 'podium' && tournament.placement <= 3) ||
      (filterPlacement === 'top5' && tournament.placement <= 5);
    return matchesSearch && matchesPlacement;
  });

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    gsap.set([titleRef.current, statsRef.current], {
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
    }, '-=0.15');
    
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
            Tournament History
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View your complete tournament performance history
          </Typography>
        </Box>

        {/* Stats Overview */}
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
                      {totalTournaments}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: theme.palette.background.paper, border: `1px solid ${theme.palette.divider}` }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                    {netProfit >= 0 ? (
                      <TrendingUpIcon color="success" />
                    ) : (
                      <TrendingDownIcon color="error" />
                    )}
                    <Typography variant="body2" color="text.secondary">
                      Net Profit/Loss
                    </Typography>
                  </Stack>
                  <Typography 
                    variant="h4" 
                    sx={{ 
                      fontWeight: 700, 
                      color: netProfit >= 0 ? theme.palette.success.main : theme.palette.error.main 
                    }}
                  >
                    {netProfit >= 0 ? '+' : ''}${netProfit}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ${totalWinnings} won - ${totalSpent} spent
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
                      Championships
                    </Typography>
                  </Stack>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.warning.main }}>
                    {firstPlaceFinishes}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Avg. Placement: {averagePlacement}
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
                  <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.success.main }}>
                    {winRate}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {wins}W - {losses}L
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        {/* Filters */}
        <Box sx={{ mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                placeholder="Search tournament history..."
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
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Filter by Placement</InputLabel>
                <Select
                  value={filterPlacement}
                  label="Filter by Placement"
                  onChange={(e) => setFilterPlacement(e.target.value)}
                >
                  <MenuItem value="all">All Placements</MenuItem>
                  <MenuItem value="podium">Podium (Top 3)</MenuItem>
                  <MenuItem value="top5">Top 5</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Box>

        {/* History Table */}
        <TableContainer 
          component={Paper}
          ref={tableRef}
          sx={{ 
            background: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
            mb: 6,
          }}
        >
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Tournament</TableCell>
                <TableCell align="center">Date</TableCell>
                <TableCell align="center">Format</TableCell>
                <TableCell align="center">Placement</TableCell>
                <TableCell align="center">Record</TableCell>
                <TableCell align="center">Entry Fee</TableCell>
                <TableCell align="center">Prize Won</TableCell>
                <TableCell align="center">Profit/Loss</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredHistory.map((tournament) => (
                <TableRow 
                  key={tournament.id}
                  sx={{ 
                    '&:hover': { 
                      backgroundColor: theme.palette.action.hover 
                    } 
                  }}
                >
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {tournament.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {tournament.participants} teams
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2">
                      {new Date(tournament.date).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2">
                      {tournament.format}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography 
                      variant="h6" 
                      sx={{ 
                        fontWeight: 700,
                        color: getPlacementColor(tournament.placement)
                      }}
                    >
                      {getPlacementMedal(tournament.placement)}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {tournament.record}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" color="error">
                      ${tournament.entryFee}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontWeight: 600,
                        color: tournament.prizeWon > 0 ? theme.palette.success.main : 'inherit'
                      }}
                    >
                      ${tournament.prizeWon}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontWeight: 700,
                        color: tournament.prizeWon - tournament.entryFee >= 0 
                          ? theme.palette.success.main 
                          : theme.palette.error.main
                      }}
                    >
                      {tournament.prizeWon - tournament.entryFee >= 0 ? '+' : ''}
                      ${tournament.prizeWon - tournament.entryFee}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Button 
                      size="small" 
                      variant="outlined"
                      sx={{
                        borderColor: theme.palette.error.main,
                        color: theme.palette.error.main,
                        '&:hover': {
                          borderColor: theme.palette.error.dark,
                          backgroundColor: `${theme.palette.error.main}10`,
                        }
                      }}
                    >
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {filteredHistory.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" color="text.secondary">
              No tournament history found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Try adjusting your search filters
            </Typography>
          </Box>
        )}
      </Box>
    </Container>
  );
};

export default TournamentHistory;
