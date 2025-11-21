import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';
import PlotProfileTool from './PlotProfile';
import CompareProfilesTool from './CompareProfilesTool';

const Dashboard = ({ onClose }) => {
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    totalProfiles: 0,
    avgTemperature: 0,
    avgSalinity: 0,
    dataQuality: 0,
    globalCoverage: 0
  });
  const [temperatureData, setTemperatureData] = useState([]);
  const [demoFloatId, setDemoFloatId] = useState('5906527');
  const [compareFloatIdA, setCompareFloatIdA] = useState('5906527');
  const [compareFloatIdB, setCompareFloatIdB] = useState('1901744');
  const [tsProfiles, setTsProfiles] = useState([]);
  const [tdProfiles, setTdProfiles] = useState([]);
  const [compareTdProfiles, setCompareTdProfiles] = useState([]);
  const [compareTsProfiles, setCompareTsProfiles] = useState([]);
  const [tsLoading, setTsLoading] = useState(false);
  const [tdLoading, setTdLoading] = useState(false);
  const [compareTdLoading, setCompareTdLoading] = useState(false);
  const [compareTsLoading, setCompareTsLoading] = useState(false);
  const [tsError, setTsError] = useState(null);
  const [tdError, setTdError] = useState(null);
  const [compareTdError, setCompareTdError] = useState(null);
  const [compareTsError, setCompareTsError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCSVData();
  }, []);

  const loadCSVData = async () => {
    try {
      const response = await fetch('/argo_demo.csv');
      const csvText = await response.text();
      const parsedData = parseCSV(csvText);
      calculateStats(parsedData);
      prepareLineChartData(parsedData);
      setLoading(false);
    } catch (error) {
      console.error('Error loading CSV data:', error);
      setLoading(false);
    }
  };

  const parseCSV = (csvText) => {
    const lines = csvText.split('\n');
    const headers = lines[0].split(',').map(header => header.trim());
    
    const data = [];
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue;
      
      const values = lines[i].split(',');
      const row = {};
      
      headers.forEach((header, index) => {
        row[header] = values[index] ? values[index].trim() : '';
      });
      
      data.push(row);
    }
    
    return data;
  };

  const calculateStats = (data) => {
    if (data.length === 0) return;

    const temperatures = data
      .filter(row => row.TEMPERATURE && !isNaN(parseFloat(row.TEMPERATURE)))
      .map(row => parseFloat(row.TEMPERATURE));
    
    const avgTemp = temperatures.length > 0 
      ? temperatures.reduce((sum, temp) => sum + temp, 0) / temperatures.length 
      : 0;

    const salinities = data
      .filter(row => row.SALINITY && !isNaN(parseFloat(row.SALINITY)))
      .map(row => parseFloat(row.SALINITY));
    
    const avgSalinity = salinities.length > 0 
      ? salinities.reduce((sum, sal) => sum + sal, 0) / salinities.length 
      : 0;

    setStats({
      totalProfiles: data.length,
      avgTemperature: avgTemp.toFixed(2),
      avgSalinity: avgSalinity.toFixed(2),
      dataQuality: 98.7,
      globalCoverage: 96.2
    });
  };

  const prepareLineChartData = (data) => {
    // Simulate temperature trends over months for the line graph
    const monthlyData = [
      { month: 'Jan', temperature: 4.1 },
      { month: 'Feb', temperature: 4.0 },
      { month: 'Mar', temperature: 4.2 },
      { month: 'Apr', temperature: 4.3 },
      { month: 'May', temperature: 4.5 },
      { month: 'Jun', temperature: 4.8 },
      { month: 'Jul', temperature: 5.1 },
      { month: 'Aug', temperature: 5.3 },
      { month: 'Sep', temperature: 5.0 },
      { month: 'Oct', temperature: 4.7 },
      { month: 'Nov', temperature: 4.4 },
      { month: 'Dec', temperature: 4.2 }
    ];

    setTemperatureData(monthlyData);
  };

  const renderLineGraph = () => {
    if (temperatureData.length === 0) return null;

    const maxTemp = Math.max(...temperatureData.map(d => d.temperature));
    const minTemp = Math.min(...temperatureData.map(d => d.temperature));
    const graphHeight = 200;

    return (
      <div className="line-graph">
        <div className="graph-title">Global Temperature Trends</div>
        <div className="graph-subtitle">Average ocean temperature at different depths over the past year</div>
        
        <div className="graph-container">
          {/* Y-axis labels */}
          <div className="y-axis">
            <span>32°C</span>
            <span>24°C</span>
            <span>16°C</span>
            <span>8°C</span>
          </div>
          
          {/* Graph area */}
          <div className="graph-area">
            <svg width="100%" height={graphHeight} className="line-chart">
              {/* Grid lines */}
              <line x1="0" y1="0" x2="100%" y2="0" stroke="#e0e0e0" strokeWidth="1" />
              <line x1="0" y1={graphHeight/3} x2="100%" y2={graphHeight/3} stroke="#e0e0e0" strokeWidth="1" />
              <line x1="0" y1={2*graphHeight/3} x2="100%" y2={2*graphHeight/3} stroke="#e0e0e0" strokeWidth="1" />
              <line x1="0" y1={graphHeight} x2="100%" y2={graphHeight} stroke="#e0e0e0" strokeWidth="1" />

              {/* Line path */}
              <path
                d={temperatureData.map((point, index) => {
                  const x = (index / (temperatureData.length - 1)) * 100;
                  const y = ((maxTemp - point.temperature) / (maxTemp - minTemp)) * graphHeight;
                  return `${index === 0 ? 'M' : 'L'} ${x}% ${y}`;
                }).join(' ')}
                fill="none"
                stroke="#3498db"
                strokeWidth="3"
                strokeLinecap="round"
              />

              {/* Data points */}
              {temperatureData.map((point, index) => {
                const x = (index / (temperatureData.length - 1)) * 100;
                const y = ((maxTemp - point.temperature) / (maxTemp - minTemp)) * graphHeight;
                return (
                  <circle
                    key={index}
                    cx={`${x}%`}
                    cy={y}
                    r="4"
                    fill="#3498db"
                    stroke="#fff"
                    strokeWidth="2"
                  />
                );
              })}
            </svg>
            
            {/* X-axis labels */}
            <div className="x-axis">
              {temperatureData.map((point, index) => (
                <span key={index} className="x-label">{point.month}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const handleFetchTsCurve = async () => {
    setTsLoading(true);
    setTsError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/ts_curve?float_id=${demoFloatId}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setTsProfiles(data.profiles || []);
    } catch (err) {
      setTsError(err.message || String(err));
      setTsProfiles([]);
    } finally {
      setTsLoading(false);
    }
  };

  const handleFetchTdCurve = async () => {
    setTdLoading(true);
    setTdError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/td_curve?float_id=${demoFloatId}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setTdProfiles(data.profiles || []);
    } catch (err) {
      setTdError(err.message || String(err));
      setTdProfiles([]);
    } finally {
      setTdLoading(false);
    }
  };

  const handleCompareTd = async () => {
    setCompareTdLoading(true);
    setCompareTdError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/compare_td?float_id_a=${compareFloatIdA}&float_id_b=${compareFloatIdB}`
      );
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setCompareTdProfiles(data.profiles || []);
    } catch (err) {
      setCompareTdError(err.message || String(err));
      setCompareTdProfiles([]);
    } finally {
      setCompareTdLoading(false);
    }
  };

  const handleCompareTs = async () => {
    setCompareTsLoading(true);
    setCompareTsError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/compare_ts?float_id_a=${compareFloatIdA}&float_id_b=${compareFloatIdB}`
      );
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setCompareTsProfiles(data.profiles || []);
    } catch (err) {
      setCompareTsError(err.message || String(err));
      setCompareTsProfiles([]);
    } finally {
      setCompareTsLoading(false);
    }
  };

  const handleClose = () => {
    if (typeof onClose === 'function') {
      onClose();
    } else {
      navigate(-1);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-overlay">
        <div className="dashboard-modal">
          <div className="dashboard-loading">Loading dashboard data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-overlay">
      <div className="dashboard-modal">
        <button className="dashboard-close" onClick={handleClose} aria-label="Close dashboard">×</button>
        <section className="dashboard-section">
          <h2>Dashboard</h2>
          <p>Overview of global oceanographic data</p>
        </section>

        {/* Charts Section */}
        <div className="charts-section">
          <div className="chart-container full-width">
            {renderLineGraph()}
          </div>
          <div className="chart-container full-width">
            <div className="graph-title">Live TS / TD and Comparison</div>
            <div className="graph-subtitle">Profiles fetched from backend trend API</div>
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
              <label>
                Float ID:
                <select
                  value={demoFloatId}
                  onChange={(e) => setDemoFloatId(e.target.value)}
                  style={{ marginLeft: '0.25rem' }}
                >
                  <option value="5906527">5906527</option>
                  <option value="1901744">1901744</option>
                  <option value="4902916">4902916</option>
                  <option value="4902917">4902917</option>
                </select>
              </label>
              <label>
                Compare A:
                <select
                  value={compareFloatIdA}
                  onChange={(e) => setCompareFloatIdA(e.target.value)}
                  style={{ marginLeft: '0.25rem' }}
                >
                  <option value="5906527">5906527</option>
                  <option value="1901744">1901744</option>
                  <option value="4902916">4902916</option>
                  <option value="4902917">4902917</option>
                </select>
              </label>
              <label>
                Compare B:
                <select
                  value={compareFloatIdB}
                  onChange={(e) => setCompareFloatIdB(e.target.value)}
                  style={{ marginLeft: '0.25rem' }}
                >
                  <option value="1901744">1901744</option>
                  <option value="5906527">5906527</option>
                  <option value="4902916">4902916</option>
                  <option value="4902917">4902917</option>
                </select>
              </label>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
              <button className="view-more-btn" onClick={handleFetchTsCurve} disabled={tsLoading}>
                {tsLoading ? 'Loading TS…' : 'Fetch TS Curve'}
              </button>
              <button className="view-more-btn" onClick={handleFetchTdCurve} disabled={tdLoading}>
                {tdLoading ? 'Loading TD…' : 'Fetch TD Profile'}
              </button>
              <button className="view-more-btn" onClick={handleCompareTd} disabled={compareTdLoading}>
                {compareTdLoading ? 'Comparing TD…' : 'Compare TD Profiles'}
              </button>
              <button className="view-more-btn" onClick={handleCompareTs} disabled={compareTsLoading}>
                {compareTsLoading ? 'Comparing TS…' : 'Compare TS Profiles'}
              </button>
              <button
                className="view-more-btn"
                onClick={() => {
                  setTsProfiles([]);
                  setTdProfiles([]);
                  setCompareTdProfiles([]);
                  setCompareTsProfiles([]);
                  setTsError(null);
                  setTdError(null);
                  setCompareTdError(null);
                  setCompareTsError(null);
                }}
              >
                Clear
              </button>
            </div>

            {(tsError || tdError || compareTdError || compareTsError) && (
              <div style={{ color: 'red', marginBottom: '0.5rem' }}>
                {tsError && <div>TS Error: {tsError}</div>}
                {tdError && <div>TD Error: {tdError}</div>}
                {compareTdError && <div>Compare TD Error: {compareTdError}</div>}
                {compareTsError && <div>Compare TS Error: {compareTsError}</div>}
              </div>
            )}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
              {tsProfiles.length > 0 && (
                <div style={{ flex: '1 1 260px', minWidth: '260px' }}>
                  <PlotProfileTool
                    profiles={tsProfiles}
                    profileId={1}
                    xKey="salinity"
                    yKey="temperature"
                    xLabel="Salinity (PSU)"
                    yLabel="Temperature (°C)"
                  />
                </div>
              )}
              {tdProfiles.length > 0 && (
                <div style={{ flex: '1 1 260px', minWidth: '260px' }}>
                  <PlotProfileTool
                    profiles={tdProfiles}
                    profileId={1}
                    xKey="depth"
                    yKey="temperature"
                    xLabel="Depth (m)"
                    yLabel="Temperature (°C)"
                    invertY={true}
                  />
                </div>
              )}
            </div>
            {compareTdProfiles.length > 0 && (
              <div style={{ marginTop: '0.75rem' }}>
                <CompareProfilesTool
                  profiles={compareTdProfiles}
                  profileIds={compareTdProfiles.map((p) => p.profileId)}
                  variable="TEMP"
                />
              </div>
            )}
            {compareTsProfiles.length >= 1 && (
              <div style={{ marginTop: '0.75rem' }}>
                <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>TS Comparison</div>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {compareTsProfiles.slice(0, 2).map((profile) => (
                    <div key={profile.profileId} style={{ flex: '1 1 260px', minWidth: '260px' }}>
                      <PlotProfileTool
                        profiles={[profile]}
                        profileId={profile.profileId}
                        xKey="salinity"
                        yKey="temperature"
                        xLabel={`Salinity (PSU) – ${profile.label || profile.profileId}`}
                        yLabel="Temperature (°C)"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;