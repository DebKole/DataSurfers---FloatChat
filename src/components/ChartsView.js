import React, { useMemo } from 'react';
import PlotProfileTool from './PlotProfile';

const ChartsView = ({ tableData }) => {
    // Helper to find a column case-insensitively
    const findColumn = (cols, keywords) => {
        if (!cols) return null;
        const lowerCols = cols.map(c => c.toLowerCase());
        for (const kw of keywords) {
            const idx = lowerCols.indexOf(kw.toLowerCase());
            if (idx !== -1) return cols[idx];
            // Try partial match
            const partial = cols.find(c => c.toLowerCase().includes(kw.toLowerCase()));
            if (partial) return partial;
        }
        return null;
    };

    const chartConfig = useMemo(() => {
        if (!tableData || !tableData.rows || tableData.rows.length === 0) return null;

        const cols = tableData.columns;
        const tempCol = findColumn(cols, ['temperature_adjusted', 'temperature', 'temp']);
        const salCol = findColumn(cols, ['salinity_adjusted', 'salinity', 'psal']);
        const presCol = findColumn(cols, ['pressure_adjusted', 'pressure', 'pres', 'depth']);
        const cycleCol = findColumn(cols, ['cycle_number', 'cycle']);
        const floatCol = findColumn(cols, ['float_id', 'float']);

        // Filter valid rows
        const validRows = tableData.rows.filter(r =>
            (tempCol ? r[tempCol] != null : true) &&
            (salCol ? r[salCol] != null : true) &&
            (presCol ? r[presCol] != null : true)
        );

        // Group into profiles
        const profilesMap = new Map();
        validRows.forEach(row => {
            // Create a unique key for each profile (Float + Cycle)
            let key = 'Data';
            let cycle = 'Unknown';
            let float = 'Unknown';

            if (floatCol) float = row[floatCol];
            if (cycleCol) cycle = row[cycleCol];

            if (floatCol && cycleCol) key = `${float}_${cycle}`;
            else if (floatCol) key = `${float}`;
            else if (cycleCol) key = `Cycle ${cycle}`;

            if (!profilesMap.has(key)) {
                profilesMap.set(key, {
                    profileId: key,
                    cycle_number: cycle,
                    float_id: float,
                    measurements: []
                });
            }
            profilesMap.get(key).measurements.push(row);
        });

        const profiles = Array.from(profilesMap.values());

        return {
            tempCol,
            salCol,
            presCol,
            profiles
        };
    }, [tableData]);

    if (!tableData || !tableData.rows || tableData.rows.length === 0) {
        return (
            <div style={{ padding: '20px', textAlign: 'center', color: '#aaa' }}>
                <p>No data available for charts.</p>
                <small>Run a query that returns oceanographic data (Temperature, Salinity, Pressure) to see charts.</small>
            </div>
        );
    }

    if (!chartConfig) return null;

    const { tempCol, salCol, presCol, profiles } = chartConfig;

    return (
        <div className="charts-view" style={{ padding: '10px', color: '#fff', overflowY: 'auto', maxHeight: '100%' }}>

            {/* T-S Diagram */}
            {tempCol && salCol && (
                <div style={{ marginBottom: '30px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '10px' }}>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px' }}>T-S Diagram</h4>
                    <PlotProfileTool
                        profiles={profiles}
                        xKey={salCol}
                        yKey={tempCol}
                        xLabel="Salinity (PSU)"
                        yLabel="Temperature (°C)"
                    />
                </div>
            )}

            {/* Temperature Profile */}
            {tempCol && presCol && (
                <div style={{ marginBottom: '30px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '10px' }}>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px' }}>Temperature Profile</h4>
                    <PlotProfileTool
                        profiles={profiles}
                        xKey={tempCol}
                        yKey={presCol}
                        xLabel="Temperature (°C)"
                        yLabel="Pressure (dbar)"
                        invertY={true}
                    />
                </div>
            )}

            {/* Salinity Profile */}
            {salCol && presCol && (
                <div style={{ marginBottom: '30px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '10px' }}>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px' }}>Salinity Profile</h4>
                    <PlotProfileTool
                        profiles={profiles}
                        xKey={salCol}
                        yKey={presCol}
                        xLabel="Salinity (PSU)"
                        yLabel="Pressure (dbar)"
                        invertY={true}
                    />
                </div>
            )}

            {!tempCol && !salCol && !presCol && (
                <div style={{ textAlign: 'center', color: '#aaa' }}>
                    <p>Data does not contain Temperature, Salinity, or Pressure columns.</p>
                </div>
            )}
        </div>
    );
};

export default ChartsView;
