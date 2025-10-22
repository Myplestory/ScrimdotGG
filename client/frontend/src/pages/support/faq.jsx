import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  InputAdornment,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SearchIcon from '@mui/icons-material/Search';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const FAQ = () => {
  const theme = useTheme();
  const [searchTerm, setSearchTerm] = useState('');
  const [expanded, setExpanded] = useState(false);

  const faqCategories = [
    {
      category: 'General',
      questions: [
        {
          question: 'What is ScrimGG?',
          answer: 'ScrimGG is a competitive matchmaking platform for Valorant players. It provides organized scrims, leagues, and tournaments for teams and solo players looking to improve their skills in a competitive environment.',
        },
        {
          question: 'Is ScrimGG free to use?',
          answer: 'Yes! Basic matchmaking and scrims are completely free. Premium features and league participation may require a subscription or one-time payment.',
        },
        {
          question: 'What ranks can participate?',
          answer: 'All ranks are welcome! We have separate queues and leagues for different skill levels to ensure balanced and competitive matches.',
        },
      ],
    },
    {
      category: 'Account & Login',
      questions: [
        {
          question: 'How do I create an account?',
          answer: 'Click the "Sign Up" button and log in using your Riot Games account. We use Riot\'s official authentication to verify your identity and rank.',
        },
        {
          question: 'Why do I need to link my Riot account?',
          answer: 'Linking your Riot account allows us to verify your rank, match history, and ensure fair matchmaking. It also prevents smurfing and maintains competitive integrity.',
        },
        {
          question: 'Can I use multiple accounts?',
          answer: 'Each player is limited to one ScrimGG account to prevent smurfing and maintain fair competition.',
        },
      ],
    },
    {
      category: 'Matchmaking',
      questions: [
        {
          question: 'How does matchmaking work?',
          answer: 'Our matchmaking system considers your rank, recent performance, and MMR to create balanced teams. Queue times vary based on your rank and time of day.',
        },
        {
          question: 'What happens if someone leaves?',
          answer: 'If a player leaves during the match setup, the match will be cancelled. During an active match, you can report the player and request a remake within the first 3 rounds.',
        },
        {
          question: 'How long does it take to find a match?',
          answer: 'Queue times typically range from 2-10 minutes depending on your rank and region. Peak hours (6 PM - 11 PM) usually have faster queue times.',
        },
      ],
    },
    {
      category: 'Leagues & Tournaments',
      questions: [
        {
          question: 'How do I join a league?',
          answer: 'Navigate to the League section, create or join a team, and register for an upcoming season. Make sure all team members meet the eligibility requirements.',
        },
        {
          question: 'What are the league requirements?',
          answer: 'Teams need 5 main players and up to 2 substitutes. All players must be within the specified rank range for their division and have active ScrimGG accounts.',
        },
        {
          question: 'When do leagues start?',
          answer: 'New league seasons start every 8 weeks. Check the Schedule page for exact dates and registration deadlines.',
        },
        {
          question: 'Are there prizes for winning?',
          answer: 'Yes! Prize pools vary by division and are announced at the start of each season. Prizes may include cash, Valorant Points, or exclusive ScrimGG merchandise.',
        },
      ],
    },
    {
      category: 'Technical Issues',
      questions: [
        {
          question: 'The client won\'t connect to the game',
          answer: 'Make sure Valorant is running and you\'re logged in. Try restarting both the ScrimGG client and Valorant. If the issue persists, check our Discord for service status.',
        },
        {
          question: 'I\'m getting a "Match not found" error',
          answer: 'This usually means the match was cancelled or you were removed from the queue. Try rejoining the queue. If it continues, submit a support ticket.',
        },
        {
          question: 'My stats aren\'t updating',
          answer: 'Stats typically update within 5 minutes of a match ending. If they haven\'t updated after 30 minutes, please submit a support ticket with your match ID.',
        },
      ],
    },
    {
      category: 'Rules & Conduct',
      questions: [
        {
          question: 'What behavior is not allowed?',
          answer: 'We have zero tolerance for toxicity, cheating, match-fixing, harassment, or discriminatory behavior. Violations may result in temporary or permanent bans.',
        },
        {
          question: 'How do I report a player?',
          answer: 'Use the in-client report feature during or after a match. Include any evidence (screenshots, clips) to help our moderation team review the case.',
        },
        {
          question: 'What happens if I get reported?',
          answer: 'Our moderation team reviews all reports. Depending on the severity, consequences range from warnings to temporary suspensions or permanent bans.',
        },
      ],
    },
  ];

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false);
  };

  const filteredFAQs = faqCategories.map((category) => ({
    ...category,
    questions: category.questions.filter(
      (q) =>
        q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.answer.toLowerCase().includes(searchTerm.toLowerCase())
    ),
  })).filter((category) => category.questions.length > 0);

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
          <HelpOutlineIcon sx={{ fontSize: 40, color: theme.palette.secondary.main, mr: 2 }} />
          <Typography variant="h4" sx={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>
            Frequently Asked Questions
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ color: theme.palette.text.secondary, mb: 3 }}>
          Find answers to common questions about ScrimGG
        </Typography>

        {/* Search */}
        <TextField
          fullWidth
          placeholder="Search for answers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: theme.palette.text.secondary }} />
              </InputAdornment>
            ),
          }}
          sx={{
            maxWidth: 600,
            '& .MuiInputBase-root': {
              backgroundColor: theme.palette.background.paper,
            },
          }}
        />
      </Box>

      {/* FAQ Sections */}
      <Box sx={{ maxWidth: 900 }}>
        {filteredFAQs.map((category, categoryIndex) => (
          <Box key={categoryIndex} sx={{ mb: 4 }}>
            <Typography
              variant="h5"
              sx={{
                color: theme.palette.text.primary,
                fontWeight: 'bold',
                mb: 2,
                pb: 1,
                borderBottom: `2px solid ${theme.palette.secondary.main}`,
              }}
            >
              {category.category}
            </Typography>

            {category.questions.map((faq, index) => (
              <Accordion
                key={index}
                expanded={expanded === `${categoryIndex}-${index}`}
                onChange={handleAccordionChange(`${categoryIndex}-${index}`)}
                sx={{
                  mb: 1,
                  backgroundColor: theme.palette.background.paper,
                  border: `1px solid ${theme.palette.divider}`,
                  '&:before': { display: 'none' },
                  '&.Mui-expanded': {
                    borderColor: theme.palette.secondary.main,
                  },
                }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon sx={{ color: theme.palette.secondary.main }} />}
                  sx={{
                    '&:hover': {
                      backgroundColor: theme.palette.background.default,
                    },
                  }}
                >
                  <Typography sx={{ color: theme.palette.text.primary, fontWeight: 500 }}>
                    {faq.question}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails
                  sx={{
                    backgroundColor: theme.palette.background.default,
                    borderTop: `1px solid ${theme.palette.divider}`,
                  }}
                >
                  <Typography sx={{ color: theme.palette.text.secondary }}>
                    {faq.answer}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        ))}

        {filteredFAQs.length === 0 && (
          <Paper
            sx={{
              p: 4,
              textAlign: 'center',
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography variant="h6" sx={{ color: theme.palette.text.secondary }}>
              No results found for "{searchTerm}"
            </Typography>
            <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mt: 1 }}>
              Try different keywords or browse all categories
            </Typography>
          </Paper>
        )}
      </Box>

      {/* Still Need Help */}
      <Paper
        sx={{
          mt: 4,
          mb: 6,
          p: 3,
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          maxWidth: 900,
        }}
      >
        <Typography variant="h6" sx={{ color: theme.palette.text.primary, mb: 1, fontWeight: 'bold' }}>
          Still need help?
        </Typography>
        <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
          If you couldn't find the answer you're looking for, please submit a support ticket and our team will get back to you as soon as possible.
        </Typography>
      </Paper>
    </Box>
  );
};

export default FAQ;
