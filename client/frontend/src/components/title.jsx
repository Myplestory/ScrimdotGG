import * as React from 'react';
import PropTypes from 'prop-types';
import Typography from '@mui/material/Typography';
import { ColorModeContext, useMode } from '../theme';

function Title(props) {
  const [theme, colorMode] = useMode();
  return (
    <Typography component="h2" variant="h6" color={theme.palette.secondary.main} gutterBottom>
      {props.children}
    </Typography>
  );
}

Title.propTypes = {
  children: PropTypes.node,
};

export default Title;