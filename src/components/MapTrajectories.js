import React, { useMemo, useState } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import trajectoriesData from '../trajectories_jan.json';

function MapTrajectories({ points = trajectoriesData, selectedFloatIds, onProfileClick }) {
  const floats = useMemo(() => {
    const byFloat = new Map();
    points.forEach((p) => {
      if (p.floatId == null || p.lat == null || p.lon == null) return;
      const fid = String(p.floatId);
      if (!byFloat.has(fid)) byFloat.set(fid, []);
      byFloat.get(fid).push(p);
    });
    byFloat.forEach((arr, key) => {
      arr.sort((a, b) => (a.cycleNumber || 0) - (b.cycleNumber || 0));
    });
    return byFloat;
  }, [points]);

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

  const center = useMemo(() => {
    const all = points.filter((p) => p.lat != null && p.lon != null);
    if (all.length === 0) return [0, 0];
    const sum = all.reduce(
      (acc, p) => {
        return [acc[0] + p.lat, acc[1] + p.lon];
      },
      [0, 0]
    );
    return [sum[0] / all.length, sum[1] / all.length];
  }, [points]);

  const colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628'];

  return (
    <div style={{ width: '100%', height: '400px' }}>
      <div style={{ marginBottom: '0.5rem' }}>
        <label>
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
      </div>
      <MapContainer center={center} zoom={2} scrollWheelZoom={true} style={{ width: '100%', height: '100%' }}>
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

