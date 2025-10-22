import React, { useState } from 'react';
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
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, flexShrink: 0 }}>
          {activeStep > 0 && (
            <IconButton 
              onClick={handleBack}
              sx={{ mr: 2, color: theme.palette.secondary.main }}
            >
              <ArrowBackIcon />
            </IconButton>
          )}
          <Typography variant="h4" sx={{ color: theme.palette.secondary.main }}>
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

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Card sx={{ 
        backgroundColor: theme.palette.background.paper,
        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        border: `1px solid ${theme.palette.divider}`
      }}>
        <CardContent>
          {activeStep === 0 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2, color: theme.palette.secondary.main }}>
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
                      <Card key={team.id} sx={{ mb: 2, backgroundColor: theme.palette.background.default }}>
                        <CardContent>
                          <FormControlLabel 
                            value={team.id.toString()}
                            control={<Radio />}
                            label={
                              <Box>
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
            <Box>
              <Typography variant="h6" sx={{ mb: 2, color: theme.palette.secondary.main }}>
                Choose Your Division
              </Typography>
              
              <FormControl component="fieldset" fullWidth>
                <RadioGroup value={selectedDivision} onChange={(e) => setSelectedDivision(e.target.value)}>
                  {divisions.map((division) => (
                    <Card key={division.id} sx={{ mb: 2, backgroundColor: theme.palette.background.default }}>
                      <CardContent>
                        <FormControlLabel 
                          value={division.id.toString()}
                          control={<Radio />}
                          label={
                            <Box sx={{ width: '100%' }}>
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
            <Box>
              <Typography variant="h6" sx={{ mb: 2, color: theme.palette.secondary.main }}>
                Payment Information
              </Typography>

              <Card sx={{ 
                mb: 3, 
                backgroundColor: theme.palette.background.default,
                boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                border: `1px solid ${theme.palette.divider}`
              }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
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
                sx={{ mb: 3 }}
                placeholder="Enter promo code if you have one"
              />

              <Typography variant="h6" sx={{ mb: 2 }}>
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
