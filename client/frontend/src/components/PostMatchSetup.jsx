import React, { useEffect, useMemo, useState } from 'react';
import { Box, Card, CardContent, Typography, Button, Avatar, useTheme } from '@mui/material';
import { tokens } from '../theme';
import { mapImageUrl } from '../utils/maps';

const PostMatchSetup = ({
  finalMap,
  serverLocation,
  pregameStatus,          // 'connecting' | 'joined' | 'failed'
  connectDeadline,        // Date | ISO string (for 3:00 countdown)
  startedAt,              // Date | ISO string (when match begins)
  onManualConnect
}) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const [now, setNow] = useState(Date.now());
  const deadlineMs = useMemo(() => connectDeadline ? new Date(connectDeadline).getTime() : null, [connectDeadline]);
  const startedMs = useMemo(() => startedAt ? new Date(startedAt).getTime() : null, [startedAt]);
  const isInProgress = !!startedMs;

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const timeLabel = isInProgress ? 'Match in progress' : 'Time to connect';
  const timeValue = useMemo(() => {
    if (isInProgress) {
      const diff = Math.max(0, now - startedMs);
      const mm = Math.floor(diff / 60000);
      const ss = Math.floor((diff % 60000) / 1000);
      return `${String(mm).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;
    }
    if (!deadlineMs) return '—';
    const diff = Math.max(0, deadlineMs - now);
    const mm = Math.floor(diff / 60000);
    const ss = Math.floor((diff % 60000) / 1000);
    return `${String(mm).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;
  }, [isInProgress, now, startedMs, deadlineMs]);

  const statusText = pregameStatus === 'failed'
    ? 'Joining match failed. Use Manual Connect.'
    : pregameStatus === 'joined'
      ? 'Joined match successfully'
      : 'Waiting for players to connect…';

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, width: '100%', maxWidth: 400, mx: 'auto' }}>
      {/* Timer */}
      <Box sx={{ mb: 1 }}>
        <Box sx={{
          display: 'inline-flex', alignItems: 'center', gap: 0.75,
          bgcolor: colors.primary[500], px: 1.5, py: 0.5, borderRadius: '12px',
          border: `1px solid ${colors.seance[400]}`
        }}>
          <Typography variant="body2" sx={{ color: colors.grey[100], fontWeight: 700 }}>{timeLabel}</Typography>
          <Typography variant="body2" sx={{ color: colors.grey[100], fontWeight: 600 }}>{timeValue}</Typography>
        </Box>
      </Box>

      {/* Server Location Card */}
      <Card sx={{ width: '100%', backgroundColor: colors.grey[800], border: `1px solid ${colors.grey[600]}`, borderRadius: 2 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1.5, px: 2 }}>
          <Avatar sx={{ width: 24, height: 16, fontSize: '12px', backgroundColor: 'transparent' }}>🌍</Avatar>
          <Typography variant="body2" sx={{ color: colors.grey[100], fontWeight: 500 }}>
            {serverLocation || 'US-East'}
          </Typography>
        </CardContent>
      </Card>

      {/* Map Card */}
      <Card sx={{ width: '100%', backgroundColor: colors.grey[800], border: `1px solid ${colors.grey[600]}`, borderRadius: 2, overflow: 'hidden' }}>
        <Box sx={{
          position: 'relative', height: 120,
          backgroundImage: `url(${mapImageUrl(finalMap)})`,
          backgroundSize: 'cover', backgroundPosition: 'center',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <Box sx={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(0,0,0,0.4)' }} />
          <Typography variant="h5" sx={{ color: colors.grey[100], fontWeight: 'bold', textShadow: '2px 2px 4px rgba(0,0,0,0.8)', zIndex: 1 }}>
            {finalMap}
          </Typography>
        </Box>
      </Card>

      {/* CTA */}
      <Button
        variant="contained"
        color="primary"
        onClick={onManualConnect}
        sx={{ mt: 1, width: '100%', borderRadius: '10px', py: 1.25, fontWeight: 700, letterSpacing: 0.5 }}
      >
        Manual Connect
      </Button>
      <Typography variant="caption" sx={{ mt: 0.75, color: pregameStatus === 'failed' ? '#ff6b6b' : colors.grey[300] }}>
        {statusText}
      </Typography>
    </Box>
  );
};

export default PostMatchSetup;


