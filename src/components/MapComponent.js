import React, { useState, useEffect, useRef } from 'react';
import './MapComponent.css';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
const MapComponent = () => {
  const [isLoading, setIsLoading] = useState(true);
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  const [floatData, setFloatData] = useState([]);
  const [dataLoaded, setDataLoaded] = useState(false);

  // Fetch real float data from database
  useEffect(() => {
    const fetchFloatData = async () => {
      try {
        // Fetch Indian Ocean floats from your January 2025 database
        const response = await fetch('http://localhost:8000/floats/indian-ocean?limit=50');
        const data = await response.json();
        
        if (data.status === 200 && data.floats) {
          // Transform database format to map format
          const transformedData = data.floats.map(float => ({
            id: float.float_id,
            lat: parseFloat(float.latitude),
            lng: parseFloat(float.longitude),
            datetime: float.datetime,
            cycle: float.cycle_number,
            measurements: float.measurement_count,
            profile_id: float.global_profile_id
          }));
          setFloatData(transformedData);
          setDataLoaded(true);
        }
      } catch (error) {
        console.error('Error fetching float data:', error);
        // Fallback to empty array if fetch fails
        setFloatData([]);
        setDataLoaded(true);
      }
    };

    fetchFloatData();
  }, []);

  // No separate initializeMap function to keep hooks simple and avoid lint warnings.

  const initializeLeafletMap = async () => {
    try {
      // Using static CSS import and static L from top-level import.

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

      // Determine map center based on data
      const mapCenter = floatData.length > 0 
        ? [floatData[0].lat, floatData[0].lng]  // Center on first float
        : [10, 70];  // Default to Indian Ocean center
      
      const mapZoom = floatData.length > 0 ? 4 : 3;

      // Create Leaflet map with explicit dragging and zoom behaviors enabled
      const map = L.map(mapContainerRef.current, {
        center: mapCenter,
        zoom: mapZoom,
        zoomControl: true,
        dragging: true,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        boxZoom: true,
        tap: false // improves interaction on touch devices
      });

      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(map);

      // Add data points as styled dots (circle markers) - use real float data
      const dataToDisplay = floatData.length > 0 ? floatData : [];
      const markers = dataToDisplay.map(point => {
        const color = '#1e90ff';
        const dot = L.circleMarker([point.lat, point.lng], {
          radius: 6,
          color,
          weight: 2,
          fillColor: color,
          fillOpacity: 0.85
        }).addTo(map);

        dot.bindTooltip(`Float ${point.id}`, { direction: 'top', offset: [0, -6] });
        
        // Format datetime
        const dateStr = point.datetime ? new Date(point.datetime).toLocaleDateString() : 'N/A';
        
        dot.bindPopup(`
          <div class="map-popup">
            <h4>Float ${point.id}</h4>
            <p><strong>Location:</strong> ${point.lat.toFixed(2)}°, ${point.lng.toFixed(2)}°</p>
            <p><strong>Date:</strong> ${dateStr}</p>
            <p><strong>Cycle:</strong> ${point.cycle || 'N/A'}</p>
            <p><strong>Measurements:</strong> ${point.measurements || 0}</p>
            <p style="font-size: 0.85em; color: #666; margin-top: 8px;">
              <em>January 2025 Data</em>
            </p>
          </div>
        `);

        // Hover highlight
        dot.on('mouseover', () => dot.setStyle({ radius: 9, fillOpacity: 1 }));
        dot.on('mouseout', () => dot.setStyle({ radius: 6, fillOpacity: 0.85 }));
        return dot;
      });

      // Fit map to markers (with small padding), ignore if bounds invalid
      try {
        const group = L.featureGroup(markers);
        const bounds = group.getBounds();
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.2));
      } catch (_) {}

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

  // Removed Plotly and Cesium implementations to keep a single, lightweight Leaflet map.

  const initializeFallbackMap = () => {
    // Fallback static map representation
    const dataToDisplay = floatData.length > 0 ? floatData : [];
    mapContainerRef.current.innerHTML = `
      <div class="fallback-map">
        <div class="map-header">
          <i class="fas fa-globe"></i>
          <h3>Ocean Data Visualization</h3>
        </div>
        <div class="data-points">
          ${dataToDisplay.length > 0 ? dataToDisplay.map(point => `
            <div class="data-point">
              <div class="point-marker" style="background-color: #1e90ff"></div>
              <div class="point-info">
                <strong>Float ${point.id}</strong><br>
                Lat: ${point.lat.toFixed(2)}°, Lng: ${point.lng.toFixed(2)}°<br>
                Measurements: ${point.measurements || 0}
              </div>
            </div>
          `).join('') : '<p>Loading float data...</p>'}
        </div>
        <div class="map-note">
          <i class="fas fa-info-circle"></i>
          ${dataToDisplay.length} floats from January 2025 data
        </div>
      </div>
    `;
  };

  // Initialize Leaflet once data is loaded
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!dataLoaded) return;  // Wait for data to load first
    
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

    return () => {
      // Cleanup on unmount
      if (mapInstanceRef.current) {
        if (mapInstanceRef.current.cleanup) {
          mapInstanceRef.current.cleanup();
        } else if (mapInstanceRef.current.remove) {
          mapInstanceRef.current.remove();
        } else if (mapInstanceRef.current.destroy) {
          mapInstanceRef.current.destroy();
        }
        mapInstanceRef.current = null;
      }
    };
  }, [dataLoaded, floatData]);

  return (
    <div className="map-component">
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
          <span><i className="fas fa-map-marker-alt"></i> {floatData.length} Active Floats</span>
          <span><i className="fas fa-calendar"></i> January 2025 Data</span>
          <span><i className="fas fa-globe"></i> Indian Ocean Region</span>
        </div>
      </div>
    </div>
  );
};

export default MapComponent;
