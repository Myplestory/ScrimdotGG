import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Button,
  Alert,
  Stepper,
  Step,
  StepLabel,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  TextField,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Container,
  IconButton
} from '@mui/material';
import { useMode } from '../../theme';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { fadeIn, staggerIn, scaleIn, ease } from '../../animations/gsapUtils';

const LeagueRegisterPay = () => {
  const [theme] = useMode();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedDivision, setSelectedDivision] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('');
  const [promoCode, setPromoCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const stepperRef = useRef(null);
  const cardRef = useRef(null);
  const buttonRef = useRef(null);

  const steps = ['Select Team', 'Choose Division', 'Payment'];

  const userTeams = [
    { id: 1, name: 'Cloud9 Blue', tag: 'C9B', members: 5 },
    { id: 2, name: 'Sentinels Academy', tag: 'SENA', members: 7 },
  ];

  const divisions = [
    { 
      id: 1, 
      name: 'Elite Division', 
      price: 99.99, 
      description: 'Top tier competitive play',
      requirements: 'Minimum Immortal rank'
    },
    { 
      id: 2, 
      name: 'Premier Division', 
      price: 74.99, 
      description: 'High level competitive matches',
      requirements: 'Minimum Diamond rank'
    },
    { 
      id: 3, 
      name: 'Advanced Division', 
      price: 49.99, 
      description: 'Competitive environment for improving teams',
      requirements: 'Minimum Platinum rank'
    },
    { 
      id: 4, 
      name: 'Open Division', 
      price: 29.99, 
      description: 'Entry level competitive league',
      requirements: 'All ranks welcome'
    },
  ];

  const handleNext = () => {
    if (activeStep === 0 && !selectedTeam) {
      setError('Please select a team');
      return;
    }
    if (activeStep === 1 && !selectedDivision) {
      setError('Please select a division');
      return;
    }
    if (activeStep === 2 && !paymentMethod) {
      setError('Please select a payment method');
      return;
    }
    
    setError('');
    
    if (activeStep === steps.length - 1) {
      handlePayment();
    } else {
      setActiveStep((prevStep) => prevStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
    setError('');
  };

  const handlePayment = () => {
    setSuccess('Registration successful! Your team has been registered for the league.');
    setTimeout(() => {
      setActiveStep(0);
      setSelectedTeam('');
      setSelectedDivision('');
      setPaymentMethod('');
      setPromoCode('');
      setSuccess('');
    }, 3000);
  };

  const getSelectedDivisionDetails = () => {
    return divisions.find(d => d.id.toString() === selectedDivision);
  };

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    tl.from(titleRef.current, {
      opacity: 0,
      x: -30,
      duration: 0.6,
      ease: ease.aggressive,
    })
    .from(stepperRef.current, {
      opacity: 0,
      y: 20,
      duration: 0.5,
      ease: ease.smooth,
    }, '-=0.3')
    .from(cardRef.current, {
      opacity: 0,
      y: 30,
      duration: 0.7,
      ease: ease.snappy,
    }, '-=0.3')
    // Immediately set step-content to visible after card animation
    .set('.step-content', { opacity: 1 }, '-=0.1');
    
    return tl;
  }, []);

  // Animate card content on step change (only after initial load)
  useEffect(() => {
    if (cardRef.current && activeStep !== 0) {
      // Only animate on step changes, not initial load
      gsap.fromTo(cardRef.current.querySelectorAll('.step-content'), 
        {
          opacity: 0,
          x: 20,
        },
        {
          opacity: 1,
          x: 0,
          duration: 0.5,
          ease: ease.smooth,
        }
      );
    }
  }, [activeStep]);

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
          overflow: 'hidden'
        }}
      >
        <Box 
          ref={titleRef}
          sx={{ display: 'flex', alignItems: 'center', mb: 3, flexShrink: 0 }}
        >
          {activeStep > 0 && (
            <IconButton 
              onClick={handleBack}
              sx={{ 
                mr: 2, 
                color: theme.palette.secondary.main,
                transition: 'transform 0.2s ease',
                '&:hover': {
                  transform: 'scale(1.1) translateX(-4px)',
                },
              }}
            >
              <ArrowBackIcon />
            </IconButton>
          )}
          <Typography 
            variant="h4" 
            sx={{ 
              color: theme.palette.secondary.main,
              fontWeight: 700,
              letterSpacing: '0.02em',
            }}
          >
            Register & Pay for League
          </Typography>
        </Box>

      <Box sx={{ flex: 1, overflow: 'auto', pr: 1, pb: 6 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Stepper 
        ref={stepperRef}
        activeStep={activeStep} 
        sx={{ 
          mb: 4,
          '& .MuiStepLabel-root .Mui-completed': {
            color: theme.palette.secondary.main,
          },
          '& .MuiStepLabel-root .Mui-active': {
            color: theme.palette.secondary.main,
          },
        }}
      >
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Card 
        ref={cardRef}
        sx={{ 
          backgroundColor: theme.palette.background.paper,
          boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          border: `1px solid ${theme.palette.divider}`,
          transition: 'box-shadow 0.3s ease',
          '&:hover': {
            boxShadow: `0 6px 20px ${theme.palette.secondary.dark}20`,
          },
        }}
      >
        <CardContent sx={{ p: 3 }}>
          {activeStep === 0 && (
            <Box className="step-content">
              <Typography 
                variant="h6" 
                sx={{ 
                  mb: 3, 
                  color: theme.palette.secondary.main,
                  fontWeight: 600,
                }}
              >
                Select Your Team
              </Typography>
              
              {userTeams.length === 0 ? (
                <Alert severity="info">
                  You don't have any teams yet. Please create a team first.
                </Alert>
              ) : (
                <FormControl component="fieldset" fullWidth>
                  <RadioGroup value={selectedTeam} onChange={(e) => setSelectedTeam(e.target.value)}>
                    {userTeams.map((team) => (
                      <Card 
                        key={team.id} 
                        sx={{ 
                          mb: 2, 
                          backgroundColor: theme.palette.background.default,
                          transition: 'all 0.3s ease',
                          cursor: 'pointer',
                          '&:hover': {
                            transform: 'translateX(8px)',
                            boxShadow: `0 4px 12px ${theme.palette.secondary.dark}20`,
                          },
                        }}
                        onClick={() => setSelectedTeam(team.id.toString())}
                      >
                        <CardContent>
                          <FormControlLabel 
                            value={team.id.toString()}
                            control={<Radio />}
                            sx={{ width: '100%', m: 0 }}
                            label={
                              <Box sx={{ ml: 1 }}>
                                <Typography variant="h6">
                                  {team.name} [{team.tag}]
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {team.members} members
                                </Typography>
                              </Box>
                            }
                          />
                        </CardContent>
                      </Card>
                    ))}
                  </RadioGroup>
                </FormControl>
              )}
            </Box>
          )}

          {activeStep === 1 && (
            <Box className="step-content">
              <Typography 
                variant="h6" 
                sx={{ 
                  mb: 3, 
                  color: theme.palette.secondary.main,
                  fontWeight: 600,
                }}
              >
                Choose Your Division
              </Typography>
              
              <FormControl component="fieldset" fullWidth>
                <RadioGroup value={selectedDivision} onChange={(e) => setSelectedDivision(e.target.value)}>
                  {divisions.map((division) => (
                    <Card 
                      key={division.id} 
                      sx={{ 
                        mb: 2, 
                        backgroundColor: theme.palette.background.default,
                        transition: 'all 0.3s ease',
                        cursor: 'pointer',
                        '&:hover': {
                          transform: 'translateX(8px)',
                          boxShadow: `0 4px 12px ${theme.palette.secondary.dark}20`,
                        },
                      }}
                      onClick={() => setSelectedDivision(division.id.toString())}
                    >
                      <CardContent>
                        <FormControlLabel 
                          value={division.id.toString()}
                          control={<Radio />}
                          sx={{ width: '100%', m: 0, alignItems: 'flex-start' }}
                          label={
                            <Box sx={{ width: '100%', ml: 1 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="h6">
                                  {division.name}
                                </Typography>
                                <Chip 
                                  label={`$${division.price}`} 
                                  color="secondary"
                                  size="small"
                                />
                              </Box>
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                {division.description}
                              </Typography>
                              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                Requirements: {division.requirements}
                              </Typography>
                            </Box>
                          }
                        />
                      </CardContent>
                    </Card>
                  ))}
                </RadioGroup>
              </FormControl>
            </Box>
          )}

          {activeStep === 2 && (
            <Box className="step-content">
              <Typography 
                variant="h6" 
                sx={{ 
                  mb: 3, 
                  color: theme.palette.secondary.main,
                  fontWeight: 600,
                }}
              >
                Payment Information
              </Typography>

              <Card sx={{ 
                mb: 3, 
                backgroundColor: theme.palette.background.default,
                boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                border: `1px solid ${theme.palette.divider}`
              }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                    Order Summary
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  <List>
                    <ListItem>
                      <ListItemText primary="Division" />
                      <Typography>
                        {getSelectedDivisionDetails()?.name}
                      </Typography>
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Price" />
                      <Typography>
                        ${getSelectedDivisionDetails()?.price}
                      </Typography>
                    </ListItem>
                    <Divider />
                    <ListItem>
                      <ListItemText 
                        primary={<Typography variant="h6">Total</Typography>} 
                      />
                      <Typography variant="h6" color="secondary">
                        ${getSelectedDivisionDetails()?.price}
                      </Typography>
                    </ListItem>
                  </List>
                </CardContent>
              </Card>

              <TextField
                fullWidth
                label="Promo Code"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value)}
                sx={{ 
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    transition: 'all 0.3s ease',
                    '&:hover fieldset': {
                      borderColor: theme.palette.secondary.main,
                    },
                  },
                }}
                placeholder="Enter promo code if you have one"
              />

              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Payment Method
              </Typography>
              
              <FormControl component="fieldset" fullWidth>
                <RadioGroup value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
                  <FormControlLabel 
                    value="stripe" 
                    control={<Radio />} 
                    label="Credit/Debit Card (Stripe)" 
                  />
                  <FormControlLabel 
                    value="paypal" 
                    control={<Radio />} 
                    label="PayPal" 
                  />
                </RadioGroup>
              </FormControl>
            </Box>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
            <Button
              variant="contained"
              color="secondary"
              onClick={handleNext}
              sx={{
                px: 4,
                py: 1.5,
                fontWeight: 600,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 6px 16px ${theme.palette.secondary.dark}40`,
                },
              }}
            >
              {activeStep === steps.length - 1 ? 'Complete Payment' : 'Next'}
            </Button>
          </Box>
        </CardContent>
      </Card>
      </Box>
      </Box>
    </Container>
  );
};

export default LeagueRegisterPay;
