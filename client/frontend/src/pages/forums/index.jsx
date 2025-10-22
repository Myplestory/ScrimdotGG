import React, { useState } from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemText, Chip, Avatar, Button } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import ForumIcon from '@mui/icons-material/Forum';
import PersonIcon from '@mui/icons-material/Person';
import AccessTimeIcon from '@mui/icons-material/AccessTime';

const ForumIndex = () => {
  const theme = useTheme();
  const navigate = useNavigate();

  // Sample forum categories and topics
  const forumCategories = [
    {
      id: 1,
      name: 'General Discussion',
      description: 'General chat about ScrimGG and Valorant',
      topics: 142,
      posts: 1823,
      lastPost: {
        title: 'Welcome to ScrimGG!',
        author: 'Admin',
        time: '2 hours ago'
      }
    },
    {
      id: 2,
      name: 'League Discussion',
      description: 'Talk about leagues, tournaments, and competitive play',
      topics: 87,
      posts: 934,
      lastPost: {
        title: 'Season 2 Registration Open',
        author: 'Moderator',
        time: '5 hours ago'
      }
    },
    {
      id: 3,
      name: 'Team Recruitment',
      description: 'Find teammates or recruit for your team',
      topics: 256,
      posts: 1456,
      lastPost: {
        title: 'LF Duelist for Competitive Team',
        author: 'PlayerOne',
        time: '1 hour ago'
      }
    },
    {
      id: 4,
      name: 'Bug Reports',
      description: 'Report bugs and technical issues',
      topics: 34,
      posts: 178,
      lastPost: {
        title: 'Queue Timer Issue',
        author: 'TestUser',
        time: '3 hours ago'
      }
    },
    {
      id: 5,
      name: 'Suggestions & Feedback',
      description: 'Share your ideas to improve ScrimGG',
      topics: 98,
      posts: 567,
      lastPost: {
        title: 'New Map Pool Suggestion',
        author: 'ProPlayer',
        time: '6 hours ago'
      }
    }
  ];

  return (
    <Box
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
        <Box>
          <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold', mb: 1 }}>
            Community Forums
          </Typography>
          <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
            Join the discussion with the ScrimGG community
          </Typography>
        </Box>
        <Button
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

      {/* Forum Categories */}
      <Box>
        {forumCategories.map((category) => (
          <Paper
            key={category.id}
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
                  <ForumIcon sx={{ color: theme.palette.secondary.main, mr: 1.5, fontSize: 28 }} />
                  <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 'bold' }}>
                    {category.name}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mb: 2 }}>
                  {category.description}
                </Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Chip
                    label={`${category.topics} Topics`}
                    size="small"
                    sx={{
                      backgroundColor: theme.palette.background.default,
                      color: theme.palette.text.secondary,
                    }}
                  />
                  <Chip
                    label={`${category.posts} Posts`}
                    size="small"
                    sx={{
                      backgroundColor: theme.palette.background.default,
                      color: theme.palette.text.secondary,
                    }}
                  />
                </Box>
              </Box>

              {/* Last Post Info */}
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
                  {category.lastPost.title}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <PersonIcon sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                      {category.lastPost.author}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <AccessTimeIcon sx={{ fontSize: 14, color: theme.palette.text.secondary }} />
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                      {category.lastPost.time}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
          </Paper>
        ))}
      </Box>

      {/* Forum Stats */}
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
              617
            </Typography>
            <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
              Total Topics
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>
              4,958
            </Typography>
            <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
              Total Posts
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>
              1,234
            </Typography>
            <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
              Total Members
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ForumIndex;
