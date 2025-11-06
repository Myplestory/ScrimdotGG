import React, { useState, useRef, useEffect } from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemText, Chip, Avatar, Button, CircularProgress } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../../contexts/WebSocketContext';
import ForumIcon from '@mui/icons-material/Forum';
import PersonIcon from '@mui/icons-material/Person';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { staggerIn, fadeIn, ease } from '../../animations/gsapUtils';

const ForumIndex = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { connected, sendEvent, on } = useWebSocket();

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const buttonRef = useRef(null);

  // State
  const [forumCategories, setForumCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [forumStats, setForumStats] = useState({
    totalTopics: 0,
    totalPosts: 0,
    totalMembers: 0
  });

  // Fetch forum categories on mount
  useEffect(() => {
    if (connected) {
      console.log('[FORUM] Fetching forum categories');
      sendEvent('get_forum_categories', {});
    }
  }, [connected, sendEvent]);

  // WebSocket event listeners
  useEffect(() => {
    const unsubscribeCategories = on('forum_categories', (payload) => {
      console.log('[FORUM] Received forum categories:', payload);
      setForumCategories(payload.categories || []);
      
      // Calculate stats from categories
      const totalTopics = payload.categories.reduce((sum, cat) => sum + (cat.thread_count || 0), 0);
      const totalPosts = payload.categories.reduce((sum, cat) => sum + (cat.post_count || 0), 0);
      
      setForumStats({
        totalTopics,
        totalPosts,
        totalMembers: payload.total_members || 0
      });
      
      setLoading(false);
    });

    const unsubscribeError = on('error', (payload) => {
      console.error('[FORUM] Error:', payload.message);
      setError(payload.message);
      setLoading(false);
    });

    return () => {
      unsubscribeCategories();
      unsubscribeError();
    };
  }, [on]);

  const handleCategoryClick = (categorySlug) => {
    navigate(`/forum/${categorySlug}`);
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
    .from(buttonRef.current, {
      opacity: 0,
      x: 20,
      duration: 0.5,
      ease: ease.smooth,
    }, '-=0.4');
    
    return tl;
  }, []);

  return (
    <Box
      ref={containerRef}
      sx={{
        width: '100%',
        height: '100%',
        overflow: 'auto',
        p: 4,
        backgroundColor: theme.palette.background.default,
      }}
    >
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box ref={titleRef}>
          <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold', mb: 1 }}>
            Community Forums
          </Typography>
          <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
            Join the discussion with the ScrimGG community
          </Typography>
        </Box>
        <Button
          ref={buttonRef}
          variant="contained"
          color="secondary"
          onClick={() => navigate('/postnew')}
          sx={{
            px: 3,
            py: 1.5,
            fontWeight: 'bold',
            textTransform: 'none',
          }}
        >
          Create New Topic
        </Button>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
          <CircularProgress color="secondary" />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Paper sx={{ p: 3, backgroundColor: theme.palette.error.dark }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}

      {/* Forum Categories */}
      {!loading && !error && (
        <Box>
          {forumCategories.map((category) => (
            <Paper
              key={category.id}
              onClick={() => handleCategoryClick(category.slug)}
              sx={{
                mb: 2,
                p: 3,
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                transition: 'all 0.2s',
                '&:hover': {
                  borderColor: theme.palette.secondary.main,
                  transform: 'translateY(-2px)',
                  boxShadow: `0 4px 12px ${theme.palette.secondary.main}33`,
                },
                cursor: 'pointer',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                {/* Category Info */}
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <ForumIcon sx={{ color: category.color || theme.palette.secondary.main, mr: 1.5, fontSize: 28 }} />
                    <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 'bold' }}>
                      {category.name}
                    </Typography>
                    {category.is_locked && (
                      <Chip label="Locked" size="small" color="error" sx={{ ml: 2 }} />
                    )}
                  </Box>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mb: 2 }}>
                    {category.description}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Chip
                      label={`${category.thread_count || 0} Topics`}
                      size="small"
                      sx={{
                        backgroundColor: theme.palette.background.default,
                        color: theme.palette.text.secondary,
                      }}
                    />
                    <Chip
                      label={`${category.post_count || 0} Posts`}
                      size="small"
                      sx={{
                        backgroundColor: theme.palette.background.default,
                        color: theme.palette.text.secondary,
                      }}
                    />
                  </Box>
                </Box>

                {/* Last Post Info */}
                {category.latest_thread && (
                  <Box
                    sx={{
                      ml: 3,
                      minWidth: 250,
                      p: 2,
                      backgroundColor: theme.palette.background.default,
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, mb: 1, display: 'block' }}>
                      Last Post
                    </Typography>
                    <Typography variant="body2" sx={{ color: theme.palette.text.primary, fontWeight: 'bold', mb: 1 }}>
                      {category.latest_thread.title}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <PersonIcon sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
                        <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                          {category.latest_thread.author?.alias || 'Unknown'}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <AccessTimeIcon sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
                        <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                          {new Date(category.latest_thread.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                )}
              </Box>
            </Paper>
          ))}
        </Box>
      )}

      {/* Forum Stats */}
      {!loading && !error && (
        <Paper
          sx={{
            mt: 4,
            mb: 6,
            p: 3,
            backgroundColor: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography variant="h6" sx={{ color: theme.palette.text.primary, mb: 2, fontWeight: 'bold' }}>
            Forum Statistics
          </Typography>
          <Box sx={{ display: 'flex', gap: 4 }}>
            <Box>
              <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>
                {forumStats.totalTopics}
              </Typography>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                Total Topics
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>
                {forumStats.totalPosts}
              </Typography>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                Total Posts
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>
                {forumStats.totalMembers}
              </Typography>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                Total Members
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default ForumIndex;
