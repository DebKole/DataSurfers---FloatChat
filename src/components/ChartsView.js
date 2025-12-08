import React, { useMemo } from 'react';
import {
    ScatterChart,
    Scatter,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    Cell
} from 'recharts';

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

    // Color interpolation function (Viridis-like approximation)
    const getDepthColor = (value, min, max) => {
        if (min === max) return '#440154'; // Default to dark purple if no range

        // Normalize value to 0-1
        const t = (value - min) / (max - min);

        // Simple 3-stop gradient: Blue -> Green -> Yellow
        // 0.0: #440154 (Dark Purple)
        // 0.5: #21908d (Teal)
        // 1.0: #fde725 (Yellow)

        let r, g, b;

        if (t < 0.5) {
            // Interpolate between Purple and Teal
            const localT = t * 2;
            r = Math.round(68 + (33 - 68) * localT);
            g = Math.round(1 + (144 - 1) * localT);
            b = Math.round(84 + (141 - 84) * localT);
        } else {
            // Interpolate between Teal and Yellow
            const localT = (t - 0.5) * 2;
            r = Math.round(33 + (253 - 33) * localT);
            g = Math.round(144 + (231 - 144) * localT);
            b = Math.round(141 + (37 - 141) * localT);
        }

        return `rgb(${r}, ${g}, ${b})`;
    };

    const chartConfig = useMemo(() => {
        if (!tableData || !tableData.rows || tableData.rows.length === 0) return null;

        const cols = tableData.columns;
        const tempCol = findColumn(cols, ['temperature_adjusted', 'temperature', 'temp']);
        const salCol = findColumn(cols, ['salinity_adjusted', 'salinity', 'psal']);
        const presCol = findColumn(cols, ['pressure_adjusted', 'pressure', 'pres', 'depth']);
        const cycleCol = findColumn(cols, ['cycle_number', 'cycle']);
        const floatCol = findColumn(cols, ['float_id', 'float']);

        // Filter out rows with null values for relevant columns
        const validRows = tableData.rows.filter(r =>
            (tempCol ? r[tempCol] != null : true) &&
            (salCol ? r[salCol] != null : true) &&
            (presCol ? r[presCol] != null : true)
        );

        // Calculate min/max pressure for coloring
        let minPres = Infinity;
        let maxPres = -Infinity;

        if (presCol) {
            validRows.forEach(r => {
                const val = r[presCol];
                if (val < minPres) minPres = val;
                if (val > maxPres) maxPres = val;
            });
        }

        // If no valid pressure range, set defaults
        if (minPres === Infinity) {
            minPres = 0;
            maxPres = 2000;
        }

        // Group by Float/Cycle for coloring/series
        // If no float/cycle, treat as one series
        const seriesMap = new Map();
        validRows.forEach(row => {
            const key = floatCol && cycleCol ? `${row[floatCol]}_${row[cycleCol]}` :
                floatCol ? row[floatCol] :
                    cycleCol ? `Cycle ${row[cycleCol]}` : 'Data';

            if (!seriesMap.has(key)) seriesMap.set(key, []);
            seriesMap.get(key).push(row);
        });

        const series = Array.from(seriesMap.entries()).map(([name, data]) => ({ name, data }));

        console.log("Chart Config:", {
            tempCol, salCol, presCol, seriesCount: series.length, minPres, maxPres
        });

        return {
            tempCol,
            salCol,
            presCol,
            series,
            minPres,
            maxPres,
            allData: validRows
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

    const { tempCol, salCol, presCol, series, minPres, maxPres, allData } = chartConfig;
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#e41a1c', '#377eb8'];

    // Custom Tooltip
    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div style={{ backgroundColor: '#fff', padding: '10px', border: '1px solid #ccc', color: '#000', fontSize: '0.8rem' }}>
                    {tempCol && <p><strong>Temp:</strong> {data[tempCol]?.toFixed(2)} °C</p>}
                    {salCol && <p><strong>Sal:</strong> {data[salCol]?.toFixed(2)} PSU</p>}
                    {presCol && <p><strong>Pres:</strong> {data[presCol]?.toFixed(1)} dbar</p>}
                    {data.cycle_number && <p><strong>Cycle:</strong> {data.cycle_number}</p>}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="charts-view" style={{ padding: '10px', color: '#fff', overflowY: 'auto', maxHeight: '100%' }}>

            {/* T-S Diagram with Depth Coloring */}
            {tempCol && salCol && (
                <div style={{ marginBottom: '30px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '10px', overflowX: 'auto' }}>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px' }}>T-S Diagram (Colored by Depth)</h4>
                    <div style={{ height: '350px', position: 'relative', minWidth: '600px' }}>
                        <ScatterChart width={600} height={350} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                            <XAxis
                                type="number"
                                dataKey={salCol}
                                name="Salinity"
                                unit=" PSU"
                                domain={['auto', 'auto']}
                                label={{ value: 'Salinity (PSU)', position: 'bottom', offset: 0, fill: '#fff' }}
                                tick={{ fill: '#fff', fontSize: 10 }}
                            />
                            <YAxis
                                type="number"
                                dataKey={tempCol}
                                name="Temperature"
                                unit=" °C"
                                domain={['auto', 'auto']}
                                label={{ value: 'Temperature (°C)', angle: -90, position: 'left', fill: '#fff' }}
                                tick={{ fill: '#fff', fontSize: 10 }}
                            />
                            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />

                            {/* Render all points as a single series to handle coloring easily */}
                            <Scatter name="Measurements" data={allData} shape="circle">
                                {allData.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={presCol ? getDepthColor(entry[presCol], minPres, maxPres) : '#8884d8'}
                                    />
                                ))}
                            </Scatter>
                        </ScatterChart>

                        {/* Gradient Legend */}
                        {presCol && (
                            <div style={{
                                position: 'absolute',
                                top: 10,
                                right: 10,
                                background: 'rgba(0,0,0,0.7)',
                                padding: '5px',
                                borderRadius: '4px',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                pointerEvents: 'none'
                            }}>
                                <div style={{ fontSize: '0.7rem', marginBottom: '2px', color: '#fff' }}>Depth (dbar)</div>
                                <div style={{
                                    width: '10px',
                                    height: '100px',
                                    background: 'linear-gradient(to bottom, #440154, #21908d, #fde725)'
                                }}></div>
                                <div style={{
                                    height: '100px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    justifyContent: 'space-between',
                                    position: 'absolute',
                                    right: '20px',
                                    top: '22px',
                                    fontSize: '0.7rem',
                                    textAlign: 'right',
                                    color: '#fff'
                                }}>
                                    <span>{Math.round(minPres)}</span>
                                    <span>{Math.round((minPres + maxPres) / 2)}</span>
                                    <span>{Math.round(maxPres)}</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Temperature Profile */}
            {tempCol && presCol && (
                <div style={{ marginBottom: '30px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '10px', overflowX: 'auto' }}>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px' }}>Temperature Profile</h4>
                    <div style={{ height: '300px', minWidth: '600px' }}>
                        <ScatterChart width={600} height={300} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                            <XAxis
                                type="number"
                                dataKey={tempCol}
                                name="Temperature"
                                domain={['auto', 'auto']}
                                stroke="#ccc"
                                label={{ value: 'Temp (°C)', position: 'bottom', fill: '#ccc', offset: 0 }}
                                tick={{ fontSize: 10 }}
                            />
                            <YAxis
                                type="number"
                                dataKey={presCol}
                                name="Pressure"
                                domain={['auto', 'auto']}
                                reversed={true} // Depth goes down
                                stroke="#ccc"
                                label={{ value: 'Pressure (dbar)', angle: -90, position: 'insideLeft', fill: '#ccc' }}
                                tick={{ fontSize: 10 }}
                            />
                            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                            <Legend wrapperStyle={{ fontSize: '10px' }} />
                            {series.map((s, i) => (
                                <Scatter
                                    key={s.name}
                                    name={s.name}
                                    data={s.data}
                                    fill={colors[i % colors.length]}
                                    line // Connect points for profile
                                    lineType="fitting"
                                />
                            ))}
                        </ScatterChart>
                    </div>
                </div>
            )}

            {/* Salinity Profile */}
            {salCol && presCol && (
                <div style={{ marginBottom: '30px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '10px', overflowX: 'auto' }}>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px' }}>Salinity Profile</h4>
                    <div style={{ height: '300px', minWidth: '600px' }}>
                        <ScatterChart width={600} height={300} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                            <XAxis
                                type="number"
                                dataKey={salCol}
                                name="Salinity"
                                domain={['auto', 'auto']}
                                stroke="#ccc"
                                label={{ value: 'Salinity (PSU)', position: 'bottom', fill: '#ccc', offset: 0 }}
                                tick={{ fontSize: 10 }}
                            />
                            <YAxis
                                type="number"
                                dataKey={presCol}
                                name="Pressure"
                                domain={['auto', 'auto']}
                                reversed={true}
                                stroke="#ccc"
                                label={{ value: 'Pressure (dbar)', angle: -90, position: 'insideLeft', fill: '#ccc' }}
                                tick={{ fontSize: 10 }}
                            />
                            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                            <Legend wrapperStyle={{ fontSize: '10px' }} />
                            {series.map((s, i) => (
                                <Scatter
                                    key={s.name}
                                    name={s.name}
                                    data={s.data}
                                    fill={colors[i % colors.length]}
                                    line
                                    lineType="fitting"
                                />
                            ))}
                        </ScatterChart>
                    </div>
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
