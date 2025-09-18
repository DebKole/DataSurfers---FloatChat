import React, { useState } from 'react';
import './DataSidebar.css';

const DataSidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedView, setSelectedView] = useState('table');

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  const handleViewChange = (e) => {
    setSelectedView(e.target.value);
  };

  return (
    <aside className={`data-sidebar ${collapsed ? 'collapsed' : ''}`} id="rightSidebar" aria-label="Data overview sidebar">
      <div className="data-header">
        <i className="fas fa-chart-line" aria-hidden="true"></i>
        <h2>Data Overview</h2>
      </div>

      <button className="collapse-btn right-toggle" onClick={toggleSidebar} aria-expanded={!collapsed} title="Collapse overview">
        <i className={`fas ${collapsed ? 'fa-chevron-left' : 'fa-chevron-right'}`} aria-hidden="true"></i>
      </button>

      <div className={`view-selector ${collapsed ? 'hidden' : ''}`}>
        <select value={selectedView} onChange={handleViewChange} className="view-dropdown">
          <option value="table">Table</option>
          <option value="map">Map</option>
          <option value="updates">Latest Updates</option>
        </select>
      </div>

      {collapsed && (
        <div className="collapsed-view-icons">
          <div className="collapsed-icon" title="Table">
            <i className="fas fa-table"></i>
          </div>
          <div className="collapsed-icon" title="Map">
            <i className="fas fa-map"></i>
          </div>
          <div className="collapsed-icon" title="Latest Updates">
            <i className="fas fa-clock"></i>
          </div>
        </div>
      )}

      {selectedView === 'table' && (
        <div className="data-card">
          <h3><i className="fas fa-table"></i> Table</h3>
          <div className="table-preview">
            <div className="table-row header">
              <span>Float ID</span>
              <span>Temp</span>
              <span>Salinity</span>
            </div>
            <div className="table-row">
              <span>4902916</span>
              <span>22.4°C</span>
              <span>35.1</span>
            </div>
            <div className="table-row">
              <span>4902917</span>
              <span>21.8°C</span>
              <span>35.3</span>
            </div>
            <div className="table-row">
              <span>4902918</span>
              <span>23.1°C</span>
              <span>34.9</span>
            </div>
          </div>
          <div className="view-more">
            <button className="view-more-btn">View Full Table</button>
          </div>
        </div>
      )}

      {selectedView === 'map' && (
        <div className="data-card">
          <h3><i className="fas fa-map"></i> Map</h3>
          <div className="map-preview">
            <div className="map-placeholder">
              <i className="fas fa-globe"></i>
              <p>Interactive Ocean Map</p>
              <div className="map-stats">
                <span>47 Active Floats</span>
                <span>North Atlantic Region</span>
              </div>
            </div>
          </div>
          <div className="view-more">
            <button className="view-more-btn">Open Map View</button>
          </div>
        </div>
      )}

      {selectedView === 'updates' && (
        <div className="data-card">
          <h3><i className="fas fa-clock"></i> Latest Updates</h3>
          <div className="update-list">
            <div className="update-item">
              <div className="update-time">2 min ago</div>
              <div className="update-text">New data from Float 4902916</div>
            </div>
            <div className="update-item">
              <div className="update-time">15 min ago</div>
              <div className="update-text">Temperature anomaly detected</div>
            </div>
            <div className="update-item">
              <div className="update-time">1 hour ago</div>
              <div className="update-text">3 floats synchronized</div>
            </div>
          </div>
          <div className="view-more">
            <button className="view-more-btn">View All Updates</button>
          </div>
        </div>
      )}
    </aside>
  );
};

export default DataSidebar;