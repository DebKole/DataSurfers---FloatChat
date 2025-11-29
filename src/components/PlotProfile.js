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

function PlotProfileTool({
  profiles,
  profileId,
  xKey = 'temperature',
  yKey = 'pressure',
  xLabel,
  yLabel,
  invertY = false,
}) {
  const profile = useMemo(
    () => profiles.find(p => p.profileId === profileId),
    [profiles, profileId]
  );

  if (!profile || !profile.measurements || profile.measurements.length === 0) {
    return <div>No profile selected or no data.</div>;
  }

  const x = profile.measurements.map(m => m[xKey]);
  const y = profile.measurements.map(m => m[yKey]);

  const resolvedXLabel = xLabel || xKey;
  const resolvedYLabel = yLabel || yKey;

  return (
    <Plot
      data={[
        {
          x,
          y,
          mode: 'lines',
          type: 'scatter',
          name: `${resolvedYLabel} vs ${resolvedXLabel}`,
          line: {
            color: '#A0D6B4', // green
            width: 2.5,
          },
        },
      ]}
      layout={{
        title: `Profile ${profileId} – ${resolvedYLabel} vs ${resolvedXLabel}`,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e8f0' },
        xaxis: {
          title: { text: resolvedXLabel, font: { color: '#e2e8f0', size: 12 }, standoff: 8 },
          gridcolor: 'rgba(226,232,240,0.12)',
          zerolinecolor: '#94a3b8',
          color: '#cbd5e1',
        },
        yaxis: {
          title: { text: resolvedYLabel, font: { color: '#e2e8f0', size: 12 } },
          gridcolor: 'rgba(226,232,240,0.12)',
          zerolinecolor: '#94a3b8',
          color: '#cbd5e1',
          ...(invertY ? { autorange: 'reversed' } : {}),
        },
        legend: { orientation: 'h', bgcolor: 'rgba(0,0,0,0)' },
        margin: { 
          l: invertY ? 70 : 60, 
          r: 30, 
          t: 40, 
          b: invertY ? 60 : 50 
        },
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

export default PlotProfileTool;