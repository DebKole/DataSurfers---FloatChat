import React, { useState, useEffect } from 'react';
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

  // Suppress Leaflet _leaflet_pos errors that occur during map initialization
  useEffect(() => {
    const handleError = (event) => {
      const error = event.error || event;
      const errorMessage = error?.message || String(error);
      
      // Suppress the specific Leaflet _leaflet_pos error
      if (errorMessage && errorMessage.includes('_leaflet_pos')) {
        event.preventDefault();
        event.stopPropagation();
        return false;
      }
    };

    // Add error event listener
    window.addEventListener('error', handleError, true);
    
    // Also catch unhandled promise rejections
    const handleUnhandledRejection = (event) => {
      const errorMessage = event.reason?.message || String(event.reason);
      if (errorMessage && errorMessage.includes('_leaflet_pos')) {
        event.preventDefault();
        return false;
      }
    };
    
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError, true);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  return (
    <div className="map-page">
      <div className="map-header">
        {/* <button className="back-button" onClick={() => navigate(-1)}>
          ← Back
        </button> */}
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