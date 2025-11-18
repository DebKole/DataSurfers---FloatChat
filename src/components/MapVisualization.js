import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import './MapVisualization.css';

// Fix for default markers in Leaflet with React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const MapVisualization = ({
    mapData = null,
    isVisible = false,
    onClose = () => { },
    parameter = 'temperature'
}) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const heatmapLayerRef = useRef(null);
    const markersLayerRef = useRef(null);
    const [isLoading, setIsLoading] = useState(false);
    const [currentParameter, setCurrentParameter] = useState(parameter);
    const [realFloatData, setRealFloatData] = useState([]);
    const [dataLoaded, setDataLoaded] = useState(false);

    // ⚙️ CONFIGURATION - Controllable radius and center point
    // Changes trigger automatic re-fetch!
    const [centerLat, setCenterLat] = useState(15.0);    // Indian coast center latitude
    const [centerLon, setCenterLon] = useState(77.5);    // Indian coast center longitude  
    const [radiusKm, setRadiusKm] = useState(500);       // Radius in kilometers
    const [maxFloats] = useState(500);                    // Maximum floats to fetch

    // Fetch real float data from database
    useEffect(() => {
        const fetchRealFloatData = async () => {
            try {
                console.log('🌊 Fetching float data from API...');
                console.log(`📍 Center: (${centerLat}, ${centerLon}), Radius: ${radiusKm}km`);

                // Use radius endpoint to get floats near Indian coast
                const response = await fetch(
                    `http://localhost:8000/floats/radius?lat=${centerLat}&lon=${centerLon}&radius=${radiusKm}&limit=${maxFloats}`
                );
                const data = await response.json();

                console.log('📊 API Response:', data);

                if (data.status === 200 && data.floats) {
                    // Transform to map format with mock temperature/salinity
                    const transformedData = data.floats.map(float => ({
                        lat: parseFloat(float.latitude),
                        lng: parseFloat(float.longitude),
                        value: Math.random() * 5 + 20, // Mock temperature 20-25°C for Indian Ocean
                        depth: 0,
                        profile: float.float_id,
                        float_id: float.float_id,
                        datetime: float.datetime,
                        measurements: float.measurement_count,
                        distance_km: float.distance_km  // Distance from center
                    }));
                    console.log(`✅ Found ${transformedData.length} floats within ${radiusKm}km of Indian coast`);
                    if (transformedData.length > 0) {
                        console.log('Sample float:', transformedData[0]);
                    }
                    setRealFloatData(transformedData);
                }
                setDataLoaded(true);
            } catch (error) {
                console.error('❌ Error fetching float data:', error);
                setDataLoaded(true);
            }
        };

        fetchRealFloatData();
    }, [centerLat, centerLon, radiusKm, maxFloats]); // Re-fetch when any of these change

    // Sample oceanographic data for demonstration (fallback)
    const sampleData = {
        temperature: realFloatData.length > 0 ? realFloatData : [],
        salinity: realFloatData.length > 0 ? realFloatData.map(d => ({ ...d, value: Math.random() * 2 + 34 })) : []
    };

    const normalizeValue = (value, param) => {
        const ranges = {
            temperature: { min: 18, max: 30 },  // Indian Ocean temperature range
            salinity: { min: 32, max: 37 }      // Indian Ocean salinity range
        };

        const range = ranges[param] || ranges.temperature;
        return Math.max(0, Math.min(1, (value - range.min) / (range.max - range.min)));
    };

    const getGradient = (param) => {
        const gradients = {
            temperature: {
                0.0: '#1e3a8a',
                0.2: '#3b82f6',
                0.4: '#06b6d4',
                0.6: '#10b981',
                0.8: '#f59e0b',
                1.0: '#dc2626'
            },
            salinity: {
                0.0: '#1e3a8a',
                0.2: '#3b82f6',
                0.4: '#06b6d4',
                0.6: '#10b981',
                0.8: '#f59e0b',
                1.0: '#dc2626'
            }
        };
        return gradients[param] || gradients.temperature;
    };

    const getMarkerColor = (value, param) => {
        const normalized = normalizeValue(value, param);
        const gradient = getGradient(param);

        if (normalized <= 0.2) return gradient[0.0];
        if (normalized <= 0.4) return gradient[0.2];
        if (normalized <= 0.6) return gradient[0.4];
        if (normalized <= 0.8) return gradient[0.6];
        return gradient[1.0];
    };

    const createPopupContent = (point, param) => {
        const unit = param === 'temperature' ? '°C' : 'PSU';
        const dateStr = point.datetime ? new Date(point.datetime).toLocaleDateString() : 'N/A';
        const distanceInfo = point.distance_km ? `<p><strong>Distance from coast:</strong> ${point.distance_km}km</p>` : '';
        return `
            <div class="popup-content">
                <h4>Argo Float ${point.float_id || point.profile}</h4>
                <p><strong>Location:</strong> ${point.lat.toFixed(4)}°, ${point.lng.toFixed(4)}°</p>
                ${distanceInfo}
                <p><strong>Date:</strong> ${dateStr}</p>
                <p><strong>Depth:</strong> ${point.depth}m</p>
                <p><strong>${param.charAt(0).toUpperCase() + param.slice(1)}:</strong> ${point.value.toFixed(2)}${unit}</p>
                <p><strong>Measurements:</strong> ${point.measurements || 'N/A'}</p>
                <p style="font-size: 0.85em; color: #666; margin-top: 8px;">
                    <em>Within ${radiusKm}km of Indian Coast</em>
                </p>
            </div>
        `;
    };

    const initializeMap = React.useCallback(() => {
        // Determine map center based on real data
        const mapCenter = realFloatData.length > 0
            ? [realFloatData[0].lat, realFloatData[0].lng]
            : [10, 70];  // Default to Indian Ocean center

        const mapZoom = realFloatData.length > 0 ? 4 : 3;

        const map = L.map(mapRef.current, {
            center: mapCenter,
            zoom: mapZoom,
            zoomControl: true,
            scrollWheelZoom: true,
        });

        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© Esri, GEBCO, NOAA, National Geographic, DeLorme, HERE',
            maxZoom: 16,
        }).addTo(map);

        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© Esri, GEBCO, NOAA',
            maxZoom: 16,
            opacity: 0.5
        }).addTo(map);

        mapInstanceRef.current = map;
        addMapControls(map);
    }, [currentParameter, realFloatData]);

    const updateMapData = React.useCallback(() => {
        if (!mapInstanceRef.current) {
            console.log('⚠️ Map instance not ready');
            return;
        }

        console.log('🗺️ Updating map data...');
        setIsLoading(true);

        if (heatmapLayerRef.current) {
            mapInstanceRef.current.removeLayer(heatmapLayerRef.current);
        }
        if (markersLayerRef.current) {
            mapInstanceRef.current.removeLayer(markersLayerRef.current);
        }

        const dataToUse = mapData || sampleData[currentParameter] || sampleData.temperature;
        console.log(`📍 Using ${dataToUse.length} data points for visualization`);

        if (dataToUse.length > 0) {
            createHeatmapLayer(dataToUse);
            createMarkersLayer(dataToUse);
        } else {
            console.warn('⚠️ No data to display on map');
        }

        setIsLoading(false);
    }, [mapData, currentParameter, realFloatData]);

    const createHeatmapLayer = (data) => {
        const heatmapData = data.map(point => {
            const intensity = normalizeValue(point.value, currentParameter);
            return [point.lat, point.lng, intensity * 0.8];
        });

        const heatmapLayer = L.heatLayer(heatmapData, {
            radius: 30,
            blur: 20,
            maxZoom: 16,
            max: 0.8,
            gradient: getGradient(currentParameter)
        });

        heatmapLayer.addTo(mapInstanceRef.current);
        heatmapLayerRef.current = heatmapLayer;
    };

    const createMarkersLayer = (data) => {
        console.log(`🎯 Creating markers for ${data.length} points`);
        const markersLayer = L.layerGroup();

        data.forEach((point, index) => {
            const color = getMarkerColor(point.value, currentParameter);

            const marker = L.circleMarker([point.lat, point.lng], {
                radius: 12,
                fillColor: color,
                color: '#ffffff',
                weight: 3,
                opacity: 1,
                fillOpacity: 0.9
            }).bindPopup(createPopupContent(point, currentParameter));

            markersLayer.addLayer(marker);

            if (index < 3) {
                console.log(`  Marker ${index + 1}: (${point.lat}, ${point.lng}) - ${point.float_id}`);
            }
        });

        markersLayer.addTo(mapInstanceRef.current);
        markersLayerRef.current = markersLayer;
        console.log(`✅ Added ${markersLayer.getLayers().length} markers to map`);

        if (data.length > 0) {
            const group = new L.featureGroup(markersLayer.getLayers());
            mapInstanceRef.current.fitBounds(group.getBounds().pad(0.2));

            setTimeout(() => {
                const currentZoom = mapInstanceRef.current.getZoom();
                if (currentZoom > 12) {
                    mapInstanceRef.current.setZoom(12);
                } else if (currentZoom < 6) {
                    mapInstanceRef.current.setZoom(8);
                }
            }, 500);
        }
    };

    const addMapControls = (map) => {
        const ParameterControl = L.Control.extend({
            onAdd: function () {
                const div = L.DomUtil.create('div', 'leaflet-control-parameter');
                div.innerHTML = `
                    <div class="parameter-control">
                        <label>Parameter:</label>
                        <select id="parameter-select">
                            <option value="temperature" ${currentParameter === 'temperature' ? 'selected' : ''}>Temperature</option>
                            <option value="salinity" ${currentParameter === 'salinity' ? 'selected' : ''}>Salinity</option>
                        </select>
                    </div>
                `;

                L.DomEvent.disableClickPropagation(div);

                const select = div.querySelector('#parameter-select');
                select.addEventListener('change', (e) => {
                    const newParameter = e.target.value;
                    setCurrentParameter(newParameter);
                    updateMarkersForParameter(newParameter);
                    updateLegend(newParameter);
                    updateInfoBar(newParameter);
                });

                return div;
            }
        });

        new ParameterControl({ position: 'topright' }).addTo(map);

        // Radius Control for visualization team
        const RadiusControl = L.Control.extend({
            onAdd: function () {
                const div = L.DomUtil.create('div', 'leaflet-control-radius');
                div.innerHTML = `
                    <div class="radius-control" style="background: white; padding: 10px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); margin-top: 10px;">
                        <label style="font-weight: bold; display: block; margin-bottom: 5px;">Radius (km):</label>
                        <input type="range" id="radius-slider" min="100" max="5000" step="100" value="${radiusKm}" 
                               style="width: 150px; display: block; margin-bottom: 5px;" />
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span id="radius-value" style="font-size: 14px; font-weight: bold;">${radiusKm}km</span>
                            <button id="apply-radius" style="padding: 4px 8px; background: #1e90ff; color: white; border: none; border-radius: 3px; cursor: pointer;">Apply</button>
                        </div>
                    </div>
                `;

                L.DomEvent.disableClickPropagation(div);

                const slider = div.querySelector('#radius-slider');
                const valueDisplay = div.querySelector('#radius-value');
                const applyButton = div.querySelector('#apply-radius');

                slider.addEventListener('input', (e) => {
                    valueDisplay.textContent = e.target.value + 'km';
                });

                applyButton.addEventListener('click', () => {
                    const newRadius = parseInt(slider.value);
                    console.log(`🎯 Applying new radius: ${newRadius}km`);
                    setRadiusKm(newRadius);
                });

                return div;
            }
        });

        new RadiusControl({ position: 'topright' }).addTo(map);

        const LegendControl = L.Control.extend({
            onAdd: function () {
                const div = L.DomUtil.create('div', 'leaflet-control-legend');
                div.innerHTML = getLegendHTML(currentParameter);
                return div;
            }
        });

        const legendControl = new LegendControl({ position: 'bottomright' }).addTo(map);
        map.legendControl = legendControl;
    };

    const getLegendHTML = (param) => {
        const legends = {
            temperature: `
                <div class="legend">
                    <h4>Temperature (°C)</h4>
                    <div class="legend-item"><span class="legend-color" style="background: #1e3a8a"></span> < 0°C</div>
                    <div class="legend-item"><span class="legend-color" style="background: #3b82f6"></span> 0-1°C</div>
                    <div class="legend-item"><span class="legend-color" style="background: #06b6d4"></span> 1-2°C</div>
                    <div class="legend-item"><span class="legend-color" style="background: #10b981"></span> 2-3°C</div>
                    <div class="legend-item"><span class="legend-color" style="background: #f59e0b"></span> 3-4°C</div>
                    <div class="legend-item"><span class="legend-color" style="background: #dc2626"></span> > 4°C</div>
                </div>
            `,
            salinity: `
                <div class="legend">
                    <h4>Salinity (PSU)</h4>
                    <div class="legend-item"><span class="legend-color" style="background: #1e3a8a"></span> < 28</div>
                    <div class="legend-item"><span class="legend-color" style="background: #3b82f6"></span> 28-30</div>
                    <div class="legend-item"><span class="legend-color" style="background: #06b6d4"></span> 30-32</div>
                    <div class="legend-item"><span class="legend-color" style="background: #10b981"></span> 32-34</div>
                    <div class="legend-item"><span class="legend-color" style="background: #f59e0b"></span> 34-36</div>
                    <div class="legend-item"><span class="legend-color" style="background: #dc2626"></span> > 36</div>
                </div>
            `
        };
        return legends[param] || legends.temperature;
    };

    const updateMarkersForParameter = (newParameter) => {
        if (!mapInstanceRef.current) return;

        if (markersLayerRef.current) {
            mapInstanceRef.current.removeLayer(markersLayerRef.current);
        }
        if (heatmapLayerRef.current) {
            mapInstanceRef.current.removeLayer(heatmapLayerRef.current);
        }

        const dataToUse = mapData || sampleData[newParameter] || sampleData.temperature;

        // Create new heatmap
        createHeatmapLayer(dataToUse, newParameter);

        // Create new markers
        const markersLayer = L.layerGroup();

        dataToUse.forEach((point) => {
            const color = getMarkerColor(point.value, newParameter);

            const marker = L.circleMarker([point.lat, point.lng], {
                radius: 12,
                fillColor: color,
                color: '#ffffff',
                weight: 3,
                opacity: 1,
                fillOpacity: 0.9
            }).bindPopup(createPopupContent(point, newParameter));

            markersLayer.addLayer(marker);
        });

        markersLayer.addTo(mapInstanceRef.current);
        markersLayerRef.current = markersLayer;
    };

    const updateLegend = (newParameter) => {
        if (!mapInstanceRef.current || !mapInstanceRef.current.legendControl) return;

        mapInstanceRef.current.removeControl(mapInstanceRef.current.legendControl);

        const LegendControl = L.Control.extend({
            onAdd: function () {
                const div = L.DomUtil.create('div', 'leaflet-control-legend');
                div.innerHTML = getLegendHTML(newParameter);
                return div;
            }
        });

        const legendControl = new LegendControl({ position: 'bottomright' }).addTo(mapInstanceRef.current);
        mapInstanceRef.current.legendControl = legendControl;
    };

    const updateInfoBar = (newParameter) => {
        const parameterDisplay = document.getElementById('parameter-display');
        const parameterIcon = parameterDisplay?.parentElement.querySelector('i');

        if (parameterDisplay) {
            parameterDisplay.textContent = `Showing ${newParameter} data`;
        }

        if (parameterIcon) {
            parameterIcon.className = `fas ${newParameter === 'temperature' ? 'fa-thermometer-half' : 'fa-tint'}`;
        }
    };

    useEffect(() => {
        if (!dataLoaded) return; // Wait for data to load first

        if (isVisible && mapRef.current && !mapInstanceRef.current) {
            setTimeout(() => {
                initializeMap();
                setTimeout(() => {
                    updateMapData();
                }, 300);
            }, 100);
        } else if (isVisible && mapInstanceRef.current) {
            updateMapData();
            setTimeout(() => {
                if (mapInstanceRef.current) {
                    mapInstanceRef.current.invalidateSize();
                }
            }, 200);
        }

        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, [isVisible, mapData, currentParameter, dataLoaded, initializeMap, updateMapData]);

    useEffect(() => {
        const handleResize = () => {
            if (mapInstanceRef.current && isVisible) {
                setTimeout(() => {
                    mapInstanceRef.current.invalidateSize();
                }, 100);
            }
        };

        if (isVisible) {
            window.addEventListener('resize', handleResize);
            return () => window.removeEventListener('resize', handleResize);
        }
    }, [isVisible]);

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && isVisible) {
                onClose();
            }
        };

        if (isVisible) {
            document.addEventListener('keydown', handleKeyDown);
            return () => document.removeEventListener('keydown', handleKeyDown);
        }
    }, [isVisible, onClose]);

    useEffect(() => {
        if (isVisible) {
            document.body.style.overflow = 'hidden';
            return () => {
                document.body.style.overflow = 'unset';
            };
        }
    }, [isVisible]);

    if (!isVisible) return null;

    const handleOverlayClick = (e) => {
        if (e.target.classList.contains('map-overlay')) {
            onClose();
        }
    };

    return createPortal(
        <div className="map-overlay" onClick={handleOverlayClick}>
            <div className="map-container">
                <div className="map-header">
                    <h3>
                        <i className="fas fa-map"></i>
                        Oceanographic Data Visualization
                    </h3>
                    <button className="close-map-btn" onClick={onClose}>
                        <i className="fas fa-times"></i>
                    </button>
                </div>

                {isLoading && (
                    <div className="map-loading">
                        <i className="fas fa-spinner fa-spin"></i>
                        <span>Loading map data...</span>
                    </div>
                )}

                <div className="map-content">
                    <div ref={mapRef} className="leaflet-map"></div>
                </div>

                <div className="map-info">
                    <div className="info-item">
                        <i className={`fas ${currentParameter === 'temperature' ? 'fa-thermometer-half' : 'fa-tint'}`}></i>
                        <span id="parameter-display">Showing {currentParameter} data</span>
                    </div>
                    <div className="info-item">
                        <i className="fas fa-map-marker-alt"></i>
                        <span>{realFloatData.length} Argo Float Profiles</span>
                    </div>
                    <div className="info-item">
                        <i className="fas fa-layer-group"></i>
                        <span>Heatmap + Markers</span>
                    </div>
                </div>
            </div>
        </div>,
        document.body
    );
};

export default MapVisualization;