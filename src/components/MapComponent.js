import React, { useState, useEffect, useRef } from 'react';
import './MapComponent.css';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

const MapComponent = ({ fullPage = false, data = null }) => { 
  const [isLoading, setIsLoading] = useState(true);
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);

  // Sample oceanographic data points
  const sampleData = [
    { id: '4902916', lat: 45.2, lng: -30.1, temp: 22.4, salinity: 35.1, depth: 150 },
    { id: '4902917', lat: 42.8, lng: -28.5, temp: 21.8, salinity: 35.3, depth: 200 },
    { id: '4902918', lat: 47.1, lng: -32.7, temp: 23.1, salinity: 34.9, depth: 120 },
    { id: '4902919', lat: 44.5, lng: -29.3, temp: 20.2, salinity: 35.5, depth: 300 },
    { id: '4902920', lat: 46.7, lng: -31.2, temp: 22.8, salinity: 35.0, depth: 180 },
  ];

  const initializeLeafletMap = async () => {
    try {

      // Wait until container has a measurable size (avoid offsetWidth null/0)
      const waitForSize = () => new Promise((resolve) => {
        const el = mapContainerRef.current;
        if (!el) return resolve();
        const hasSize = () => el.offsetWidth > 0 && el.offsetHeight > 0 && document.body.contains(el);
        if (hasSize()) return resolve();

        const RO = window.ResizeObserver;
        if (typeof RO === 'function') {
          const observer = new RO(() => {
            if (hasSize()) {
              try { observer.disconnect(); } catch (_) {}
              resolve();
            }
          });
          try { observer.observe(el); } catch (_) { resolve(); }
          // Fallback timeout
          setTimeout(() => {
            try { observer.disconnect(); } catch (_) {}
            resolve();
          }, 800);
        } else {
          // Fallback polling if ResizeObserver is unavailable
          let attempts = 0;
          const iv = setInterval(() => {
            attempts += 1;
            if (hasSize() || attempts > 20) {
              clearInterval(iv);
              resolve();
            }
          }, 50);
        }
      });
      await waitForSize();

      // If a map already exists (React StrictMode or remount), remove it cleanly
      if (mapInstanceRef.current && mapInstanceRef.current.map) {
        try { mapInstanceRef.current.map.remove(); } catch (_) {}
        mapInstanceRef.current = null;
      }
      // Leaflet stores an internal id on the container; ensure it's cleared
      if (mapContainerRef.current && mapContainerRef.current._leaflet_id) {
        try { delete mapContainerRef.current._leaflet_id; } catch (_) {}
      }
      // Clear container children
      mapContainerRef.current.innerHTML = '';

      // Create Leaflet map with explicit dragging and zoom behaviors enabled
      const map = L.map(mapContainerRef.current, {
        center: [45.0, -30.0],
        zoom: 6,
        zoomControl: true,
        dragging: true,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        boxZoom: true,
        tap: false // improves interaction on touch devices
      });

      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: ' OpenStreetMap contributors'
      }).addTo(map);

      markersLayerRef.current = L.layerGroup().addTo(map);

      const renderMarkers = (points) => {
        if (!markersLayerRef.current) return;
        markersLayerRef.current.clearLayers();
        const created = [];
        (points || []).forEach(point => {
          if (typeof point.lat !== 'number' || typeof point.lng !== 'number') return;
          const color = '#1e90ff';
          const dot = L.circleMarker([point.lat, point.lng], {
            radius: 6,
            color,
            weight: 2,
            fillColor: color,
            fillOpacity: 0.85
          });
          dot.bindTooltip(`Float ${point.id}`, { direction: 'top', offset: [0, -6] });
          dot.bindPopup(`
            <div class="map-popup">
              <h4>Float ${point.id}</h4>
              <p><strong>Temperature:</strong> ${point.temp}°C</p>
              <p><strong>Salinity:</strong> ${point.salinity} PSU</p>
              <p><strong>Depth:</strong> ${point.depth}m</p>
            </div>
          `);
          dot.on('mouseover', () => dot.setStyle({ radius: 9, fillOpacity: 1 }));
          dot.on('mouseout', () => dot.setStyle({ radius: 6, fillOpacity: 0.85 }));
          dot.addTo(markersLayerRef.current);
          created.push(dot);
        });
        try {
          if (created.length > 0) {
            const group = L.featureGroup(created);
            const bounds = group.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds.pad(0.2));
          }
        } catch (_) {}
      };

      const initialPoints = Array.isArray(data) && data.length ? data : sampleData;
      renderMarkers(initialPoints);

      // Invalidate size after a tick and on container resize to avoid layout issues
      setTimeout(() => {
        try { map.invalidateSize(false); } catch (_) {}
      }, 0);
      const resizeObs = new ResizeObserver(() => {
        try { map.invalidateSize(false); } catch (_) {}
      });
      resizeObs.observe(mapContainerRef.current);

      // Save for cleanup
      mapInstanceRef.current = {
        map,
        renderMarkers,
        cleanup: () => {
          try { resizeObs.disconnect(); } catch (_) {}
          try { map.remove(); } catch (_) {}
        }
      };

    } catch (error) {
      // Gracefully ignore benign duplicate init errors in dev StrictMode
      const msg = (error && (error.message || String(error))) || '';
      if (msg.toLowerCase().includes('already initialized')) {
        console.warn('Leaflet map container was already initialized; skipping re-init.');
        return;
      }
      console.error('Leaflet not available or failed to initialize:', error);
      initializeFallbackMap();
    }
  };

  const initializeFallbackMap = () => {
    // Fallback static map representation
    mapContainerRef.current.innerHTML = `
      <div class="fallback-map">
        <div class="map-header">
          <i class="fas fa-globe"></i>
          <h3>Ocean Data Visualization</h3>
        </div>
        <div class="data-points">
          ${sampleData.map(point => `
            <div class="data-point">
              <div class="point-marker" style="background-color: hsl(${200 + point.temp * 2}, 70%, 50%)"></div>
              <div class="point-info">
                <strong>Float ${point.id}</strong><br>
                Lat: ${point.lat}°, Lng: ${point.lng}°<br>
                Temp: ${point.temp}°C, Salinity: ${point.salinity}
              </div>
            </div>
          `).join('')}
        </div>
        <div class="map-note">
          <i class="fas fa-info-circle"></i>
          Install map libraries for interactive visualization
        </div>
      </div>
    `;
  };

  // Initialize Leaflet once on mount
  useEffect(() => {
    (async () => {
      if (!mapContainerRef.current) return;
      try {
        await initializeLeafletMap();
        setIsLoading(false);
      } catch (error) {
        console.error('Error initializing map:', error);
        initializeFallbackMap();
        setIsLoading(false);
      }
    })();
  }, []);

  // Update markers whenever incoming data changes
  useEffect(() => {
    const points = Array.isArray(data) && data.length ? data : sampleData;
    if (mapInstanceRef.current && mapInstanceRef.current.renderMarkers) {
      try { mapInstanceRef.current.renderMarkers(points); } catch (_) {}
    }
  }, [data]);

  // Compute summary values from current points
  const currentPoints = Array.isArray(data) && data.length ? data : sampleData;

  return (
    <div className={`map-component ${fullPage ? 'full-page' : ''}`}> {/* Add conditional class */}
      <div className="map-container">
        {isLoading && (
          <div className="map-loading">
            <i className="fas fa-spinner fa-spin"></i>
            <p>Loading map...</p>
          </div>
        )}
        <div 
          ref={mapContainerRef} 
          className="map-display"
          style={{ width: '100%' }}
        />
      </div>
      
      <div className="map-info">
        <div className="data-summary">
          <span><i className="fas fa-map-marker-alt"></i> {currentPoints.length} Active Floats</span>
          <span><i className="fas fa-thermometer-half"></i> Avg Temp: {(currentPoints.reduce((sum, d) => sum + (d.temp || 0), 0) / Math.max(currentPoints.length, 1)).toFixed(1)}°C</span>
        </div>
      </div>
    </div>
  );
};

export default MapComponent;