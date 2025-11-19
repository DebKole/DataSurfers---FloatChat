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

function CompareProfilesTool({ profiles, profileIds = [], variable = 'TEMP' }) {
  const selectedProfiles = useMemo(
    () => profiles.filter(p => profileIds.includes(p.profileId)),
    [profiles, profileIds]
  );

  if (!selectedProfiles.length) {
    return <div>No profiles selected for comparison.</div>;
  }

  const traces = selectedProfiles.map((profile) => {
    const x = profile.measurements.map(m =>
      variable === 'SAL' ? m.salinity : m.temperature
    );
    const y = profile.measurements.map(m => m.pressure);

    return {
      x,
      y,
      mode: 'lines+markers',
      type: 'scatter',
      name: `Profile ${profile.profileId}`,
    };
  });

  return (
    <Plot
      data={traces}
      layout={{
        title: `Compare profiles – ${variable} vs PRES`,
        xaxis: { title: variable },
        yaxis: { title: 'PRES', autorange: 'reversed' },
        margin: { l: 60, r: 20, t: 40, b: 50 },
        legend: { orientation: 'h' },
      }}
      style={{ width: '100%', height: '400px' }}
    />
  );
}

export default CompareProfilesTool;
