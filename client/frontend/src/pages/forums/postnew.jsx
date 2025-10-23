import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../../contexts/WebSocketContext';
import SendIcon from '@mui/icons-material/Send';
import CancelIcon from '@mui/icons-material/Cancel';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { staggerIn, fadeIn, ease } from '../../animations/gsapUtils';

const PostNew = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { connected, sendEvent, on } = useWebSocket();

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const formRef = useRef(null);

  const [formData, setFormData] = useState({
    category: '',
    title: '',
    content: '',
  });

  const [errors, setErrors] = useState({});
  const [showSuccess, setShowSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [categories, setCategories] = useState([]);

  // Fetch categories on mount
  useEffect(() => {
    if (connected) {
      console.log('[FORUM] Fetching categories for new thread');
      sendEvent('get_forum_categories', {});
    }
  }, [connected, sendEvent]);

  // WebSocket event listeners
  useEffect(() => {
    const unsubscribeCategories = on('forum_categories', (payload) => {
      console.log('[FORUM] Received categories:', payload);
      setCategories(payload.categories || []);
    });

    const unsubscribeThreadCreated = on('thread_created', (payload) => {
      console.log('[FORUM] Thread created:', payload);
      setShowSuccess(true);
      setSubmitting(false);
      setTimeout(() => {
        navigate(`/forum/${payload.thread.category.slug}`);
      }, 2000);
    });

    const unsubscribeError = on('error', (payload) => {
      console.error('[FORUM] Error:', payload.message);
      setErrors({ submit: payload.message });
      setSubmitting(false);
    });

    return () => {
      unsubscribeCategories();
      unsubscribeThreadCreated();
      unsubscribeError();
    };
  }, [on, navigate]);

  const handleChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
    // Clear error for this field
    if (errors[field]) {
      setErrors({
        ...errors,
        [field]: '',
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.category) {
      newErrors.category = 'Please select a category';
    }
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.trim().length < 5) {
      newErrors.title = 'Title must be at least 5 characters';
    }
    if (!formData.content.trim()) {
      newErrors.content = 'Content is required';
    } else if (formData.content.trim().length < 20) {
      newErrors.content = 'Content must be at least 20 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      setSubmitting(true);
      
      // Find selected category object
      const selectedCategory = categories.find(cat => cat.name === formData.category);
      
      console.log('[FORUM] Creating thread:', formData);
      sendEvent('create_forum_thread', {
        category_slug: selectedCategory?.slug || formData.category.toLowerCase().replace(/\s+/g, '-'),
        title: formData.title,
        content: formData.content,
        tags: [] // Can add tag selection later
      });
    }
  };

  const handleCancel = () => {
    navigate('/forumindex');
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
    .from(formRef.current, {
      opacity: 0,
      y: 30,
      duration: 0.6,
      ease: ease.smooth,
    }, '-=0.3');
    
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
      <Box ref={titleRef} sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold', mb: 1 }}>
          Create New Topic
        </Typography>
        <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
          Start a new discussion with the community
        </Typography>
      </Box>

      {/* Success Alert */}
      {showSuccess && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Topic created successfully! Redirecting to forum...
        </Alert>
      )}

      {/* Form */}
      <Paper
        ref={formRef}
        sx={{
          p: 4,
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          maxWidth: 900,
        }}
      >
        {/* Category Selection */}
        <FormControl fullWidth sx={{ mb: 3 }} error={!!errors.category}>
          <InputLabel>Category</InputLabel>
          <Select
            value={formData.category}
            label="Category"
            onChange={handleChange('category')}
            disabled={categories.length === 0}
            sx={{
              backgroundColor: theme.palette.background.default,
            }}
          >
            {categories.map((category) => (
              <MenuItem key={category.id} value={category.name}>
                {category.name}
              </MenuItem>
            ))}
          </Select>
          {errors.category && (
            <Typography variant="caption" sx={{ color: 'error.main', mt: 0.5 }}>
              {errors.category}
            </Typography>
          )}
          {categories.length === 0 && (
            <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5 }}>
              Loading categories...
            </Typography>
          )}
        </FormControl>

        {/* Title Input */}
        <TextField
          fullWidth
          label="Topic Title"
          value={formData.title}
          onChange={handleChange('title')}
          error={!!errors.title}
          helperText={errors.title}
          sx={{
            mb: 3,
            '& .MuiInputBase-root': {
              backgroundColor: theme.palette.background.default,
            },
          }}
          placeholder="Enter a descriptive title for your topic"
        />

        {/* Content Input */}
        <TextField
          fullWidth
          multiline
          rows={12}
          label="Content"
          value={formData.content}
          onChange={handleChange('content')}
          error={!!errors.content}
          helperText={errors.content}
          sx={{
            mb: 3,
            '& .MuiInputBase-root': {
              backgroundColor: theme.palette.background.default,
            },
          }}
          placeholder="Write your message here..."
        />

        {/* Character Count */}
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            textAlign: 'right',
            color: theme.palette.text.secondary,
            mb: 3,
          }}
        >
          {formData.content.length} characters
        </Typography>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            startIcon={<CancelIcon />}
            onClick={handleCancel}
            disabled={submitting}
            sx={{
              px: 3,
              py: 1,
              textTransform: 'none',
              borderColor: theme.palette.divider,
              color: theme.palette.text.secondary,
              '&:hover': {
                borderColor: theme.palette.text.primary,
                backgroundColor: 'transparent',
              },
            }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={submitting ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            onClick={handleSubmit}
            disabled={submitting}
            sx={{
              px: 3,
              py: 1,
              textTransform: 'none',
              fontWeight: 'bold',
            }}
          >
            {submitting ? 'Creating...' : 'Post Topic'}
          </Button>
        </Box>
        
        {/* Submit Error */}
        {errors.submit && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {errors.submit}
          </Alert>
        )}
      </Paper>

      {/* Guidelines */}
      <Paper
        sx={{
          mt: 3,
          mb: 6,
          p: 3,
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          maxWidth: 900,
        }}
      >
        <Typography variant="h6" sx={{ color: theme.palette.text.primary, mb: 2, fontWeight: 'bold' }}>
          Posting Guidelines
        </Typography>
        <Box component="ul" sx={{ color: theme.palette.text.secondary, pl: 2 }}>
          <li>Be respectful and courteous to other community members</li>
          <li>Choose the appropriate category for your topic</li>
          <li>Use a clear and descriptive title</li>
          <li>Provide enough detail in your post</li>
          <li>Search for existing topics before creating a duplicate</li>
          <li>No spam, advertising, or self-promotion</li>
        </Box>
      </Paper>
    </Box>
  );
};

export default PostNew;
