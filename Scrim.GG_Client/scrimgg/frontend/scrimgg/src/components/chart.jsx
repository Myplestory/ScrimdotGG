import * as React from 'react';
import { ColorModeContext, useMode } from '../theme';
import { LineChart, axisClasses } from '@mui/x-charts';

import Title from './title';

// Generate Sales Data
function createData(month, amount) {
  return { month, amount: amount ?? null };
}

const data = [
  createData('September', 8),
  createData('November', 16),
  createData('December', 11),
  createData('January', 12),
  createData('February', 7),
  createData('March', 13),
];

export default function Chart() {
  const [theme, colorMode] = useMode();

  return (
    <React.Fragment>
      <Title color={theme.palette.secondary}>Server Stats</Title>
      <div style={{ width: '100%', flexGrow: 1, overflow: 'hidden' }}>
        <LineChart
          dataset={data}
          margin={{
            top: 16,
            right: 20,
            left: 70,
            bottom: 30,
          }}
          xAxis={[
            {
              scaleType: 'point',
              dataKey: 'month',
              tickNumber: 2,
              tickLabelStyle: theme.typography.body2,
            },
          ]}
          yAxis={[
            {
              label: 'RWS',
              labelStyle: {
                ...theme.typography.body1,
                fill: theme.palette.secondary,
                color: theme.palette.secondary,
              },
              tickLabelStyle: theme.typography.body2,
              tickNumber: 3,
            },
          ]}
          series={[
            {
              dataKey: 'amount',
              showMark: false,
              color: theme.palette.secondary.light,
              showMark: true
            },
          ]}
          sx={{
            [`.${axisClasses.root} line`]: { stroke: theme.palette.secondary.light },
            [`.${axisClasses.root} text`]: { fill: theme.palette.secondary },
            [`& .${axisClasses.left} .${axisClasses.label}`]: {
              transform: 'translateX(-25px)',
            },
            '& .MuiMarkElement-root': {
              color: theme.palette.secondary.light,
            },
          }}
        />
      </div>
    </React.Fragment>
  );
}