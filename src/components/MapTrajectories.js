import React, { useMemo, useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function MapTrajectories({
  center = { lat: -2, lon: 80 },
  radiusKm = 2000,
  limit = 100,
  selectedFloatIds,
  onProfileClick,
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
  }, [filteredPoints, center.lat, center.lon]);

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

  return (
    <div style={{ width: '100%', height: '400px' }}>
      <div style={{ marginBottom: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label style={{ color: '#003366' }}>
            Float ID:
            <select
              value={localFloatId}
              onChange={(e) => setLocalFloatId(e.target.value)}
            >
              <option value="">All floats</option>
              {allFloatIds.map((fid) => (
                <option key={fid} value={fid}>{fid}</option>
              ))}
            </select>
          </label>
          <div>
            {loading && <span style={{ fontSize: '0.85rem', marginRight: '0.5rem' }}>Loading trajectories…</span>}
            {error && !loading && (
              <span style={{ fontSize: '0.85rem', color: 'red' }}>Error: {error}</span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.85rem', color: '#003366' }}>Radius (km):</label>
            <input
              type="number"
              min={10}
              max={2000}
              step={10}
              value={radius}
              onChange={(e) => {
                const val = Number(e.target.value);
                if (!Number.isNaN(val)) {
                  const clamped = Math.min(2000, Math.max(10, val));
                  setRadius(clamped);
                }
              }}
              style={{ width: '80px' }}
            />
            <input
              type="range"
              min={10}
              max={2000}
              step={10}
              value={radius}
              onChange={(e) => setRadius(Number(e.target.value))}
              style={{ flexGrow: 1 }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.85rem', color: '#003366' }}>Days (history):</label>
            <input
              type="number"
              min={1}
              max={30}
              step={1}
              value={daysWindow}
              onChange={(e) => {
                const val = Number(e.target.value);
                if (!Number.isNaN(val)) {
                  const clamped = Math.min(30, Math.max(1, val));
                  setDaysWindow(clamped);
                }
              }}
              style={{ width: '80px' }}
            />
            <input
              type="range"
              min={1}
              max={30}
              step={1}
              value={daysWindow}
              onChange={(e) => setDaysWindow(Number(e.target.value))}
              style={{ flexGrow: 1 }}
            />
          </div>
        </div>
      </div>
      <MapContainer center={centerPoint} zoom={2} scrollWheelZoom={true} style={{ width: '100%', height: '100%' }}>
        <TileLayer
          attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
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
                />
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
                />
              )}
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
}

export default MapTrajectories;

