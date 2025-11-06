import React, { useState, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  Container
} from '@mui/material';
import { useMode } from '../../theme';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import GavelIcon from '@mui/icons-material/Gavel';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { gsap } from 'gsap';
import { usePageEnter } from '../../animations/useGSAP';
import { staggerIn, fadeIn, ease } from '../../animations/gsapUtils';

const LeagueRules = () => {
  const [theme] = useMode();
  const [expanded, setExpanded] = useState(false); // Changed from 'general' to false

  // Animation refs
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const alertRef = useRef(null);
  const accordionsRef = useRef(null);

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false);
  };

  // Page enter animations
  usePageEnter(containerRef, () => {
    const tl = gsap.timeline();
    
    // Set initial states immediately
    gsap.set(titleRef.current, {
      opacity: 0,
      y: -30,
    });
    
    gsap.set(alertRef.current, {
      opacity: 0,
      y: 20,
    });
    
    gsap.set(accordionsRef.current.children, {
      opacity: 0,
      y: 30,
    });
    
    // Animate to final states
    tl.to(titleRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.2,
      ease: ease.smooth,
    })
    .to(alertRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.15,
      ease: ease.smooth,
    }, '-=0.1')
    .to(accordionsRef.current.children, {
      opacity: 1,
      y: 0,
      duration: 0.15,
      stagger: 0.03,
      ease: ease.smooth,
    }, '-=0.05');
    
    return tl;
  }, []);

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
          paddingTop: theme.spacing(2),
          overflow: 'auto'
        }}
      >
      <Box ref={titleRef}>
        <Typography 
          variant="h4" 
          sx={{ 
            mb: 1, 
            color: theme.palette.secondary.main,
            fontWeight: 700,
            letterSpacing: '0.02em',
          }}
        >
          League Rules & Regulations
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Last Updated: October 21, 2025 - Season 2025
        </Typography>
      </Box>

      <Alert 
        ref={alertRef}
        severity="info" 
        sx={{ mb: 3 }}
      >
        All participants must read and agree to these rules before competing. Violations may result in penalties or disqualification.
      </Alert>

      <Box ref={accordionsRef}>
      <Accordion 
        expanded={expanded === 'general'} 
        onChange={handleAccordionChange('general')}
        sx={{ 
          mb: 2, 
          backgroundColor: theme.palette.background.paper,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          border: `1px solid ${theme.palette.divider}`,
          '&:before': { display: 'none' },
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            transform: 'translateY(-2px)',
          }
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{
            transition: 'background-color 0.2s ease',
            '&:hover': {
              backgroundColor: theme.palette.action.hover
            }
          }}
        >
          <GavelIcon sx={{ mr: 2, color: theme.palette.secondary.main }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>1. General Rules</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText 
                primary="1.1 Team Composition"
                secondary="Each team must consist of exactly 5 active players with up to 2 substitutes. All players must be registered and verified before match start."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="1.2 Player Eligibility"
                secondary="Players must be 13 years or older. Players can only be registered on one team per division. Violation results in immediate disqualification."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="1.3 Team Name & Tag"
                secondary="Team names and tags must be appropriate and not offensive. Inappropriate names will result in forced rename or disqualification."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="1.4 Code of Conduct"
                secondary="All players must maintain sportsmanlike conduct. Toxicity, harassment, or unsportsmanlike behavior will result in penalties."
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion 
        expanded={expanded === 'match'} 
        onChange={handleAccordionChange('match')}
        sx={{ 
          mb: 2, 
          backgroundColor: theme.palette.background.paper,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          border: `1px solid ${theme.palette.divider}`,
          '&:before': { display: 'none' },
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            transform: 'translateY(-2px)',
          }
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{
            '&:hover': {
              backgroundColor: theme.palette.action.hover
            }
          }}
        >
          <GavelIcon sx={{ mr: 2, color: theme.palette.secondary.main }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>2. Match Rules</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText 
                primary="2.1 Match Format"
                secondary="All matches are Best of 3 (BO3) format. Playoffs are Best of 5 (BO5). Standard competitive rules apply with overtime if needed."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="2.2 Punctuality"
                secondary="Teams must be ready 15 minutes before scheduled match time. 15-minute grace period allowed. After that, forfeit will be issued."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="2.3 Map Selection"
                secondary="Maps are selected through a veto process: Ban-Ban-Pick-Pick-Ban-Ban-Decider. Higher seed gets first ban in playoffs."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="2.4 Side Selection"
                secondary="Side selection for Map 1 is determined by coin flip. Teams alternate side selection for remaining maps. Decider map uses standard knife round."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="2.5 Technical Issues"
                secondary="Teams can pause up to 10 minutes total per match for technical issues. Issues must be reported immediately. Admins have final say on tech pauses."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="2.6 Disconnections"
                secondary="Players have 5 minutes to reconnect. If unable to reconnect, substitute can replace. If no substitute available, team must play 4v5 or forfeit round."
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion 
        expanded={expanded === 'player'} 
        onChange={handleAccordionChange('player')}
        sx={{ 
          mb: 2, 
          backgroundColor: theme.palette.background.paper,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          border: `1px solid ${theme.palette.divider}`,
          '&:before': { display: 'none' },
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            transform: 'translateY(-2px)',
          }
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{
            '&:hover': {
              backgroundColor: theme.palette.action.hover
            }
          }}
        >
          <GavelIcon sx={{ mr: 2, color: theme.palette.secondary.main }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>3. Player & Roster Rules</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText 
                primary="3.1 Substitutions"
                secondary="Substitutions allowed between maps only, not during a map. Maximum 2 substitutions per match. Substitutes must be registered before match starts."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="3.2 Roster Changes"
                secondary="Roster changes allowed until Week 8. After Week 8, rosters are locked for playoffs. Emergency substitutions require admin approval."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="3.3 Account Verification"
                secondary="All players must verify their Riot account. Playing on unregistered accounts results in match forfeit and potential ban."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="3.4 Smurfing Policy"
                secondary="Players must play on their highest ranked account. Smurfing is strictly prohibited and results in immediate team disqualification."
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion 
        expanded={expanded === 'prohibited'} 
        onChange={handleAccordionChange('prohibited')}
        sx={{ 
          mb: 2, 
          backgroundColor: theme.palette.background.paper,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          border: `1px solid ${theme.palette.divider}`,
          '&:before': { display: 'none' },
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            transform: 'translateY(-2px)',
          }
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{
            '&:hover': {
              backgroundColor: theme.palette.action.hover
            }
          }}
        >
          <WarningIcon sx={{ mr: 2, color: theme.palette.error.main }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>4. Prohibited Actions</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText 
                primary="4.1 Cheating"
                secondary="Use of any unauthorized third-party software, exploits, or cheats results in permanent ban from all ScrimGG leagues."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="4.2 Match Fixing"
                secondary="Intentionally losing matches or colluding with opponents results in permanent ban and potential legal action."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="4.3 Bug Exploitation"
                secondary="Exploiting known bugs or glitches results in round loss minimum, match forfeit maximum. Must report bugs to admins immediately."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="4.4 Ghosting"
                secondary="Using external information sources during matches (stream sniping, spectator info) results in immediate disqualification."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="4.5 Harassment & Toxicity"
                secondary="Verbal abuse, harassment, or toxic behavior towards players, staff, or community results in warnings, suspensions, or bans."
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion 
        expanded={expanded === 'penalties'} 
        onChange={handleAccordionChange('penalties')}
        sx={{ 
          mb: 2, 
          backgroundColor: theme.palette.background.paper,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          border: `1px solid ${theme.palette.divider}`,
          '&:before': { display: 'none' },
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            transform: 'translateY(-2px)',
          }
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{
            '&:hover': {
              backgroundColor: theme.palette.action.hover
            }
          }}
        >
          <WarningIcon sx={{ mr: 2, color: theme.palette.warning.main }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>5. Penalties & Enforcement</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText 
                primary="5.1 Warning System"
                secondary="Minor violations: Verbal warning → Written warning → 1-match suspension → Multi-match suspension → Season ban"
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="5.2 Match Forfeit"
                secondary="No-show without 48hr notice, unregistered players, or severe rule violations result in 0-2 forfeit loss."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="5.3 Point Deductions"
                secondary="Repeated minor violations may result in league point deductions at admin discretion."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="5.4 Permanent Bans"
                secondary="Cheating, match fixing, or severe harassment results in permanent ban from all ScrimGG services."
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion 
        expanded={expanded === 'appeals'} 
        onChange={handleAccordionChange('appeals')}
        sx={{ 
          mb: 2, 
          backgroundColor: theme.palette.background.paper,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          border: `1px solid ${theme.palette.divider}`,
          '&:before': { display: 'none' },
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            transform: 'translateY(-2px)',
          }
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{
            '&:hover': {
              backgroundColor: theme.palette.action.hover
            }
          }}
        >
          <GavelIcon sx={{ mr: 2, color: theme.palette.secondary.main }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>6. Protests & Appeals</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText 
                primary="6.1 Filing a Protest"
                secondary="Protests must be filed within 24 hours of match completion via official ticket system with evidence (screenshots, recordings)."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="6.2 Admin Decisions"
                secondary="Admin decisions are final. Appeals can be submitted to head admin within 48 hours with new evidence only."
              />
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText 
                primary="6.3 Evidence Requirements"
                secondary="All claims must be supported by video evidence or screenshots. Hearsay or unsubstantiated claims will be dismissed."
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>
      </Box>

      <Grid container spacing={2} sx={{ mt: 2, pb: 6 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ 
            backgroundColor: theme.palette.info.dark,
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            border: `1px solid ${theme.palette.divider}`,
            transition: 'transform 0.3s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: `0 6px 16px ${theme.palette.secondary.dark}30`,
            }
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CheckCircleIcon sx={{ mr: 1, color: theme.palette.info.light }} />
                <Typography variant="h6">Important Notes</Typography>
              </Box>
              <Typography variant="body2">
                • Rules are subject to change with notice
              </Typography>
              <Typography variant="body2">
                • Admins reserve right to make final decisions
              </Typography>
              <Typography variant="body2">
                • All times are in EST unless stated otherwise
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ 
            backgroundColor: theme.palette.warning.dark,
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            border: `1px solid ${theme.palette.divider}`,
            transition: 'transform 0.3s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: `0 6px 16px ${theme.palette.secondary.dark}30`,
            }
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <WarningIcon sx={{ mr: 1, color: theme.palette.warning.light }} />
                <Typography variant="h6">Contact</Typography>
              </Box>
              <Typography variant="body2">
                Questions: support@scrimgg.com
              </Typography>
              <Typography variant="body2">
                League Admin: league@scrimgg.com
              </Typography>
              <Typography variant="body2">
                Discord: discord.gg/scrimgg
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      </Box>
    </Container>
  );
};

export default LeagueRules;
