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

  // Color palette for comparison graphs - keeping soft orange for first profile
  const colors = ['#FF7F50', '#A0D6B4']; // Soft chocolate orange and soft cadet blue
  
  const traces = selectedProfiles.map((profile, index) => {
    const x = profile.measurements.map(m =>
      variable === 'SAL' ? m.salinity : m.temperature
    );
    const y = profile.measurements.map(m => m.pressure);
    
    const color = colors[index % colors.length];

    return {
      x,
      y,
      mode: 'lines',
      type: 'scatter',
      name: `Profile ${profile.profileId}`,
      line: {
        color: color,
        width: 2.5,
      },
    };
  });

  // Map variable to display name with units
  const getVariableLabel = (varName) => {
    switch (varName) {
      case 'TEMP':
        return 'Temperature (°C)';
      case 'SAL':
        return 'Salinity (PSU)';
      default:
        return varName;
    }
  };

  return (
    <Plot
      data={traces}
      layout={{
        title: `Compare profiles – ${getVariableLabel(variable)} vs Pressure (dbar)`,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e8f0' },
        xaxis: {
          title: { text: getVariableLabel(variable), font: { color: '#e2e8f0', size: 12 }, standoff: 8 },
          gridcolor: 'rgba(226,232,240,0.12)',
          zerolinecolor: '#94a3b8',
          color: '#cbd5e1',
        },
        yaxis: {
          title: { text: 'Pressure (dbar)', font: { color: '#e2e8f0', size: 12 } },
          autorange: 'reversed',
          gridcolor: 'rgba(226,232,240,0.12)',
          zerolinecolor: '#94a3b8',
          color: '#cbd5e1',
        },
        margin: { l: 70, r: 30, t: 40, b: 60 },
        legend: { orientation: 'h', bgcolor: 'rgba(0,0,0,0)' },
        autosize: true,
      }}
      style={{ width: '100%', height: '400px', minHeight: '400px' }}
      config={{ 
        displayModeBar: false,
        responsive: true,
      }}
    />
  );
}

export default CompareProfilesTool;
