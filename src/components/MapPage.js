import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import MapComponent from './MapComponent';
import ChatContainer from './ChatContainer';
import './MapPage.css';

const MapPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mapData } = location.state || {};
  const [showChat, setShowChat] = useState(false);
  const [chatMapData, setChatMapData] = useState(mapData || null);

  return (
    <div className="map-page">
      <div className="map-header">
        <button className="back-button" onClick={() => navigate(-1)}>
          ← Back
        </button>
        <h1>Oceanographic Data Visualization</h1>
        <button className="ask-chat-button" onClick={() => setShowChat(true)}>
          Ask FloatChat
        </button>
      </div>

      <div className="map-content">
        <MapComponent fullPage={true} data={chatMapData} />
      </div>

      {showChat && (
        <>
          <div className="chat-overlay" onClick={() => setShowChat(false)} />
          <div className="chat-drawer" role="dialog" aria-label="FloatChat drawer">
            <button className="chat-close" onClick={() => setShowChat(false)} aria-label="Close chat">
              ×
            </button>
            <ChatContainer 
              onMapRequest={() => {/* already on map; no navigation needed */}}
              onMapData={(data) => {
                try {
                  setChatMapData(data);
                } catch (_) {}
              }}
            />
          </div>
        </>
      )}
    </div>
  );
};

export default MapPage;