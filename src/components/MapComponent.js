import React, { useState, useEffect, useRef } from "react";
import "./MapComponent.css";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const MapComponent = ({ fullPage = false, data = null }) => {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markersLayerRef = useRef(null);

  const [floatData, setFloatData] = useState([]);
  const [loading, setLoading] = useState(true);

  // -------------------------------------------------------
  // 1. Fetch float data
  // -------------------------------------------------------
  useEffect(() => {
    const fetchFloatData = async () => {
      try {
        const res = await fetch(
          "http://localhost:8000/floats/indian-ocean?limit=50"
        );
        const json = await res.json();

        if (json.status === 200 && json.floats) {
          const transformed = json.floats.map((f) => ({
            id: f.float_id,
            lat: parseFloat(f.latitude),
            lng: parseFloat(f.longitude),
            datetime: f.datetime,
            cycle: f.cycle_number,
            measurements: f.measurement_count,
            profile_id: f.global_profile_id,
          }));

          setFloatData(transformed);
        }
      } catch (err) {
        console.error("Error fetching float data:", err);
        setFloatData([]);
      }

      setLoading(false);
    };

    fetchFloatData();
  }, []);

  // -------------------------------------------------------
  // 2. Initialize map ONCE
  // -------------------------------------------------------
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Create map
    mapRef.current = L.map(mapContainerRef.current, {
      center: [10, 70],
      zoom: 3,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    // Add tiles
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "OpenStreetMap contributors",
    }).addTo(mapRef.current);

    // Layer group for markers
    markersLayerRef.current = L.layerGroup().addTo(mapRef.current);

    return () => {
      // Clean up on unmount
      if (mapRef.current) {
        mapRef.current.remove();
      }
    };
  }, []);

  // -------------------------------------------------------
  // 3. Render markers (for floatData or incoming props.data)
  // -------------------------------------------------------
  const renderMarkers = (points) => {
    const map = mapRef.current;
    if (!map || !markersLayerRef.current) return;

    markersLayerRef.current.clearLayers();
    const created = [];

    points.forEach((p) => {
      if (isNaN(p.lat) || isNaN(p.lng)) return;

      const marker = L.circleMarker([p.lat, p.lng], {
        radius: 6,
        color: '#1e90ff',
        weight: 2,
        fillColor: '#1e90ff',
        fillOpacity: 0.85
      });

      const id = p.id || p.float_id || p.profile_id || '—';
      const dateStr = p.datetime ? new Date(p.datetime).toLocaleDateString() : '';

      marker.bindTooltip(`Float ${id}`, { direction: 'top', offset: [0, -6] });
      marker.bindPopup(`
        <div class="map-popup">
          <h4>Float ${id}</h4>
          <p><strong>Location:</strong> ${Number(p.lat).toFixed(2)}°, ${Number(p.lng).toFixed(2)}°</p>
          ${dateStr ? `<p><strong>Date:</strong> ${dateStr}</p>` : ''}
          ${p.cycle ? `<p><strong>Cycle:</strong> ${p.cycle}</p>` : ''}
          ${p.measurements ? `<p><strong>Measurements:</strong> ${p.measurements}</p>` : ''}
        </div>
      `);

      marker.on('mouseover', () => marker.setStyle({ radius: 9, fillOpacity: 1 }));
      marker.on('mouseout', () => marker.setStyle({ radius: 6, fillOpacity: 0.85 }));
      marker.addTo(markersLayerRef.current);
      created.push(marker);
    });

    if (created.length > 0) {
      const group = L.featureGroup(created);
      const bounds = group.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds.pad(0.2));
      }
    }
  };

  // -------------------------------------------------------
  // 4. Update markers when floatData loads
  // -------------------------------------------------------
  useEffect(() => {
    if (!loading && floatData.length > 0) {
      renderMarkers(floatData);
    }
  }, [loading, floatData]);

  // -------------------------------------------------------
  // 5. Apply incoming external data
  // -------------------------------------------------------
  useEffect(() => {
    if (!data || !Array.isArray(data) || data.length === 0) return;
    renderMarkers(data);
  }, [data]);

  // -------------------------------------------------------
  // UI
  // -------------------------------------------------------
  return (
    <div className={`map-component ${fullPage ? "full-page" : ""}`}>
      <div className="map-container">
        {loading && (
          <div className="map-loading">
            <i className="fas fa-spinner fa-spin"></i>
            <p>Loading map...</p>
          </div>
        )}

        <div
          ref={mapContainerRef}
          className="map-display"
          style={{ width: "100%", height: "100%" }}
        />
      </div>

      <div className="map-info">
        <div className="data-summary">
          <span>
            <i className="fas fa-map-marker-alt"></i>{" "}
            {floatData.length} Active Floats
          </span>
          <span>
            <i className="fas fa-calendar"></i> January 2025 Data
          </span>
          <span>
            <i className="fas fa-globe"></i> Indian Ocean Region
          </span>
        </div>
      </div>
    </div>
  );
};

export default MapComponent;
