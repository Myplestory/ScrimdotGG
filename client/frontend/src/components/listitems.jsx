import * as React from 'react';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListSubheader from '@mui/material/ListSubheader';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import { Accordion, AccordionSummary, AccordionDetails, List } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useNavigate, Link } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { ColorModeContext, useMode } from '../theme';



const CustomListItem = ({ text, onClick, navigateTo }) => {
  const [theme, colorMode] = useMode();
  const navigate = useNavigate();
  
  const handleClick = () => {
    if (onClick) {
      onClick();
    } else if (navigateTo) {
      navigate(navigateTo);
    }
  };
  
  return (
    <ListItemButton sx={{color:theme.palette.primary}} onClick={handleClick} >
      <ListItemText primary={text} />
    </ListItemButton>
  );
};

export const MainListItems = ({ setActiveComponent }) => {
  const [expandedAccordion, setExpandedAccordion] = React.useState(null);

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpandedAccordion(isExpanded ? panel : null);
  };

  return (
    <React.Fragment>
      <Accordion 
        expanded={expandedAccordion === 'matchmake'}
        onChange={handleAccordionChange('matchmake')}
        sx={{ 
          '&:before': { display: 'none' }, 
          boxShadow: 'none', 
          margin: '0 !important',
          '&.MuiAccordion-root': { margin: '0 !important' },
          '&.MuiAccordion-root:before': { display: 'none' }
        }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <ListItemText primary="Matchmake" />
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <CustomListItem text="Play" onClick={() => setActiveComponent && setActiveComponent('pug')} />
            <CustomListItem text="Scrim" onClick={() => setActiveComponent && setActiveComponent('lobby')} />
            {/* Add more options as needed */}
          </List>
      </AccordionDetails>
    </Accordion>
    <Accordion 
      expanded={expandedAccordion === 'league'}
      onChange={handleAccordionChange('league')}
      sx={{ 
        '&:before': { display: 'none' }, 
        boxShadow: 'none', 
        margin: '0 !important',
        '&.MuiAccordion-root': { margin: '0 !important' },
        '&.MuiAccordion-root:before': { display: 'none' }
      }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <ListItemText primary="League" />
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <CustomListItem text="Create a Team" navigateTo="/leaguecreateteam" />
            <CustomListItem text="Register & Pay" navigateTo="/leagueregteam" />
            <CustomListItem text="Divisions & Standings" navigateTo="/leaguestandings" />
            <CustomListItem text="Schedule" navigateTo="/leagueschedule" />
            <CustomListItem text="Rules" navigateTo="/leaguerules" />
          </List>
      </AccordionDetails>
    </Accordion>
    <Accordion 
      expanded={expandedAccordion === 'forums'}
      onChange={handleAccordionChange('forums')}
      sx={{ 
        '&:before': { display: 'none' }, 
        boxShadow: 'none', 
        margin: '0 !important',
        '&.MuiAccordion-root': { margin: '0 !important' },
        '&.MuiAccordion-root:before': { display: 'none' }
      }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <ListItemText primary="Forums" />
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <CustomListItem text="Forum Index" navigateTo="/forumindex" />
            <CustomListItem text="Post New Topic" navigateTo="/postnew" />
          </List>
      </AccordionDetails>
      </Accordion>
      <Accordion 
        expanded={expandedAccordion === 'support'}
        onChange={handleAccordionChange('support')}
        sx={{ 
          '&:before': { display: 'none' }, 
          boxShadow: 'none', 
          margin: '0 !important',
          '&.MuiAccordion-root': { margin: '0 !important' },
          '&.MuiAccordion-root:before': { display: 'none' }
        }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <ListItemText primary="Support" />
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <CustomListItem text="FAQ" navigateTo="/faq" />
            <CustomListItem text="Support Tickets" navigateTo="/supporttickets" />
          </List>
      </AccordionDetails>
    </Accordion>
      <Accordion 
        expanded={expandedAccordion === 'client'}
        onChange={handleAccordionChange('client')}
        sx={{ 
          '&:before': { display: 'none' }, 
          boxShadow: 'none', 
          margin: '0 !important',
          '&.MuiAccordion-root': { margin: '0 !important' },
          '&.MuiAccordion-root:before': { display: 'none' }
        }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <ListItemText primary="Client" />
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <CustomListItem text="Download" navigateTo="/download" />
          </List>
      </AccordionDetails>
    </Accordion>
  </React.Fragment>
  );
};
