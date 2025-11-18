import React, { useState, useMemo } from 'react';
import './DataSidebar.css';
import MapVisualization from './MapVisualization';
import PlotProfileTool from './PlotProfile';
import CompareProfilesTool from './CompareProfilesTool';
import MapTrajectories from './MapTrajectories';
import profiles from '../profiles_jan.json';
import trajectories from '../trajectories_jan.json';

const DataSidebar = ({ selectedView = 'table', onViewChange, mapData = null, showMap = false, onMapClose = () => {}, tableData = null, onOpenTrajectoryOverlay = () => {} }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [isMapVisible, setIsMapVisible] = useState(false);
  const [showProfilePreview, setShowProfilePreview] = useState(false);
  const [selectedFloatId, setSelectedFloatId] = useState('');
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [compareProfileId1, setCompareProfileId1] = useState(null);
  const [compareProfileId2, setCompareProfileId2] = useState(null);
  const [variable, setVariable] = useState('TEMP');
  const [showTrajectoryPreview, setShowTrajectoryPreview] = useState(false);

  const floatToProfiles = useMemo(() => {
    const map = new Map();
    trajectories.forEach((pt) => {
      if (!pt.floatId || pt.profileId === undefined || pt.profileId === null) return;
      const key = String(pt.floatId);
      if (!map.has(key)) map.set(key, new Set());
      map.get(key).add(pt.profileId);
    });
    const result = {};
    map.forEach((set, key) => {
      result[key] = Array.from(set);
    });
    return result;
  }, []);

  const floatOptions = useMemo(
    () => Object.keys(floatToProfiles).sort(),
    [floatToProfiles]
  );

  const profileOptionsForSelectedFloat = useMemo(() => {
    if (!selectedFloatId) return [];
    const ids = floatToProfiles[String(selectedFloatId)] || [];
    return profiles.filter((p) => ids.includes(p.profileId));
  }, [selectedFloatId, floatToProfiles]);

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  const handleViewChange = (e) => {
    const newView = e.target.value;
    if (onViewChange) {
      onViewChange(newView);
    }
  };

  const handleOpenMap = () => {
    setIsMapVisible(true);
  };

  const handleCloseMap = () => {
    setIsMapVisible(false);
    onMapClose();
  };

  // Auto-open map when new map data is received
  React.useEffect(() => {
    if (showMap && mapData) {
      setIsMapVisible(true);
      if (onViewChange) {
        onViewChange('map');
      }
    }
  }, [showMap, mapData, onViewChange]);

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
            {tableData && tableData.columns && tableData.rows && tableData.rows.length > 0 ? (
              <>
                <div className="table-row header">
                  {tableData.columns.slice(0, 5).map((col, idx) => (
                    <span key={idx} title={col}>
                      {col.length > 12 ? col.substring(0, 12) + '...' : col}
                    </span>
                  ))}
                </div>
                {tableData.rows.slice(0, 10).map((row, rowIdx) => (
                  <div className="table-row" key={rowIdx}>
                    {tableData.columns.slice(0, 5).map((col, colIdx) => {
                      const value = row[col];
                      let displayValue = value;
                      
                      // Format different data types
                      if (value === null || value === undefined) {
                        displayValue = '-';
                      } else if (typeof value === 'number') {
                        displayValue = value.toFixed(2);
                      } else if (typeof value === 'string' && value.length > 15) {
                        displayValue = value.substring(0, 15) + '...';
                      }
                      
                      return (
                        <span key={colIdx} title={String(value)}>
                          {String(displayValue)}
                        </span>
                      );
                    })}
                  </div>
                ))}
              </>
            ) : (
              <div className="no-data-message">
                <i className="fas fa-inbox"></i>
                <p>No data available</p>
                <small>Run a query to see results</small>
              </div>
            )}
          </div>
          <div className="view-more">
            {tableData && tableData.total_rows > 0 && (
              <div className="data-stats">
                <small>Showing {Math.min(10, tableData.total_rows)} of {tableData.total_rows} rows</small>
              </div>
            )}
            <button className="view-more-btn" disabled={!tableData || tableData.total_rows === 0}>
              View Full Table
            </button>
            <button className="view-more-btn" disabled={!tableData || tableData.total_rows === 0}>
              Export as CSV
            </button>
          </div>
          <div className="view-more" style={{ marginTop: '0.5rem' }}>
            <button
              className="view-more-btn"
              onClick={() => setShowProfilePreview(!showProfilePreview)}
            >
              {showProfilePreview ? 'Hide Profile Preview' : 'Show Profile Preview'}
            </button>
          </div>
          {showProfilePreview && (
            <div className="profile-section" style={{ marginTop: '0.5rem' }}>
              <h4>PlotProfile Preview</h4>
              <div className="profile-controls">
                <label>
                  Float ID:
                  <select
                    value={selectedFloatId}
                    onChange={(e) => {
                      const fid = e.target.value;
                      setSelectedFloatId(fid);
                      setSelectedProfileId(null);
                      setCompareProfileId1(null);
                      setCompareProfileId2(null);
                    }}
                  >
                    <option value="">Select float</option>
                    {floatOptions.map((fid) => (
                      <option key={fid} value={fid}>{fid}</option>
                    ))}
                  </select>
                </label>

                <label>
                  Profile ID:
                  <select
                    value={selectedProfileId ?? ''}
                    onChange={(e) =>
                      setSelectedProfileId(
                        e.target.value === '' ? null : Number(e.target.value)
                      )
                    }
                    disabled={!selectedFloatId}
                  >
                    <option value="">Select profile</option>
                    {profileOptionsForSelectedFloat.map((p) => (
                      <option key={p.profileId} value={p.profileId}>
                        {p.profileId}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Variable:
                  <select
                    value={variable}
                    onChange={(e) => setVariable(e.target.value)}
                  >
                    <option value="TEMP">Temperature</option>
                    <option value="SAL">Salinity</option>
                  </select>
                </label>
              </div>

              <PlotProfileTool
                profiles={profiles}
                profileId={selectedProfileId}
                variable={variable}
              />

              <h4 style={{ marginTop: '1rem' }}>Compare Profiles (same float)</h4>
              <div className="profile-controls">
                <label>
                  Profile A:
                  <select
                    value={compareProfileId1 ?? ''}
                    onChange={(e) =>
                      setCompareProfileId1(
                        e.target.value === '' ? null : Number(e.target.value)
                      )
                    }
                    disabled={!selectedFloatId}
                  >
                    <option value="">Select profile</option>
                    {profileOptionsForSelectedFloat.map((p) => (
                      <option key={p.profileId} value={p.profileId}>
                        {p.profileId}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Profile B:
                  <select
                    value={compareProfileId2 ?? ''}
                    onChange={(e) =>
                      setCompareProfileId2(
                        e.target.value === '' ? null : Number(e.target.value)
                      )
                    }
                    disabled={!selectedFloatId}
                  >
                    <option value="">Select profile</option>
                    {profileOptionsForSelectedFloat.map((p) => (
                      <option key={p.profileId} value={p.profileId}>
                        {p.profileId}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <CompareProfilesTool
                profiles={profiles}
                profileIds={
                  [compareProfileId1, compareProfileId2].filter(
                    (id) => id !== null && id !== undefined
                  )
                }
                variable={variable}
              />
            </div>
          )}
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
                {mapData ? (
                  <>
                    <span>{mapData.map_data?.length || 0} Data Points</span>
                    <span>{mapData.parameter?.charAt(0).toUpperCase() + mapData.parameter?.slice(1) || 'Temperature'} Data</span>
                    <span>{mapData.region?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Current Location'}</span>
                  </>
                ) : (
                  <>
                    <span>5 Argo Float Profiles</span>
                    <span>North Atlantic Region</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <div className="view-more">
            <button 
              className={`view-more-btn ${mapData ? 'has-data' : ''}`} 
              onClick={handleOpenMap}
            >
              {mapData ? '🗺️ View Data Map' : 'Open Map View'}
            </button>
          </div>
          <div className="view-more" style={{ marginTop: '0.5rem' }}>
            <button
              className="view-more-btn"
              onClick={() => setShowTrajectoryPreview(!showTrajectoryPreview)}
            >
              {showTrajectoryPreview ? 'Hide Trajectory Preview' : 'Show Trajectory Preview'}
            </button>
          </div>
          <div className="view-more" style={{ marginTop: '0.5rem' }}>
            <button
              className="view-more-btn"
              onClick={onOpenTrajectoryOverlay}
            >
              Open Trajectory Map (Full Screen)
            </button>
          </div>

          {showTrajectoryPreview && (
            <div style={{ marginTop: '0.5rem' }}>
              <MapTrajectories />
            </div>
          )}
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
      <div className="update-time">30 min ago</div>
      <div className="update-text">Float 4902917 battery low</div>
    </div>
    <div className="update-item">
      <div className="update-time">45 min ago</div>
      <div className="update-text">Salinity spike in Float 4902918</div>
    </div>
    <div className="update-item">
      <div className="update-time">1 hour ago</div>
      <div className="update-text">3 floats synchronized</div>
    </div>
    <div className="update-item">
      <div className="update-time">2 hours ago</div>
      <div className="update-text">Firmware update applied to Float 4902920</div>
    </div>
    <div className="update-item">
      <div className="update-time">3 hours ago</div>
      <div className="update-text">New float added: 4902921</div>
    </div>
  </div>
  <div className="view-more">
    <button className="view-more-btn">View All Updates</button>
  </div>
</div>
      )}

      {/* Map Visualization Component */}
      <MapVisualization
        mapData={mapData?.map_data}
        isVisible={isMapVisible}
        onClose={handleCloseMap}
        queryType={mapData?.query_type || 'general'}
        parameter={mapData?.parameter || 'temperature'}
      />
    </aside>
  );
};

export default DataSidebar;