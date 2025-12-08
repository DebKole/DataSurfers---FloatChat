import React, { useState, useEffect, useRef, useMemo } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import "./MapComponent.css";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const MapComponent = ({ fullPage = false, data = null, selectedFloatIds = [] }) => {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const [loading, setLoading] = useState(true);
  // const markersLayerRef = useRef(null);
  // const [floatData, setFloatData] = useState([]);

  const [error, setError] = useState(null);
  const [trajectories, setTrajectories] = useState([]);
  const [radiusKm, setRadiusKm] = useState(2000);
  const [daysWindow, setDaysWindow] = useState(10);
  const [localFloatId, setLocalFloatId] = useState('');
  const [showTrajectories, setShowTrajectories] = useState({});
  const [hoveredFloat, setHoveredFloat] = useState(null);

  // Colors for different trajectory lines (using yellow for all markers)
  const colors = ['#ffeb3b', '#ffeb3b', '#ffeb3b', '#ffeb3b', '#ffeb3b', '#ffeb3b'];

  // Fetch trajectory data
  useEffect(() => {
    const fetchTrajectories = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          lat: '10',
          lon: '70',
          radius: String(radiusKm),
          limit: '50',
        });
        const res = await fetch(`http://localhost:8000/floats/trajectories/radius?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        setTrajectories(data.trajectories || []);
      } catch (err) {
        console.error("Error fetching trajectory data:", err);
        setError(err.message || String(err));
        setTrajectories([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTrajectories();
  }, [radiusKm]);

  // Process trajectory data
  const { floats, allFloatIds } = useMemo(() => {
    const byFloat = new Map();
    const validTrajectories = trajectories.filter(
      p => p.floatId != null && p.lat != null && p.lon != null
    );

    validTrajectories.forEach((p) => {
      const fid = String(p.floatId);
      if (!byFloat.has(fid)) byFloat.set(fid, []);
      byFloat.get(fid).push(p);
    });
    // Sort points by cycle number
    byFloat.forEach((arr) => {
      arr.sort((a, b) => (a.cycleNumber || 0) - (b.cycleNumber || 0));
    });

    return {
      floats: byFloat,
      allFloatIds: Array.from(byFloat.keys())
    };
  }, [trajectories]);

    // Determine which float IDs to show
  const visibleFloatIds = useMemo(() => {
    if (selectedFloatIds && selectedFloatIds.length > 0) {
      return selectedFloatIds.map(String);
    }
    if (localFloatId) {
      return [String(localFloatId)];
    }
    return allFloatIds;
  }, [selectedFloatIds, localFloatId, allFloatIds]);

  // Render the map and trajectories
  return (
    <div className={`map-component ${fullPage ? "full-page" : ""}`}>
      <div className="map-container">
        {loading && (
          <div className="map-loading">
            <i className="fas fa-spinner fa-spin"></i>
            <p>Loading map...</p>
          </div>
        )}

        <MapContainer
          center={[10, 70]} // Indian Ocean-ish
          zoom={3}
          scrollWheelZoom={true}
          style={{ width: "100%", height: "100%" }}
          whenCreated={map => { mapRef.current = map; }}
        >
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
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
                {prevPts.map((p, idx) => (
                  <CircleMarker
                    key={p.profileId}
                    center={[p.lat, p.lon]}
                    radius={4}
                    color="#ffeb3b"
                    fillColor="#ffeb3b"
                    weight={1}
                    opacity={0.9}
                    fillOpacity={0.7}
                    eventHandlers={{
                      click: () => {
                        setShowTrajectories(prev => ({
                          ...prev,
                          [fid]: !prev[fid]
                        }));
                      },
                      mouseover: () => setHoveredFloat({ id: fid, point: p }),
                      mouseout: () => setHoveredFloat(null)
                    }}
                  >
                    {(hoveredFloat?.id === fid && hoveredFloat?.point.profileId === p.profileId) && (
                      <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent>
                        <div style={{ fontSize: '0.8rem' }}>
                          <div><strong>Float ID:</strong> {p.floatId ?? 'N/A'}</div>
                          <div><strong>Cycle:</strong> {p.cycleNumber ?? 'N/A'}</div>
                          <div><em>Click to {showTrajectories[fid] ? 'hide' : 'show'} trajectory</em></div>
                        </div>
                      </Tooltip>
                    )}
                  </CircleMarker>
                ))}
                {lastPt && (
                  <CircleMarker
                    key={`${fid}-current`}
                    center={[lastPt.lat, lastPt.lon]}
                    radius={8}
                    color="#ffeb3b"
                    fillColor="#ffeb3b"
                    weight={1.5}
                    opacity={1}
                    fillOpacity={0.9}
                    eventHandlers={{
                      click: () => {
                        setShowTrajectories(prev => ({
                          ...prev,
                          [fid]: !prev[fid]
                        }));
                      },
                      mouseover: () => setHoveredFloat({ id: fid, point: lastPt }),
                      mouseout: () => setHoveredFloat(null)
                    }}
                  >
                    {(hoveredFloat?.id === fid && hoveredFloat?.point.profileId === lastPt.profileId) && (
                      <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent>
                        <div style={{ fontSize: '0.8rem' }}>
                          <div><strong>Float ID:</strong> {lastPt.floatId ?? 'N/A'}</div>
                          <div><strong>Cycle:</strong> {lastPt.cycleNumber ?? 'N/A'}</div>
                          <div><strong>Position:</strong> {lastPt.lat?.toFixed?.(2)}, {lastPt.lon?.toFixed?.(2)}</div>
                          <div><strong>Time:</strong> {lastPt.datetime ? new Date(lastPt.datetime).toLocaleString() : 'N/A'}</div>
                          <div><em>Click to {showTrajectories[fid] ? 'hide' : 'show'} trajectory</em></div>
                        </div>
                      </Tooltip>
                    )}
                    <Popup>
                      <div style={{ fontSize: '0.8rem', color: '#000' }}>
                        <div><strong>Float ID:</strong> {lastPt.floatId ?? 'N/A'}</div>
                        <div><strong>Profile ID:</strong> {lastPt.profileId ?? 'N/A'}</div>
                        <div><strong>Cycle:</strong> {lastPt.cycleNumber ?? 'N/A'}</div>
                        <div><strong>Position:</strong> {lastPt.lat?.toFixed?.(2)}, {lastPt.lon?.toFixed?.(2)}</div>
                        <div><strong>Time:</strong> {lastPt.datetime ? new Date(lastPt.datetime).toLocaleString() : 'N/A'}</div>
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
                              background: '#ffeb3b',
                              color: '#1a202c',
                              border: 'none',
                              padding: '4px 8px',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '0.8rem',
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

      <div className="map-info">
        <div className="data-summary">
          <span>
            <i className="fas fa-map-marker-alt"></i>
            {allFloatIds.length} Active Floats
          </span>
          <span>
            <i className="fas fa-calendar"></i> Last {daysWindow} Days
          </span>
          <span>
            <i className="fas fa-ruler"></i> Radius: {radiusKm} km
          </span>
          <span>
            <i className="fas fa-info-circle"></i> Click on any point to {Object.values(showTrajectories).some(v => v) ? 'hide' : 'show'} its trajectory
          </span>
        </div>
      </div>
    </div>
  );

  

    // Sort points by cycle number
    // byFloat.forEach((arr) => {
    //   arr.sort((a, b) => (a.cycleNumber || 0) - (b.cycleNumber || 0));
    // });

  //   return {
  //     floats: byFloat,
  //     allFloatIds: Array.from(byFloat.keys())
  //   };
  // }, [trajectories]);

  // -------------------------------------------------------
  // 1. Fetch float data from backend
  // -------------------------------------------------------
  // useEffect(() => {
  //   const fetchFloatData = async () => {
  //     try {
  //       const res = await fetch(
  //         "http://localhost:8000/floats/indian-ocean?limit=50"
  //       );
  //       const json = await res.json();

  //       if (json.status === 200 && Array.isArray(json.floats)) {
  //         const transformed = json.floats.map((f) => ({
  //           id: f.float_id,
  //           lat: parseFloat(f.latitude),
  //           lng: parseFloat(f.longitude),
  //           datetime: f.datetime,
  //           cycle: f.cycle_number,
  //           measurements: f.measurement_count,
  //           profile_id: f.global_profile_id,
  //         }));

  //         setFloatData(transformed);
  //       } else {
  //         setFloatData([]);
  //       }
  //     } catch (err) {
  //       console.error("Error fetching float data:", err);
  //       setFloatData([]);
  //     } finally {
  //       setLoading(false);
  //     }
  //   };

  //   fetchFloatData();
  // }, []);

  // // -------------------------------------------------------
  // // 2. Initialize Leaflet map ONCE
  // // -------------------------------------------------------
  // useEffect(() => {
  //   if (!mapContainerRef.current || mapRef.current) return;

  //   const map = L.map(mapContainerRef.current, {
  //     center: [10, 70], // Indian Ocean-ish
  //     zoom: 3,
  //     zoomControl: true,
  //     scrollWheelZoom: true,
  //   });

  //   L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
  //     attribution: "Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
  //   }).addTo(map);

  //   mapRef.current = map;
  //   markersLayerRef.current = L.layerGroup().addTo(map);

  //   return () => {
  //     if (mapRef.current) {
  //       mapRef.current.remove();
  //       mapRef.current = null;
  //     }
  //     markersLayerRef.current = null;
  //   };
  // }, []);

  // -------------------------------------------------------
  // 3. Helper: render markers on the map
  // -------------------------------------------------------
  // const renderMarkers = (points) => {
  //   const map = mapRef.current;
  //   const layer = markersLayerRef.current;
  //   if (!map || !layer) return;

  //   layer.clearLayers();
  //   const created = [];

  //   (points || []).forEach((point) => {
  //     const lat = Number(point.lat ?? point.latitude);
  //     const lng = Number(point.lng ?? point.longitude);
  //     if (Number.isNaN(lat) || Number.isNaN(lng)) return;

  //     const color = "#1e90ff";

  //     const marker = L.circleMarker([lat, lng], {
  //       radius: 6,
  //       color: color,
  //       weight: 2,
  //       fillColor: color,
  //       fillOpacity: 0.85,
  //     });

  //     const id = point.id || point.float_id || point.profile_id || '—';
  //     const dateStr = point.datetime 
  //       ? new Date(point.datetime).toLocaleString() 
  //       : '';

  //     marker.bindTooltip(`Float ${id}`, { direction: 'top', offset: [0, -6] });

  //     marker.bindPopup(`
  //       <div class="map-popup">
  //         <h4>Float ${id}</h4>
  //         <p><strong>Location:</strong> ${lat.toFixed(2)}°, ${lng.toFixed(2)}°</p>
  //         ${dateStr ? `<p><strong>Date:</strong> ${dateStr}</p>` : ''}
  //         ${point.cycle ? `<p><strong>Cycle:</strong> ${point.cycle}</p>` : ''}
  //         ${point.measurements ? `<p><strong>Measurements:</strong> ${point.measurements}</p>` : ''}
  //       </div>
  //     `);

  //     marker.on('mouseover', () => marker.setStyle({ radius: 9, fillOpacity: 1 }));
  //     marker.on('mouseout', () => marker.setStyle({ radius: 6, fillOpacity: 0.85 }));
  //     marker.addTo(layer);
  //     created.push(marker);
  //   });

  //   if (created.length > 0) {
  //     const group = L.featureGroup(created);
  //     const bounds = group.getBounds();
  //     if (bounds.isValid()) {
  //       map.fitBounds(bounds.pad(0.2));
  //     }
  //   }
  // };

  // -------------------------------------------------------
  // 4. Update markers when data changes
  //    - If `data` prop is provided, use that
  //    - Otherwise use fetched floatData
  // -------------------------------------------------------
  // useEffect(() => {
  //   if (data && Array.isArray(data) && data.length > 0) {
  //     renderMarkers(data);
  //   } else if (!loading && floatData.length > 0) {
  //     renderMarkers(floatData);
  //   }
  // }, [data, floatData, loading]);

  // -------------------------------------------------------
  // UI
  // -------------------------------------------------------
  // return (
  //   <div className={`map-component ${fullPage ? "full-page" : ""}`}>
  //     <div className="map-container">
  //       {loading && (
  //         <div className="map-loading">
  //           <i className="fas fa-spinner fa-spin"></i>
  //           <p>Loading map...</p>
  //         </div>
  //       )}

  //       <div
  //         ref={mapContainerRef}
  //         className="map-display"
  //         style={{ width: "100%", height: "100%" }}
  //       />
  //     </div>

  //     <div className="map-info">
  //       <div className="data-summary">
  //         <span>
  //           <i className="fas fa-map-marker-alt"></i>{" "}
  //           {floatData.length} Active Floats
  //         </span>
  //         <span>
  //           <i className="fas fa-calendar"></i> January 2025 Data
  //         </span>
  //         <span>
  //           <i className="fas fa-globe"></i> Indian Ocean Region
  //         </span>
  //       </div>
  //     </div>
  //   </div>
  // );
};

export default MapComponent;