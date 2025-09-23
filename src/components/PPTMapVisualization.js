  import React, { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import './PPTMapVisualization.css';

const PPTMapVisualization = ({ isVisible, onClose }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);


  const [currentLayer, setCurrentLayer] = useState('floats');
  const [selectedParameter, setSelectedParameter] = useState('temperature');
  const [demoData, setDemoData] = useState(null);
  const layerGroupsRef = useRef({});

  // Load demo data
  const loadDemoData = useCallback(async () => {
    try {
      const response = await fetch('/ppt_demo_map_data.json');
      const data = await response.json();
      setDemoData(data);
    } catch (error) {
      console.error('Failed to load demo data:', error);
      // Fallback to minimal demo data
      setDemoData({
        floatMarkers: [
          { lat: 45, lng: -30, temperature: 15, salinity: 35, depth: 0, floatId: '4900000', region: 'north_atlantic' },
          { lat: 35, lng: -150, temperature: 20, salinity: 34, depth: 10, floatId: '4900001', region: 'north_pacific' },
          { lat: -15, lng: 75, temperature: 28, salinity: 36, depth: 0, floatId: '4900002', region: 'indian_ocean' }
        ],
        pollutionMarkers: [
          { lat: 31.2, lng: 121.5, level: 'high', severity: 8.5 },
          { lat: 34.0, lng: -118.2, level: 'medium', severity: 6.2 }
        ],
        organismMarkers: [
          { lat: 36.0, lng: -140.0, biomass: 'high', depth: '200-800m' },
          { lat: -10.0, lng: 65.0, biomass: 'medium', depth: '300-600m' }
        ]
      });
    }
  }, []);

  // Initialize map
  const initializeMap = useCallback(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    mapInstanceRef.current = L.map(mapRef.current, {
      center: [20, 0],
      zoom: 2,
      zoomControl: true,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      boxZoom: true,
      keyboard: true,
      dragging: true,
      touchZoom: true
    });

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri',
      maxZoom: 13
    }).addTo(mapInstanceRef.current);

    layerGroupsRef.current = {
      floats: L.layerGroup(),
      pollution: L.layerGroup(),
      organisms: L.layerGroup(),
      heatmap: L.layerGroup()
    };
  }, []);

  // Add float markers
  const addFloatMarkers = useCallback(() => {
    if (!demoData?.floatMarkers) return;

    const floatLayer = layerGroupsRef.current.floats;

    demoData.floatMarkers.forEach(float => {
      const value = selectedParameter === 'temperature' ? float.temperature : float.salinity;
      const color = getParameterColor(value, selectedParameter);
      const size = getMarkerSize(value, selectedParameter);

      const marker = L.circleMarker([float.lat, float.lng], {
        radius: size,
        fillColor: color,
        color: '#ffffff',
        weight: 1,
        opacity: 0.8,
        fillOpacity: 0.7
      });

      const popupContent = `
        <div class="float-popup">
          <h4>🌊 Argo Float ${float.floatId}</h4>
          <div class="popup-data">
            <div class="data-row">
              <span class="label">Temperature:</span>
              <span class="value">${float.temperature}°C</span>
            </div>
            <div class="data-row">
              <span class="label">Salinity:</span>
              <span class="value">${float.salinity} PSU</span>
            </div>
            <div class="data-row">
              <span class="label">Depth:</span>
              <span class="value">${float.depth}m</span>
            </div>
            <div class="data-row">
              <span class="label">Region:</span>
              <span class="value">${float.region.replace('_', ' ')}</span>
            </div>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);
      floatLayer.addLayer(marker);
    });

    mapInstanceRef.current.addLayer(floatLayer);
  }, [demoData, selectedParameter]);

  // Add pollution markers
  const addPollutionMarkers = useCallback(() => {
    if (!demoData?.pollutionMarkers) return;

    const pollutionLayer = layerGroupsRef.current.pollution;

    demoData.pollutionMarkers.forEach(pollution => {
      const color = getPollutionColor(pollution.level);
      const size = getPollutionSize(pollution.severity);

      const marker = L.circleMarker([pollution.lat, pollution.lng], {
        radius: size,
        fillColor: color,
        color: '#ff0000',
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.6
      });

      const popupContent = `
        <div class="pollution-popup">
          <h4>🏭 Pollution Detection</h4>
          <div class="popup-data">
            <div class="data-row">
              <span class="label">Level:</span>
              <span class="value pollution-${pollution.level}">${pollution.level.toUpperCase()}</span>
            </div>
            <div class="data-row">
              <span class="label">Severity:</span>
              <span class="value">${pollution.severity}/10</span>
            </div>
            <div class="data-row">
              <span class="label">Status:</span>
              <span class="value">⚠️ Monitoring</span>
            </div>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);
      pollutionLayer.addLayer(marker);
    });

    mapInstanceRef.current.addLayer(pollutionLayer);
  }, [demoData]);

  // Add organism markers
  const addOrganismMarkers = useCallback(() => {
    if (!demoData?.organismMarkers) return;

    const organismLayer = layerGroupsRef.current.organisms;

    demoData.organismMarkers.forEach(organism => {
      const color = getOrganismColor(organism.biomass);
      const size = getOrganismSize(organism.biomass);

      const marker = L.circleMarker([organism.lat, organism.lng], {
        radius: size,
        fillColor: color,
        color: '#00ff00',
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.5
      });

      const popupContent = `
        <div class="organism-popup">
          <h4>🐟 Mesopelagic Life</h4>
          <div class="popup-data">
            <div class="data-row">
              <span class="label">Depth Range:</span>
              <span class="value">${organism.depth}</span>
            </div>
            <div class="data-row">
              <span class="label">Biomass:</span>
              <span class="value biomass-${organism.biomass}">${organism.biomass.replace('_', ' ').toUpperCase()}</span>
            </div>
            <div class="data-row">
              <span class="label">Status:</span>
              <span class="value">🔍 Detected</span>
            </div>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);
      organismLayer.addLayer(marker);
    });

    mapInstanceRef.current.addLayer(organismLayer);
  }, [demoData]);

  // Update map layers
  const updateMapLayers = useCallback(() => {
    if (!mapInstanceRef.current || !demoData) return;

    // Clear existing layers
    Object.values(layerGroupsRef.current).forEach(layer => {
      mapInstanceRef.current.removeLayer(layer);
      layer.clearLayers();
    });

    // Add selected layer
    switch (currentLayer) {
      case 'floats':
        addFloatMarkers();
        break;
      case 'pollution':
        addPollutionMarkers();
        break;
      case 'organisms':
        addOrganismMarkers();
        break;
      case 'combined':
        addFloatMarkers();
        addPollutionMarkers();
        addOrganismMarkers();
        break;
      default:
        addFloatMarkers();
    }
  }, [currentLayer, addFloatMarkers, addPollutionMarkers, addOrganismMarkers, demoData]);

  // Initialize when visible
  useEffect(() => {
    if (isVisible) {
      loadDemoData();
      initializeMap();
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [isVisible, loadDemoData, initializeMap]);

  // Update layers when dependencies change
  useEffect(() => {
    if (mapInstanceRef.current && isVisible && demoData) {
      updateMapLayers();
    }
  }, [updateMapLayers, isVisible, demoData]);

  // Helper functions
  const getParameterColor = (value, parameter) => {
    if (parameter === 'temperature') {
      if (value < 0) return '#0066cc';
      if (value < 10) return '#0099ff';
      if (value < 20) return '#66ccff';
      if (value < 25) return '#ffcc00';
      return '#ff6600';
    } else { // salinity
      if (value < 34) return '#0066cc';
      if (value < 35) return '#0099ff';
      if (value < 36) return '#66ccff';
      if (value < 37) return '#ffcc00';
      return '#ff6600';
    }
  };

  const getMarkerSize = (value, parameter) => {
    return parameter === 'temperature' ?
      Math.max(4, Math.min(12, value / 2 + 4)) :
      Math.max(4, Math.min(12, (value - 30) * 2 + 6));
  };

  const getPollutionColor = (level) => {
    switch (level) {
      case 'high': return '#ff0000';
      case 'medium': return '#ff6600';
      case 'low': return '#ffcc00';
      default: return '#ff0000';
    }
  };

  const getPollutionSize = (severity) => {
    if (value < 36) return '#66ccff';
    if (value < 37) return '#ffcc00';
    return '#ff6600';
  }
};

const getMarkerSize = (value, parameter) => {
  return parameter === 'temperature' ?
    Math.max(4, Math.min(12, value / 2 + 4)) :
    Math.max(4, Math.min(12, (value - 30) * 2 + 6));
};

const getPollutionColor = (level) => {
  switch (level) {
    case 'high': return '#ff0000';
    case 'medium': return '#ff6600';
    case 'low': return '#ffcc00';
    default: return '#ff0000';
  }
};

const getPollutionSize = (severity) => {
  return Math.max(8, Math.min(16, severity * 1.5));
};

const getOrganismColor = (biomass) => {
  switch (biomass) {
    case 'very_high': return '#00ff00';
    case 'high': return '#66ff66';
    case 'medium': return '#99ff99';
    case 'low': return '#ccffcc';
    default: return '#66ff66';
  }
};

const getOrganismSize = (biomass) => {
  switch (biomass) {
    case 'very_high': return 14;
    case 'high': return 12;
    case 'medium': return 10;
    case 'low': return 8;
    default: return 10;
  }
};

const handleKeyPress = (e) => {
  if (e.key === 'Escape') {
    onClose();
  }
};


return (
  <div className="ppt-map-overlay" onKeyDown={handleKeyPress} tabIndex={0}>
    <div className="ppt-map-container">
      <div className="ppt-map-header">
        <div className="ppt-map-title">
          <h2>🌊 FloatChat Global Ocean Network</h2>
          <p>Real-time oceanographic data visualization</p>
        </div>
        <button className="ppt-map-close" onClick={onClose}>×</button>
      </div>

      <div className="ppt-map-controls">
        <div className="layer-controls">
          <label>Data Layer:</label>
          <select value={currentLayer} onChange={(e) => setCurrentLayer(e.target.value)}>
            <option value="floats">🌊 Argo Floats</option>
            <option value="pollution">🏭 Pollution Detection</option>
            <option value="organisms">🐟 Organism Detection</option>
            <option value="combined">🔍 All Layers</option>
          </select>
        </div>

        {currentLayer === 'floats' && (
          <div className="parameter-controls">
            <label>Parameter:</label>
            <select value={selectedParameter} onChange={(e) => setSelectedParameter(e.target.value)}>
              <option value="temperature">🌡️ Temperature</option>
              <option value="salinity">🧂 Salinity</option>
            </select>
          </div>
        )}
      </div>

      <div className="ppt-map-content">
        <div ref={mapRef} className="ppt-leaflet-map"></div>

        <div className="ppt-map-legend">
          {currentLayer === 'floats' && (
            <div className="legend-section">
              <h4>{selectedParameter === 'temperature' ? '🌡️ Temperature (°C)' : '🧂 Salinity (PSU)'}</h4>
              <div className="legend-items">
                {selectedParameter === 'temperature' ? (
                  <>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#0066cc' }}></span> &lt; 0°C</div>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#0099ff' }}></span> 0-10°C</div>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#66ccff' }}></span> 10-20°C</div>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ffcc00' }}></span> 20-25°C</div>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ff6600' }}></span> &gt; 25°C</div>
                  </>
                ) : (
                  <>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#0066cc' }}></span> &lt; 34 PSU</div>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#0099ff' }}></span> 34-35 PSU</div>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#66ccff' }}></span> 35-36 PSU</div>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ffcc00' }}></span> 36-37 PSU</div>
                    <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ff6600' }}></span> &gt; 37 PSU</div>
                  </>
                )}
              </div>
            </div>
          )}

          {(currentLayer === 'pollution' || currentLayer === 'combined') && (
            <div className="legend-section">
              <h4>🏭 Pollution Levels</h4>
              <div className="legend-items">
                <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ff0000' }}></span> High Risk</div>
                <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ff6600' }}></span> Medium Risk</div>
                <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ffcc00' }}></span> Low Risk</div>
              </div>
            </div>
          )}

          {(currentLayer === 'organisms' || currentLayer === 'combined') && (
            <div className="legend-section">
              <h4>🐟 Organism Biomass</h4>
              <div className="legend-items">
                <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#00ff00' }}></span> Very High</div>
                <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#66ff66' }}></span> High</div>
                <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#99ff99' }}></span> Medium</div>
                <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ccffcc' }}></span> Low</div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="ppt-map-stats">
        <div className="stat-item">
          <span className="stat-number">{demoData?.floatMarkers?.length || 0}</span>
          <span className="stat-label">Active Floats</span>
        </div>
        <div className="stat-item">
          <span className="stat-number">{demoData?.pollutionMarkers?.length || 0}</span>
          <span className="stat-label">Pollution Sites</span>
        </div>
        <div className="stat-item">
          <span className="stat-number">{demoData?.organismMarkers?.length || 0}</span>
          <span className="stat-label">Organism Zones</span>
        </div>
        <div className="stat-item">
          <span className="stat-number">8</span>
          <span className="stat-label">Ocean Regions</span>
        </div>
      </div>
    </div>
  </div>
);
export default PPTMapVisualization;