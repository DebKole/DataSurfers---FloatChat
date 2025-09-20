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

    // Sample oceanographic data for demonstration
    const sampleData = {
        temperature: [
            { lat: 73.2692, lng: -57.9165, value: 2.82, depth: 0, profile: 0 },
            { lat: 73.2704, lng: -57.9189, value: 3.26, depth: 0, profile: 1 },
            { lat: 73.279, lng: -57.9338, value: 3.63, depth: 0, profile: 2 },
            { lat: 73.2757, lng: -57.9801, value: 3.87, depth: 0, profile: 3 },
            { lat: 73.2606, lng: -58.0544, value: 3.89, depth: 0, profile: 4 },
            { lat: 73.25, lng: -57.85, value: 3.1, depth: 0, profile: 'extra_1' },
            { lat: 73.30, lng: -57.75, value: 3.4, depth: 0, profile: 'extra_2' },
            { lat: 73.22, lng: -58.15, value: 3.6, depth: 0, profile: 'extra_3' },
            { lat: 73.28, lng: -58.05, value: 2.9, depth: 0, profile: 'extra_4' },
            { lat: 73.24, lng: -57.95, value: 3.2, depth: 0, profile: 'extra_5' },
        ],
        salinity: [
            { lat: 73.2692, lng: -57.9165, value: 32.17, depth: 0, profile: 0 },
            { lat: 73.2704, lng: -57.9189, value: 32.15, depth: 0, profile: 1 },
            { lat: 73.279, lng: -57.9338, value: 32.15, depth: 0, profile: 2 },
            { lat: 73.2757, lng: -57.9801, value: 25.59, depth: 0, profile: 3 },
            { lat: 73.2606, lng: -58.0544, value: 29.34, depth: 0, profile: 4 },
            { lat: 73.25, lng: -57.85, value: 31.8, depth: 0, profile: 'extra_1' },
            { lat: 73.30, lng: -57.75, value: 30.2, depth: 0, profile: 'extra_2' },
            { lat: 73.22, lng: -58.15, value: 28.9, depth: 0, profile: 'extra_3' },
            { lat: 73.28, lng: -58.05, value: 33.1, depth: 0, profile: 'extra_4' },
            { lat: 73.24, lng: -57.95, value: 32.5, depth: 0, profile: 'extra_5' },
        ]
    };

    const normalizeValue = (value, param) => {
        const ranges = {
            temperature: { min: -2, max: 5 },
            salinity: { min: 25, max: 36 }
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
        return `
            <div class="popup-content">
                <h4>Argo Float Data</h4>
                <p><strong>Profile:</strong> ${point.profile}</p>
                <p><strong>Location:</strong> ${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}</p>
                <p><strong>Depth:</strong> ${point.depth}m</p>
                <p><strong>${param.charAt(0).toUpperCase() + param.slice(1)}:</strong> ${point.value}${unit}</p>
            </div>
        `;
    };

    const initializeMap = React.useCallback(() => {
        const map = L.map(mapRef.current, {
            center: [73.27, -58.0],
            zoom: 8,
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
    }, [currentParameter]);

    const updateMapData = React.useCallback(() => {
        if (!mapInstanceRef.current) return;

        setIsLoading(true);

        if (heatmapLayerRef.current) {
            mapInstanceRef.current.removeLayer(heatmapLayerRef.current);
        }
        if (markersLayerRef.current) {
            mapInstanceRef.current.removeLayer(markersLayerRef.current);
        }

        const dataToUse = mapData || sampleData[currentParameter] || sampleData.temperature;
        
        createHeatmapLayer(dataToUse);
        createMarkersLayer(dataToUse);
        
        setIsLoading(false);
    }, [mapData, currentParameter]);

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
        const markersLayer = L.layerGroup();

        data.forEach((point) => {
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
        });

        markersLayer.addTo(mapInstanceRef.current);
        markersLayerRef.current = markersLayer;

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
    }, [isVisible, mapData, currentParameter, initializeMap, updateMapData]);

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
                        <span>10 Argo Float Profiles</span>
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