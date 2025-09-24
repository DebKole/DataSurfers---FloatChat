import React, { useState } from 'react';
import PPTMapVisualization from './PPTMapVisualization';
import './PPTDemo.css';

const PPTDemo = () => {
  const [showMap, setShowMap] = useState(false);

  return (
    <div className="ppt-demo-container">
      <div className="ppt-demo-content">
        <div className="ppt-demo-header">
          <h1>🌊 FloatChat</h1>
          <h2>Ocean Intelligence Through AI</h2>
          <p>Conversational AI for advanced oceanographic analysis and environmental monitoring</p>
        </div>

        <div className="ppt-demo-features">
          <div className="feature-grid">
            <div className="feature-card innovation">
              <div className="feature-icon">🏭</div>
              <h3>Pollution Detection</h3>
              <p>Real-time contamination monitoring and alert system</p>
            </div>
            
            <div className="feature-card innovation">
              <div className="feature-icon">🐟</div>
              <h3>Mesopelagic Organism Detection</h3>
              <p>Deep-sea life monitoring and biomass estimation</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>AI-Powered Chat</h3>
              <p>Natural language ocean data queries</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📍</div>
              <h3>Interactive Mapping</h3>
              <p>Visual ocean data exploration</p>
            </div>
          </div>
        </div>

        <div className="ppt-demo-cta">
          <button 
            className="demo-map-button"
            onClick={() => setShowMap(true)}
          >
            🗺️ View Global Ocean Network
          </button>
          <p className="demo-stats">
            <span>70+ Active Floats</span> • 
            <span>8 Ocean Regions</span> • 
            <span>Real-time Monitoring</span>
          </p>
        </div>

        <div className="ppt-demo-tagline">
          <h3>Detect. Monitor. Protect.</h3>
        </div>
      </div>

      {showMap && (
        <PPTMapVisualization 
          isVisible={showMap} 
          onClose={() => setShowMap(false)} 
        />
      )}
    </div>
  );
};

export default PPTDemo;