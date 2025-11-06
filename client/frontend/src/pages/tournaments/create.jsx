import React, { useState, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Button,
  Container,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Stack,
  Divider,
  InputAdornment,
  Stepper,
  Step,
  StepLabel,
  Alert,
  Slider,
  Chip
} from '@mui/material';
import { useMode } from '../../theme';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import PeopleIcon from '@mui/icons-material/People';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { ease } from '../../animations/gsapUtils';

const CreateTournament = () => {
  const [theme] = useMode();
  const [activeStep, setActiveStep] = useState(0);

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const formRef = useRef(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    format: 'single-elimination',
    maxParticipants: 16,
    entryFee: 0,
    sponsorPrize: 0,
    startDate: '',
    startTime: '',
    registrationDeadline: '',
    rules: '',
    prizeDistribution: [50, 30, 20], // 1st, 2nd, 3rd place percentages
  });

  const steps = ['Basic Info', 'Tournament Settings', 'Prize Pool & Fees', 'Review & Create'];

  const formatOptions = [
    { value: 'single-elimination', label: 'Single Elimination' },
    { value: 'double-elimination', label: 'Double Elimination' },
    { value: 'round-robin', label: 'Round Robin' },
    { value: 'swiss', label: 'Swiss System' },
  ];

  const participantOptions = [4, 8, 16, 32, 64, 128];

  // Calculate prize pool
  const totalEntryFees = formData.entryFee * formData.maxParticipants;
  const totalPrizePool = totalEntryFees + formData.sponsorPrize;
  const firstPlace = (totalPrizePool * formData.prizeDistribution[0]) / 100;
  const secondPlace = (totalPrizePool * formData.prizeDistribution[1]) / 100;
  const thirdPlace = (totalPrizePool * formData.prizeDistribution[2]) / 100;

  // Platform fee (10% of entry fees)
  const platformFee = totalEntryFees * 0.1;
  const netPrizePool = totalPrizePool - platformFee;

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNext = () => {
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handlePrizeDistributionChange = (index, value) => {
    const newDistribution = [...formData.prizeDistribution];
    newDistribution[index] = value;
    
    // Auto-adjust other values to maintain 100%
    const total = newDistribution.reduce((a, b) => a + b, 0);
    if (total > 100) {
      newDistribution[index] = 100 - newDistribution.filter((_, i) => i !== index).reduce((a, b) => a + b, 0);
    }
    
    setFormData(prev => ({
      ...prev,
      prizeDistribution: newDistribution
    }));
  };

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    gsap.set([titleRef.current, formRef.current], {
      opacity: 0,
      y: -20,
    });
    
    tl.to(titleRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.3,
      ease: ease.aggressive,
    })
    .to(formRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.3,
      ease: ease.smooth,
    }, '-=0.15');
    
    return tl;
  }, []);

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Stack spacing={3}>
            <TextField
              fullWidth
              label="Tournament Name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., Winter Championship 2025"
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              multiline
              rows={4}
              placeholder="Describe your tournament..."
            />
            <TextField
              fullWidth
              label="Tournament Rules"
              value={formData.rules}
              onChange={(e) => handleInputChange('rules', e.target.value)}
              multiline
              rows={6}
              placeholder="Enter tournament rules and regulations..."
            />
          </Stack>
        );

      case 1:
        return (
          <Stack spacing={3}>
            <FormControl fullWidth>
              <InputLabel>Tournament Format</InputLabel>
              <Select
                value={formData.format}
                label="Tournament Format"
                onChange={(e) => handleInputChange('format', e.target.value)}
              >
                {formatOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Max Participants</InputLabel>
              <Select
                value={formData.maxParticipants}
                label="Max Participants"
                onChange={(e) => handleInputChange('maxParticipants', e.target.value)}
              >
                {participantOptions.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option} Teams
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Start Date"
                  type="date"
                  value={formData.startDate}
                  onChange={(e) => handleInputChange('startDate', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Start Time"
                  type="time"
                  value={formData.startTime}
                  onChange={(e) => handleInputChange('startTime', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  required
                />
              </Grid>
            </Grid>

            <TextField
              fullWidth
              label="Registration Deadline"
              type="datetime-local"
              value={formData.registrationDeadline}
              onChange={(e) => handleInputChange('registrationDeadline', e.target.value)}
              InputLabelProps={{ shrink: true }}
              required
            />
          </Stack>
        );

      case 2:
        return (
          <Stack spacing={3}>
            <Alert severity="info" icon={<InfoOutlinedIcon />}>
              Platform fee: 10% of total entry fees. Sponsor prizes are not subject to fees.
            </Alert>

            <TextField
              fullWidth
              label="Entry Fee (per team)"
              type="number"
              value={formData.entryFee}
              onChange={(e) => handleInputChange('entryFee', parseFloat(e.target.value) || 0)}
              InputProps={{
                startAdornment: <InputAdornment position="start">$</InputAdornment>,
              }}
              helperText="Set to 0 for free tournaments"
            />

            <TextField
              fullWidth
              label="Sponsor Prize Contribution"
              type="number"
              value={formData.sponsorPrize}
              onChange={(e) => handleInputChange('sponsorPrize', parseFloat(e.target.value) || 0)}
              InputProps={{
                startAdornment: <InputAdornment position="start">$</InputAdornment>,
              }}
              helperText="Additional prize money you're contributing"
            />

            <Divider />

            <Card sx={{ background: theme.palette.background.default, border: `1px solid ${theme.palette.divider}` }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Prize Pool Breakdown
                </Typography>
                
                <Stack spacing={2}>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography color="text.secondary">Total Entry Fees ({formData.maxParticipants} teams × ${formData.entryFee}):</Typography>
                    <Typography fontWeight={600}>${totalEntryFees.toFixed(2)}</Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography color="text.secondary">Sponsor Contribution:</Typography>
                    <Typography fontWeight={600} color="success.main">+${formData.sponsorPrize.toFixed(2)}</Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography color="text.secondary">Platform Fee (10%):</Typography>
                    <Typography fontWeight={600} color="error.main">-${platformFee.toFixed(2)}</Typography>
                  </Stack>
                  <Divider />
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>Total Prize Pool:</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 700, color: theme.palette.warning.main }}>
                      ${netPrizePool.toFixed(2)}
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Prize Distribution
            </Typography>

            <Box>
              <Stack spacing={3}>
                <Box>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                    <Typography>1st Place</Typography>
                    <Chip label={`${formData.prizeDistribution[0]}% - $${firstPlace.toFixed(2)}`} color="warning" />
                  </Stack>
                  <Slider
                    value={formData.prizeDistribution[0]}
                    onChange={(e, value) => handlePrizeDistributionChange(0, value)}
                    min={0}
                    max={100}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}%`}
                  />
                </Box>

                <Box>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                    <Typography>2nd Place</Typography>
                    <Chip label={`${formData.prizeDistribution[1]}% - $${secondPlace.toFixed(2)}`} color="default" />
                  </Stack>
                  <Slider
                    value={formData.prizeDistribution[1]}
                    onChange={(e, value) => handlePrizeDistributionChange(1, value)}
                    min={0}
                    max={100}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}%`}
                  />
                </Box>

                <Box>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                    <Typography>3rd Place</Typography>
                    <Chip label={`${formData.prizeDistribution[2]}% - $${thirdPlace.toFixed(2)}`} />
                  </Stack>
                  <Slider
                    value={formData.prizeDistribution[2]}
                    onChange={(e, value) => handlePrizeDistributionChange(2, value)}
                    min={0}
                    max={100}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}%`}
                  />
                </Box>

                <Alert severity="warning">
                  Total distribution must equal 100%. Current: {formData.prizeDistribution.reduce((a, b) => a + b, 0)}%
                </Alert>
              </Stack>
            </Box>
          </Stack>
        );

      case 3:
        return (
          <Stack spacing={3}>
            <Alert severity="success">
              Review your tournament details before creating
            </Alert>

            <Card sx={{ background: theme.palette.background.default }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Tournament Details
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Name:</Typography>
                      <Typography fontWeight={600}>{formData.name || 'Not set'}</Typography>
                    </Stack>
                  </Grid>
                  <Grid item xs={12}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Format:</Typography>
                      <Typography fontWeight={600}>
                        {formatOptions.find(f => f.value === formData.format)?.label}
                      </Typography>
                    </Stack>
                  </Grid>
                  <Grid item xs={12}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Max Participants:</Typography>
                      <Typography fontWeight={600}>{formData.maxParticipants} teams</Typography>
                    </Stack>
                  </Grid>
                  <Grid item xs={12}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Start Date/Time:</Typography>
                      <Typography fontWeight={600}>{formData.startDate} {formData.startTime}</Typography>
                    </Stack>
                  </Grid>
                  <Grid item xs={12}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Entry Fee:</Typography>
                      <Typography fontWeight={600}>${formData.entryFee}</Typography>
                    </Stack>
                  </Grid>
                  <Grid item xs={12}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Prize Pool:</Typography>
                      <Typography fontWeight={600} color="warning.main">${netPrizePool.toFixed(2)}</Typography>
                    </Stack>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {formData.sponsorPrize > 0 && (
              <Alert severity="warning" icon={<AttachMoneyIcon />}>
                You will need to deposit ${formData.sponsorPrize.toFixed(2)} to create this tournament. 
                This amount will be held in escrow until the tournament completes.
              </Alert>
            )}
          </Stack>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ height: '100%', overflow: 'auto', py: 4, pb: 10 }}>
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
            Create Tournament
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Set up your own competitive tournament with custom rules and prizes
          </Typography>
        </Box>

        {/* Form */}
        <Box ref={formRef}>
          <Card sx={{ background: theme.palette.background.paper, border: `1px solid ${theme.palette.divider}` }}>
            <CardContent sx={{ p: 4 }}>
              {/* Stepper */}
              <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
                {steps.map((label) => (
                  <Step key={label}>
                    <StepLabel>{label}</StepLabel>
                  </Step>
                ))}
              </Stepper>

              {/* Step Content */}
              <Box sx={{ minHeight: '400px', mb: 4 }}>
                {renderStepContent(activeStep)}
              </Box>

              {/* Navigation Buttons */}
              <Stack direction="row" spacing={2} justifyContent="space-between">
                <Button
                  disabled={activeStep === 0}
                  onClick={handleBack}
                  variant="outlined"
                  sx={{
                    borderColor: theme.palette.error.main,
                    color: theme.palette.error.main,
                    '&:hover': {
                      borderColor: theme.palette.error.dark,
                      backgroundColor: `${theme.palette.error.main}10`,
                    },
                    '&.Mui-disabled': {
                      borderColor: theme.palette.divider,
                      color: theme.palette.text.disabled,
                    }
                  }}
                >
                  Back
                </Button>
                <Box sx={{ flex: 1 }} />
                {activeStep < steps.length - 1 ? (
                  <Button
                    variant="contained"
                    onClick={handleNext}
                    sx={{
                      background: `linear-gradient(135deg, ${theme.palette.secondary.main} 0%, ${theme.palette.secondary.dark} 100%)`,
                    }}
                  >
                    Next
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    sx={{
                      background: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
                    }}
                  >
                    Create Tournament
                  </Button>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Container>
  );
};

export default CreateTournament;
