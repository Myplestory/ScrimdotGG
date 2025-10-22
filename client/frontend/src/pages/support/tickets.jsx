import React, { useState } from 'react';
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
  Chip,
  List,
  ListItem,
  ListItemText,
  Tabs,
  Tab,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import SendIcon from '@mui/icons-material/Send';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PendingIcon from '@mui/icons-material/Pending';
import CancelIcon from '@mui/icons-material/Cancel';

const SupportTickets = () => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [showSuccess, setShowSuccess] = useState(false);

  const [formData, setFormData] = useState({
    category: '',
    priority: 'medium',
    subject: '',
    description: '',
  });

  const [errors, setErrors] = useState({});

  // Sample existing tickets
  const existingTickets = [
    {
      id: '#TICKET-1234',
      subject: 'Cannot connect to match',
      category: 'Technical Issue',
      status: 'open',
      priority: 'high',
      created: '2 hours ago',
      lastUpdate: '1 hour ago',
    },
    {
      id: '#TICKET-1189',
      subject: 'Missing league registration',
      category: 'Account',
      status: 'in-progress',
      priority: 'medium',
      created: '1 day ago',
      lastUpdate: '3 hours ago',
    },
    {
      id: '#TICKET-1156',
      subject: 'Question about league rules',
      category: 'General',
      status: 'resolved',
      priority: 'low',
      created: '3 days ago',
      lastUpdate: '2 days ago',
    },
  ];

  const categories = [
    'Technical Issue',
    'Account Problem',
    'Payment Issue',
    'League Question',
    'Report Player',
    'Bug Report',
    'Feature Request',
    'Other',
  ];

  const handleChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
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
    if (!formData.subject.trim()) {
      newErrors.subject = 'Subject is required';
    }
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formData.description.trim().length < 20) {
      newErrors.description = 'Please provide more details (minimum 20 characters)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      console.log('Submitting ticket:', formData);
      setShowSuccess(true);
      setFormData({
        category: '',
        priority: 'medium',
        subject: '',
        description: '',
      });
      setTimeout(() => setShowSuccess(false), 5000);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'open':
        return <PendingIcon sx={{ color: '#FFA726' }} />;
      case 'in-progress':
        return <PendingIcon sx={{ color: '#42A5F5' }} />;
      case 'resolved':
        return <CheckCircleIcon sx={{ color: '#66BB6A' }} />;
      default:
        return <CancelIcon sx={{ color: '#EF5350' }} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open':
        return '#FFA726';
      case 'in-progress':
        return '#42A5F5';
      case 'resolved':
        return '#66BB6A';
      default:
        return '#EF5350';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return '#EF5350';
      case 'medium':
        return '#FFA726';
      case 'low':
        return '#66BB6A';
      default:
        return theme.palette.text.secondary;
    }
  };

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
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SupportAgentIcon sx={{ fontSize: 40, color: theme.palette.secondary.main, mr: 2 }} />
          <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>
            Support Tickets
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ color: theme.palette.text.secondary }}>
          Submit a ticket or view your existing support requests
        </Typography>
      </Box>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onChange={(e, newValue) => setActiveTab(newValue)}
        sx={{
          mb: 3,
          borderBottom: `1px solid ${theme.palette.divider}`,
          '& .MuiTab-root': {
            textTransform: 'none',
            fontWeight: 'bold',
            fontSize: '1rem',
            minWidth: 150,
            color: theme.palette.text.secondary,
            '&.Mui-selected': {
              color: theme.palette.secondary.main,
            },
          },
          '& .MuiTabs-indicator': {
            backgroundColor: theme.palette.secondary.main,
            height: 3,
          },
        }}
      >
        <Tab label="My Tickets" />
        <Tab label="Submit New Ticket" />
      </Tabs>

      {/* My Tickets Tab */}
      {activeTab === 0 && (
        <Box sx={{ mb: 4 }}>
          <Paper
            sx={{
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <List sx={{ p: 0 }}>
              {existingTickets.map((ticket, index) => (
                <ListItem
                  key={ticket.id}
                  sx={{
                    borderBottom: index < existingTickets.length - 1 ? `1px solid ${theme.palette.divider}` : 'none',
                    p: 3,
                    '&:hover': {
                      backgroundColor: theme.palette.background.default,
                      cursor: 'pointer',
                    },
                  }}
                >
                  <Box sx={{ width: '100%' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {getStatusIcon(ticket.status)}
                          <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 'bold' }}>
                            {ticket.subject}
                          </Typography>
                        </Box>
                        <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                          {ticket.id} • {ticket.category}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          label={ticket.status.replace('-', ' ').toUpperCase()}
                          size="small"
                          sx={{
                            backgroundColor: getStatusColor(ticket.status),
                            color: 'white',
                            fontWeight: 'bold',
                          }}
                        />
                        <Chip
                          label={ticket.priority.toUpperCase()}
                          size="small"
                          sx={{
                            backgroundColor: getPriorityColor(ticket.priority),
                            color: 'white',
                            fontWeight: 'bold',
                          }}
                        />
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 3, mt: 2 }}>
                      <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                        Created: {ticket.created}
                      </Typography>
                      <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                        Last Update: {ticket.lastUpdate}
                      </Typography>
                    </Box>
                  </Box>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      )}

      {/* Submit New Ticket Tab */}
      {activeTab === 1 && (
        <Box>
          {showSuccess && (
            <Alert severity="success" sx={{ mb: 3 }}>
              Your ticket has been submitted successfully! We'll get back to you within 24-48 hours.
            </Alert>
          )}

          <Paper
            sx={{
              p: 4,
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
              maxWidth: 900,
            }}
          >
            {/* Category */}
            <FormControl fullWidth sx={{ mb: 3 }} error={!!errors.category}>
              <InputLabel>Category</InputLabel>
              <Select
                value={formData.category}
                label="Category"
                onChange={handleChange('category')}
                sx={{
                  backgroundColor: theme.palette.background.default,
                }}
              >
                {categories.map((category) => (
                  <MenuItem key={category} value={category}>
                    {category}
                  </MenuItem>
                ))}
              </Select>
              {errors.category && (
                <Typography variant="caption" sx={{ color: 'error.main', mt: 0.5 }}>
                  {errors.category}
                </Typography>
              )}
            </FormControl>

            {/* Priority */}
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Priority</InputLabel>
              <Select
                value={formData.priority}
                label="Priority"
                onChange={handleChange('priority')}
                sx={{
                  backgroundColor: theme.palette.background.default,
                }}
              >
                <MenuItem value="low">Low - General inquiry</MenuItem>
                <MenuItem value="medium">Medium - Issue affecting gameplay</MenuItem>
                <MenuItem value="high">High - Critical issue preventing play</MenuItem>
              </Select>
            </FormControl>

            {/* Subject */}
            <TextField
              fullWidth
              label="Subject"
              value={formData.subject}
              onChange={handleChange('subject')}
              error={!!errors.subject}
              helperText={errors.subject}
              sx={{
                mb: 3,
                '& .MuiInputBase-root': {
                  backgroundColor: theme.palette.background.default,
                },
              }}
              placeholder="Brief description of your issue"
            />

            {/* Description */}
            <TextField
              fullWidth
              multiline
              rows={8}
              label="Description"
              value={formData.description}
              onChange={handleChange('description')}
              error={!!errors.description}
              helperText={errors.description}
              sx={{
                mb: 3,
                '& .MuiInputBase-root': {
                  backgroundColor: theme.palette.background.default,
                },
              }}
              placeholder="Please provide detailed information about your issue..."
            />

            {/* Submit Button */}
            <Button
              variant="contained"
              color="secondary"
              startIcon={<SendIcon />}
              onClick={handleSubmit}
              sx={{
                px: 3,
                py: 1.5,
                textTransform: 'none',
                fontWeight: 'bold',
              }}
            >
              Submit Ticket
            </Button>
          </Paper>

          {/* Tips */}
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
              Tips for faster support
            </Typography>
            <Box component="ul" sx={{ color: theme.palette.text.secondary, pl: 2 }}>
              <li>Check the FAQ section first - your question might already be answered</li>
              <li>Choose the correct category for faster routing</li>
              <li>Provide as much detail as possible</li>
              <li>Include screenshots or error messages if applicable</li>
              <li>Mention your username and any relevant match/ticket IDs</li>
            </Box>
          </Paper>
        </Box>
      )}
    </Box>
  );
};

export default SupportTickets;
