import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

// profiles: [
//   {
//     profileId: number | string,
//     measurements: [
//       { pressure: number, temperature: number, salinity: number }
//     ]
//   }
// ]

function PlotProfileTool({ profiles, profileId, variable = 'TEMP' }) {
  const profile = useMemo(
    () => profiles.find(p => p.profileId === profileId),
    [profiles, profileId]
  );

  if (!profile || !profile.measurements || profile.measurements.length === 0) {
    return <div>No profile selected or no data.</div>;
  }

  const x = profile.measurements.map(m =>
    variable === 'SAL' ? m.salinity : m.temperature
  );
  const y = profile.measurements.map(m => m.pressure);

  return (
    <Plot
      data={[
        {
          x,
          y,
          mode: 'lines+markers',
          type: 'scatter',
          name: `${variable} profile`,
        },
      ]}
      layout={{
        title: `Profile ${profileId} – ${variable} vs PRES`,
        xaxis: { title: variable },
        yaxis: { title: 'PRES', autorange: 'reversed' },
        margin: { l: 60, r: 20, t: 40, b: 50 },
      }}
      style={{ width: '100%', height: '400px' }}
    />
  );
}

export default PlotProfileTool;