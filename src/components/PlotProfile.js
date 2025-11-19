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
          mode: 'lines+markers',
          type: 'scatter',
          name: `${resolvedYLabel} vs ${resolvedXLabel}`,
        },
      ]}
      layout={{
        title: `Profile ${profileId} – ${resolvedYLabel} vs ${resolvedXLabel}`,
        xaxis: { title: resolvedXLabel },
        yaxis: {
          title: resolvedYLabel,
          ...(invertY ? { autorange: 'reversed' } : {}),
        },
        margin: { l: 60, r: 20, t: 40, b: 50 },
      }}
      style={{ width: '100%', height: '400px' }}
    />
  );
}

export default PlotProfileTool;