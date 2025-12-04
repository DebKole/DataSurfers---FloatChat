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
  // 1. Fetch float data from backend
  // -------------------------------------------------------
  useEffect(() => {
    const fetchFloatData = async () => {
      try {
        const res = await fetch(
          "http://localhost:8000/floats/indian-ocean?limit=50"
        );
        const json = await res.json();

        if (json.status === 200 && Array.isArray(json.floats)) {
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
        } else {
          setFloatData([]);
        }
      } catch (err) {
        console.error("Error fetching float data:", err);
        setFloatData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchFloatData();
  }, []);

  // -------------------------------------------------------
  // 2. Initialize Leaflet map ONCE
  // -------------------------------------------------------
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [10, 70], // Indian Ocean-ish
      zoom: 3,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "OpenStreetMap contributors",
    }).addTo(map);

    mapRef.current = map;
    markersLayerRef.current = L.layerGroup().addTo(map);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      markersLayerRef.current = null;
    };
  }, []);

  // -------------------------------------------------------
  // 3. Helper: render markers on the map
  // -------------------------------------------------------
  const renderMarkers = (points) => {
    const map = mapRef.current;
    const layer = markersLayerRef.current;
    if (!map || !layer) return;

    layer.clearLayers();
    const created = [];

    (points || []).forEach((point) => {
      const lat = Number(point.lat ?? point.latitude);
      const lng = Number(point.lng ?? point.longitude);
      if (Number.isNaN(lat) || Number.isNaN(lng)) return;

      const color = "#1e90ff";

      const marker = L.circleMarker([lat, lng], {
        radius: 6,
        color,
        weight: 2,
        fillColor: color,
        fillOpacity: 0.85,
      });

      const id =
        point.id || point.float_id || point.profile_id || "Unknown Float";
      const dateStr = point.datetime
        ? new Date(point.datetime).toLocaleString()
        : "";

      marker.bindTooltip(`Float ${id}`, { direction: "top", offset: [0, -6] });

      marker.bindPopup(`
        <div class="map-popup">
          <h4>Float ${id}</h4>
          <p><strong>Location:</strong> ${lat.toFixed(2)}°, ${lng.toFixed(
        2
      )}°</p>
          ${dateStr ? `<p><strong>Date:</strong> ${dateStr}</p>` : ""}
          ${
            point.cycle
              ? `<p><strong>Cycle:</strong> ${point.cycle}</p>`
              : ""
          }
          ${
            point.measurements
              ? `<p><strong>Measurements:</strong> ${point.measurements}</p>`
              : ""
          }
        </div>
      `);

      marker.on("mouseover", () =>
        marker.setStyle({ radius: 9, fillOpacity: 1 })
      );
      marker.on("mouseout", () =>
        marker.setStyle({ radius: 6, fillOpacity: 0.85 })
      );

      marker.addTo(layer);
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
  // 4. Update markers when data changes
  //    - If `data` prop is provided, use that
  //    - Otherwise use fetched floatData
  // -------------------------------------------------------
  useEffect(() => {
    const points =
      Array.isArray(data) && data.length > 0 ? data : floatData;
    if (points && points.length > 0) {
      renderMarkers(points);
    }
  }, [data, floatData]); // eslint-disable-line react-hooks/exhaustive-deps

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
