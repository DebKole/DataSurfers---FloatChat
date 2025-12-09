import React, { useMemo } from "react";
import Plot from "react-plotly.js";

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
  xKey = "temperature",
  yKey = "pressure",
  xLabel,
  yLabel,
  invertY = false,
}) {
  const visibleProfiles = useMemo(() => {
    if (profileId) {
      // Handle both string/number comparison loosely
      return profiles.filter((p) =>
        (p.profileId == profileId) ||
        (p.cycle_number == profileId)
      );
    }
    return profiles;
  }, [profiles, profileId]);

  if (!visibleProfiles || visibleProfiles.length === 0) {
    return <div style={{ color: "#e2e8f0", padding: "10px" }}>No data available.</div>;
  }

  const resolvedXLabel = xLabel || xKey;
  const resolvedYLabel = yLabel || yKey;

  const traces = visibleProfiles.map((profile, index) => {
    const x = profile.measurements.map((m) => m[xKey]);
    const y = profile.measurements.map((m) => m[yKey]);
    const cycle = profile.cycle_number ?? profile.profileId ?? "Unknown";

    return {
      x,
      y,
      mode: "lines", // lines only for cleaner look with many profiles
      type: "scatter",
      name: `Cycle ${cycle}`,
      line: {
        width: visibleProfiles.length === 1 ? 3 : 1.5,
        // Let Plotly assign colors automatically or use a scale if needed
      },
      // Add a subtle fill only if viewing a single profile
      fill: visibleProfiles.length === 1 ? "tozeroy" : "none",
      fillcolor: "rgba(183, 226, 200, 0.20)",
      hovertemplate: `<b>Cycle ${cycle}</b><br>${resolvedXLabel}: %{x}<br>${resolvedYLabel}: %{y}<extra></extra>`,
    };
  });

  return (
    <Plot
      data={traces}
      layout={{
        title: visibleProfiles.length === 1
          ? `Cycle ${visibleProfiles[0].cycle_number ?? visibleProfiles[0].profileId}`
          : `All Cycles (${visibleProfiles.length})`,
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "#e2e8f0" },
        xaxis: {
          title: {
            text: resolvedXLabel,
            font: { color: "#e2e8f0", size: 12 },
            standoff: 8,
          },
          gridcolor: "rgba(226,232,240,0.12)",
          zerolinecolor: "#94a3b8",
          color: "#cbd5e1",
        },
        yaxis: {
          title: { text: resolvedYLabel, font: { color: "#e2e8f0", size: 12 } },
          gridcolor: "rgba(226,232,240,0.12)",
          zerolinecolor: "#94a3b8",
          color: "#cbd5e1",
          ...(invertY ? { autorange: "reversed" } : {}),
        },
        legend: {
          orientation: "h",
          bgcolor: "rgba(0,0,0,0)",
          // Hide legend if too many items to avoid clutter
          visible: visibleProfiles.length < 10
        },
        margin: {
          l: invertY ? 70 : 60,
          r: 30,
          t: 40,
          b: invertY ? 60 : 50,
        },
        autosize: true,
        hovermode: "closest",
      }}
      style={{ width: "100%", height: "400px", minHeight: "400px" }}
      config={{
        displayModeBar: false,
        responsive: true,
      }}
    />
  );
}

export default PlotProfileTool;
