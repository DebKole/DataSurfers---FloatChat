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

      // Create Leaflet map with explicit dragging and zoom behaviors enabled
      const map = L.map(mapContainerRef.current, {
        center: mapCenter,
        zoom: mapZoom,
        zoomControl: true,
        dragging: true,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        boxZoom: true,
        tap: false, // improves interaction on touch devices
        fadeAnimation: false, // Disable fade to prevent timing issues
        zoomAnimation: false // Disable zoom animation initially
      });

      // Wait for map to fully initialize - ensure panes are created
      // This prevents the _leaflet_pos error
      await new Promise(resolve => {
        // Use a simple delay to ensure map panes are initialized
        setTimeout(() => {
          try {
            // Verify map panes exist before proceeding
            if (map && map._panes && map._panes.mapPane) {
              resolve();
            } else {
              // If panes aren't ready, wait a bit more
              setTimeout(resolve, 100);
            }
          } catch (e) {
            // If there's an error, proceed anyway after delay
            setTimeout(resolve, 100);
          }
        }, 100);
      });

    points.forEach((p) => {
      if (isNaN(p.lat) || isNaN(p.lng)) return;

      // Layer for markers and a unified renderer that supports both incoming data and real float data
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
          const id = point.id || point.float_id || point.profile_id || '—';
          const dateStr = point.datetime ? new Date(point.datetime).toLocaleDateString() : '';
          dot.bindTooltip(`Float ${id}`, { direction: 'top', offset: [0, -6] });
          dot.bindPopup(`
            <div class="map-popup">
              <h4>Float ${id}</h4>
              <p><strong>Location:</strong> ${Number(point.lat).toFixed(2)}°, ${Number(point.lng).toFixed(2)}°</p>
              ${dateStr ? `<p><strong>Date:</strong> ${dateStr}</p>` : ''}
              ${point.cycle ? `<p><strong>Cycle:</strong> ${point.cycle}</p>` : ''}
              ${point.measurements ? `<p><strong>Measurements:</strong> ${point.measurements}</p>` : ''}
            </div>
          `);
          dot.on('mouseover', () => dot.setStyle({ radius: 9, fillOpacity: 1 }));
          dot.on('mouseout', () => dot.setStyle({ radius: 6, fillOpacity: 0.85 }));
          dot.addTo(markersLayerRef.current);
          created.push(dot);
        });
        try {
          if (created.length > 0 && map && map._loaded) {
            const group = L.featureGroup(created);
            const bounds = group.getBounds();
            if (bounds.isValid()) {
              // Use setTimeout to ensure map is ready for fitBounds
              setTimeout(() => {
                try {
                  if (map && map._loaded) {
                    map.fitBounds(bounds.pad(0.2));
                  }
                } catch (e) {
                  // Silently ignore fitBounds errors
                }
              }, 150);
            }
          }
        } catch (_) {}
      };

      marker.bindTooltip(`Float ${p.id}`);

      // Invalidate size after a tick and on container resize to avoid layout issues
      // Use a safer approach that checks if map is still valid
      setTimeout(() => {
        try {
          if (map && mapContainerRef.current && map._loaded) {
            map.invalidateSize(false);
          }
        } catch (e) {
          // Silently ignore - map may not be fully ready
        }
      }, 100);
      
      const resizeObs = new ResizeObserver(() => {
        try {
          if (map && mapContainerRef.current && map._loaded) {
            // Use requestAnimationFrame to ensure DOM is stable
            requestAnimationFrame(() => {
              try {
                if (map && map._loaded) {
                  map.invalidateSize(false);
                }
              } catch (e) {
                // Ignore resize errors
              }
            });
          }
        } catch (e) {
          // Ignore resize observer errors
        }
      });
      
      if (mapContainerRef.current) {
        resizeObs.observe(mapContainerRef.current);
      }

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
    if (!dataLoaded) return;  // Wait for data to load first
    
    // Use requestAnimationFrame to ensure DOM is fully ready
    const initTimeout = setTimeout(() => {
      (async () => {
        if (!mapContainerRef.current) return;
        
        // Double-check container is in DOM and has size
        if (!document.body.contains(mapContainerRef.current)) {
          return;
        }
        
        // Wait for next frame to ensure all DOM updates are complete
        requestAnimationFrame(() => {
          requestAnimationFrame(async () => {
            try {
              await initializeLeafletMap();
              setIsLoading(false);
            } catch (error) {
              // Silently handle the _leaflet_pos error - it's a timing issue
              const errorMsg = error?.message || String(error);
              if (errorMsg.includes('_leaflet_pos') || errorMsg.includes('undefined')) {
                // Retry once after a short delay
                setTimeout(async () => {
                  try {
                    if (mapContainerRef.current && !mapInstanceRef.current) {
                      await initializeLeafletMap();
                      setIsLoading(false);
                    }
                  } catch (retryError) {
                    console.warn('Map initialization retry failed, using fallback');
                    initializeFallbackMap();
                    setIsLoading(false);
                  }
                }, 100);
              } else {
                console.error('Error initializing map:', error);
                initializeFallbackMap();
                setIsLoading(false);
              }
            }
          });
        });
      })();
    }, 50); // Small delay to ensure component is fully mounted
    
    return () => {
      clearTimeout(initTimeout);
      // Cleanup on unmount
      if (mapInstanceRef.current) {
        if (mapInstanceRef.current.cleanup) {
          try {
            mapInstanceRef.current.cleanup();
          } catch (e) {
            // Ignore cleanup errors
          }
        } else if (mapInstanceRef.current.map) {
          try {
            mapInstanceRef.current.map.remove();
          } catch (e) {
            // Ignore cleanup errors
          }
        }
        mapInstanceRef.current = null;
      }
    };
  }, [dataLoaded, floatData]);

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
