import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

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

        {/* Alert Section
        <div className="alert-section">
          <div className="temperature-alert">
            <h3>Temperature Alert</h3>
            <p>Latest SST: {stats.avgTemperature}°C - Delta vs mean: -1.47°C</p>
            
            <div className="threshold-table">
              <table>
                <thead>
                  <tr>
                    <th>Mean SST (°C)</th>
                    <th>Yellow threshold (±°C)</th>
                    <th>Orange threshold (±°C)</th>
                    <th>Red threshold (±°C)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>28</td>
                    <td>0.5</td>
                    <td>1</td>
                    <td>1.5</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div> */}

        {/* Stats Grid
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Active Floats</h3>
            <div className="stat-value">{stats.totalProfiles}</div>
            <div className="stat-trend positive">+12 from last week</div>
          </div>

          <div className="stat-card">
            <h3>Global Coverage</h3>
            <div className="stat-value">{stats.globalCoverage}%</div>
            <div className="stat-trend positive">+2.1% from last week</div>
          </div>

          <div className="stat-card">
            <h3>Avg Temperature</h3>
            <div className="stat-value">{stats.avgTemperature}°C</div>
            <div className="stat-trend positive">+0.3°C from last week</div>
          </div>

          <div className="stat-card">
            <h3>Data Quality</h3>
            <div className="stat-value">{stats.dataQuality}%</div>
            <div className="stat-trend positive">+0.8% from last week</div>
          </div>
        </div> */}

        {/* Charts Section */}
        <div className="charts-section">
          <div className="chart-container full-width">
            {renderLineGraph()}
          </div>

          {/* <div className="recent-profiles">
            <h3>Recent Profiles</h3>
            <p>Latest data from ARGO floats</p>
            
            <div className="profile-list">
              <div className="profile-item">
                <div className="profile-id">4902916</div>
                <div className="profile-location">North Atlantic</div>
                <div className="profile-time">2 hours ago</div>
                <div className="profile-depth">2000m</div>
                <div className="profile-quality excellent">Excellent</div>
              </div>
              
              <div className="profile-item">
                <div className="profile-id">4902917</div>
                <div className="profile-location">Pacific Ocean</div>
                <div className="profile-time">4 hours ago</div>
                <div className="profile-depth">1500m</div>
                <div className="profile-quality great">Great</div>
              </div>
            </div>
          </div> */}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;