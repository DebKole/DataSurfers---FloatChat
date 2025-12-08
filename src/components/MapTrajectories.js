import React, { useMemo, useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function MapTrajectories({
  center = { lat: -2, lon: 80 },
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
  const [daysWindow, setDaysWindow] = useState(10);

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
        const res = await fetch(`http://127.0.0.1:8000/floats/trajectories/radius?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        setPoints(data.trajectories || []);
      } catch (err) {
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
    () => Array.from(floats.keys()),
    [floats]
  );

  const [localFloatId, setLocalFloatId] = useState('');

  const visibleFloatIds = useMemo(() => {
    if (selectedFloatIds && selectedFloatIds.length > 0) {
      return selectedFloatIds.map((id) => String(id));
    }
    if (localFloatId) {
      return [String(localFloatId)];
    }
    return allFloatIds;
  }, [selectedFloatIds, localFloatId, allFloatIds]);

  const centerPoint = useMemo(() => {
    // Keep the map centered over the chosen region (e.g., Indian Ocean)
    return [center.lat, center.lon];
  }, [center.lat, center.lon]);

  const colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628'];

  const containerStyle = fullScreen
    ? { width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }
    : { width: '100%', height: '520px', display: 'flex', flexDirection: 'column' };

  return (
    <div style={containerStyle}>
      <div className={`sidebar-input-panel ${fullScreen ? 'full-screen' : ''}`} style={{ flexShrink: 0 }}>
        <div className="sidebar-input-container">
          <div className="sidebar-input-group">
            <label
              className={`sidebar-input-label ${fullScreen ? 'dark' : ''}`}
              htmlFor="sidebarFloatId"
            >
              Float ID
            </label>
            <select
              id="sidebarFloatId"
              className="sidebar-input-field"
              value={localFloatId}
              onChange={(e) => setLocalFloatId(e.target.value)}
            >
              <option value="">All floats</option>
              {allFloatIds.map((fid) => (
                <option key={fid} value={fid}>
                  {fid}
                </option>
              ))}
            </select>
          </div>

          <div className="sidebar-input-group sidebar-input-inline">
            <label
              className={`sidebar-input-label ${fullScreen ? 'dark' : ''}`}
              htmlFor="sidebarRadiusKm"
            >
              Radius (km)
            </label>
            <input
              id="sidebarRadiusKm"
              type="number"
              min={10}
              max={2000}
              step={10}
              className="sidebar-input-field sidebar-number-field"
              value={radius}
              onChange={(e) => {
                const val = Number(e.target.value);
                if (!Number.isNaN(val)) {
                  const clamped = Math.min(2000, Math.max(10, val));
                  setRadius(clamped);
                }
              }}
            />
          </div>
        </div>

        {fullScreen && (
          <>
            <div className="sidebar-slider-group">
              <label className={`sidebar-input-label ${fullScreen ? 'dark' : ''}`}>
                Radius Range
              </label>
              <input
                type="range"
                min={10}
                max={2000}
                step={10}
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}
              />
            </div>
            <div className="sidebar-input-container">
              <div className="sidebar-input-group sidebar-input-inline">
                <label className="sidebar-input-label dark" htmlFor="sidebarDaysWindow">
                  Days (history)
                </label>
                <input
                  id="sidebarDaysWindow"
                  type="number"
                  min={1}
                  max={30}
                  step={1}
                  className="sidebar-input-field sidebar-number-field"
                  value={daysWindow}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    if (!Number.isNaN(val)) {
                      const clamped = Math.min(30, Math.max(1, val));
                      setDaysWindow(clamped);
                    }
                  }}
                />
              </div>
              <div className="sidebar-slider-group">
                <label className={`sidebar-input-label ${fullScreen ? 'dark' : ''}`}>
                  Days Range
                </label>
                <input
                  type="range"
                  min={1}
                  max={30}
                  step={1}
                  value={daysWindow}
                  onChange={(e) => setDaysWindow(Number(e.target.value))}
                />
              </div>
            </div>
          </>
        )}

        <div className="sidebar-status-line">
          {loading && <span>Loading trajectories…</span>}
          {error && !loading && <span className="sidebar-error">Error: {error}</span>}
        </div>
      </div>
      <MapContainer
        center={centerPoint}
        zoom={2}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%', flex: 1 }}
      >
        <TileLayer
          // attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
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
              <Polyline positions={latlngs} color={color} weight={2} dashArray="4 8" />
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
                      if (onProfileClick) {
                        onProfileClick(p.profileId);
                      }
                    },
                  }}
                >
                  <Popup>
                    <div style={{ fontSize: '0.8rem' }}>
                      <div><strong>Float ID:</strong> {p.floatId ?? 'N/A'}</div>
                      <div><strong>Profile ID:</strong> {p.profileId ?? 'N/A'}</div>
                      <div><strong>Cycle:</strong> {p.cycleNumber ?? 'N/A'}</div>
                      <div>
                        <strong>Position:</strong> {p.lat?.toFixed?.(2)}, {p.lon?.toFixed?.(2)}
                      </div>
                      <div>
                        <strong>Time:</strong>{' '}
                        {p.datetime ? new Date(p.datetime).toLocaleString() : 'N/A'}
                      </div>
                    </div>
                  </Popup>
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
                      if (onProfileClick) {
                        onProfileClick(lastPt.profileId);
                      }
                    },
                  }}
                >
                  <Popup>
                    <div style={{ fontSize: '0.8rem' }}>
                      <div><strong>Float ID:</strong> {lastPt.floatId ?? 'N/A'}</div>
                      <div><strong>Profile ID:</strong> {lastPt.profileId ?? 'N/A'}</div>
                      <div><strong>Cycle:</strong> {lastPt.cycleNumber ?? 'N/A'}</div>
                      <div>
                        <strong>Position:</strong> {lastPt.lat?.toFixed?.(2)}, {lastPt.lon?.toFixed?.(2)}
                      </div>
                      <div>
                        <strong>Time:</strong>{' '}
                        {lastPt.datetime ? new Date(lastPt.datetime).toLocaleString() : 'N/A'}
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
  );
}

export default MapTrajectories;



