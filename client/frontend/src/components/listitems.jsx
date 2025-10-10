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



const CustomListItem = ({ text, onClick }) => {
  const [theme, colorMode] = useMode();
  return (
  <ListItemButton sx={{color:theme.palette.primary}} onClick={onClick} >
    <ListItemText primary={text} />
  </ListItemButton>
  );
};

export const MainListItems = ({ setActiveComponent }) => (
  <React.Fragment>
    <Accordion >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <ListItemText primary="Pugs & Ranks" />
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <CustomListItem text="Find Match" onClick={() => setActiveComponent('pug')} />
            <CustomListItem text="Create Party" onClick={() => setActiveComponent('lobby')} />
            <CustomListItem text="Join Party" navigateTo="/joinparty" />
            {/* Add more options as needed */}
          </List>
      </AccordionDetails>
    </Accordion>
    <Accordion>
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
    <Accordion>
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
      <Accordion>
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
    <Accordion>
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
