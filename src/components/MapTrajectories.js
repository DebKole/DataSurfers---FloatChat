import React, { useMemo, useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import "./MapComponent.css";

function MapTrajectories({
  center = { lat: 10, lon: 70 }, // Default to Indian Ocean
  radiusKm = 2000,
  limit = 100,
  selectedFloatIds,
  onProfileClick,
  fullScreen = false,
}) {
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [radius, setRadius] = useState(radiusKm);
  const [daysWindow, setDaysWindow] = useState(365);
  const [localFloatId, setLocalFloatId] = useState('');
  const [showTrajectories, setShowTrajectories] = useState({});
  const [hoveredFloat, setHoveredFloat] = useState(null);

  // Use yellow for all markers as requested
  const colors = ['#ffeb3b', '#ffeb3b', '#ffeb3b', '#ffeb3b', '#ffeb3b', '#ffeb3b'];

  useEffect(() => {
    const fetchTrajectories = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          lat: String(center.lat),
          lon: String(center.lon),
          radius: String(radius),
          limit: String(limit),
        });
        const res = await fetch(`http://localhost:8000/floats/trajectories/radius?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        setPoints(data.trajectories || []);
      } catch (err) {
        console.error("Error fetching trajectory data:", err);
        setError(err.message || String(err));
        setPoints([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTrajectories();
  }, [center.lat, center.lon, radius, limit]);

  const filteredPoints = useMemo(() => {
    if (!points || points.length === 0) return [];
    // Find the latest datetime across all points
    const parsed = points
      .map((p) => ({
        ...p,
        _t: p.datetime ? new Date(p.datetime).getTime() : null,
      }))
      .filter((p) => p._t != null && !Number.isNaN(p._t));

    if (parsed.length === 0) return points;

    const maxTime = parsed.reduce((max, p) => (p._t > max ? p._t : max), parsed[0]._t);
    const windowMs = daysWindow * 24 * 60 * 60 * 1000;
    const cutoff = maxTime - windowMs;

    return parsed.filter((p) => p._t >= cutoff);
  }, [points, daysWindow]);

  const floats = useMemo(() => {
    const byFloat = new Map();
    filteredPoints.forEach((p) => {
      if (p.floatId == null || p.lat == null || p.lon == null) return;
      const fid = String(p.floatId);
      if (!byFloat.has(fid)) byFloat.set(fid, []);
      byFloat.get(fid).push(p);
    });
    byFloat.forEach((arr, key) => {
      arr.sort((a, b) => (a.cycleNumber || 0) - (b.cycleNumber || 0));
    });
    return byFloat;
  }, [filteredPoints]);

  const allFloatIds = useMemo(
    () => Array.from(floats.keys()).sort(),
    [floats]
  );

  const visibleFloatIds = useMemo(() => {
    if (selectedFloatIds && selectedFloatIds.length > 0) {
      return selectedFloatIds.map((id) => String(id));
    }
    if (localFloatId) {
      return [String(localFloatId)];
    }
    return allFloatIds;
  }, [selectedFloatIds, localFloatId, allFloatIds]);

  const containerStyle = fullScreen
    ? { width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }
    : { width: '100%', height: '520px', display: 'flex', flexDirection: 'column' };

  return (
    <div style={containerStyle} className="map-component">
      <div className={`sidebar-input-panel ${fullScreen ? 'full-screen' : ''}`} style={{ flexShrink: 0, padding: '10px', background: '#1a202c', color: 'white' }}>
        <div className="sidebar-input-container" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <div className="sidebar-input-group">
            <label className="sidebar-input-label" htmlFor="sidebarFloatId" style={{ display: 'block', fontSize: '0.8rem', marginBottom: '4px' }}>
              Float ID
            </label>
            <select
              id="sidebarFloatId"
              className="sidebar-input-field"
              value={localFloatId}
              onChange={(e) => setLocalFloatId(e.target.value)}
              style={{ background: '#2d3748', color: 'white', border: '1px solid #4a5568', padding: '4px', borderRadius: '4px' }}
            >
              <option value="">All floats</option>
              {allFloatIds.map((fid) => (
                <option key={fid} value={fid}>
                  {fid}
                </option>
              ))}
            </select>
          </div>

          <div className="sidebar-input-group">
            <label className="sidebar-input-label" htmlFor="sidebarRadiusKm" style={{ display: 'block', fontSize: '0.8rem', marginBottom: '4px' }}>
              Radius (km): {radius}
            </label>
            <input
              type="range"
              min={10}
              max={2000}
              step={10}
              value={radius}
              onChange={(e) => setRadius(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div className="sidebar-input-group">
            <label className="sidebar-input-label" htmlFor="sidebarDaysWindow" style={{ display: 'block', fontSize: '0.8rem', marginBottom: '4px' }}>
              History (days): {daysWindow}
            </label>
            <input
              type="range"
              min={1}
              max={365}
              step={1}
              value={daysWindow}
              onChange={(e) => setDaysWindow(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <div className="sidebar-status-line" style={{ marginTop: '8px', fontSize: '0.8rem', color: '#a0aec0' }}>
          {loading && <span>Loading trajectories...</span>}
          {error && !loading && <span style={{ color: '#fc8181' }}>Error: {error}</span>}
          {!loading && !error && <span>Found {allFloatIds.length} floats</span>}
        </div>
      </div>

      <div className="map-container" style={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={[center.lat, center.lon]}
          zoom={3}
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%' }}
        >
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="Tiles © Esri"
          />
          {visibleFloatIds.map((fid, idx) => {
            const pts = floats.get(fid) || [];
            if (pts.length === 0) return null;
            const color = colors[idx % colors.length];
            const latlngs = pts.map((p) => [p.lat, p.lon]);

            const lastIndex = pts.length - 1;
            const lastPt = pts[lastIndex];
            const prevPts = pts.slice(0, lastIndex);

            return (
              <React.Fragment key={fid}>
                {showTrajectories[fid] && (
                  <Polyline
                    positions={latlngs}
                    color={color}
                    weight={2}
                    dashArray="4 8"
                  />
                )}
                {prevPts.map((p) => (
                  <CircleMarker
                    key={p.profileId}
                    center={[p.lat, p.lon]}
                    radius={3}
                    color={color}
                    opacity={0.5}
                    fillOpacity={0.4}
                    eventHandlers={{
                      click: () => {
                        setShowTrajectories(prev => ({
                          ...prev,
                          [fid]: !prev[fid]
                        }));
                        if (onProfileClick) onProfileClick(p.profileId);
                      },
                      mouseover: () => setHoveredFloat({ id: fid, point: p }),
                      mouseout: () => setHoveredFloat(null)
                    }}
                  >
                    {(hoveredFloat?.id === fid && hoveredFloat?.point.profileId === p.profileId) && (
                      <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent>
                        <div style={{ fontSize: '0.8rem' }}>
                          <div><strong>Float ID:</strong> {p.floatId}</div>
                          <div><strong>Cycle:</strong> {p.cycleNumber}</div>
                          <div><em>Click to toggle trajectory</em></div>
                        </div>
                      </Tooltip>
                    )}
                  </CircleMarker>
                ))}
                {lastPt && (
                  <CircleMarker
                    key={`${fid}-current`}
                    center={[lastPt.lat, lastPt.lon]}
                    radius={6}
                    color={color}
                    opacity={1}
                    fillOpacity={0.9}
                    eventHandlers={{
                      click: () => {
                        setShowTrajectories(prev => ({
                          ...prev,
                          [fid]: !prev[fid]
                        }));
                        if (onProfileClick) onProfileClick(lastPt.profileId);
                      },
                      mouseover: () => setHoveredFloat({ id: fid, point: lastPt }),
                      mouseout: () => setHoveredFloat(null)
                    }}
                  >
                    {(hoveredFloat?.id === fid && hoveredFloat?.point.profileId === lastPt.profileId) && (
                      <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent>
                        <div style={{ fontSize: '0.8rem' }}>
                          <div><strong>Float ID:</strong> {lastPt.floatId}</div>
                          <div><strong>Cycle:</strong> {lastPt.cycleNumber}</div>
                          <div><strong>Time:</strong> {new Date(lastPt.datetime).toLocaleDateString()}</div>
                          <div><em>Click to toggle trajectory</em></div>
                        </div>
                      </Tooltip>
                    )}
                    <Popup>
                      <div style={{ fontSize: '0.8rem', color: '#000' }}>
                        <div><strong>Float ID:</strong> {lastPt.floatId}</div>
                        <div><strong>Profile ID:</strong> {lastPt.profileId}</div>
                        <div><strong>Cycle:</strong> {lastPt.cycleNumber}</div>
                        <div><strong>Position:</strong> {lastPt.lat?.toFixed(2)}, {lastPt.lon?.toFixed(2)}</div>
                        <div><strong>Time:</strong> {new Date(lastPt.datetime).toLocaleString()}</div>
                        <div style={{ marginTop: '8px' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowTrajectories(prev => ({
                                ...prev,
                                [fid]: !prev[fid]
                              }));
                            }}
                            style={{
                              background: color,
                              color: '#1a202c',
                              border: 'none',
                              padding: '4px 8px',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontWeight: 'bold'
                            }}
                          >
                            {showTrajectories[fid] ? 'Hide' : 'Show'} Trajectory
                          </button>
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                )}
              </React.Fragment>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}

export default MapTrajectories;