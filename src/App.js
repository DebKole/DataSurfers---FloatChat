import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import MapTrajectories from './components/MapTrajectories';
import './index.css';

import { useArgoDemoData } from './useargodemodata';

function App() {
  const argoRows = useArgoDemoData();

  const [dataSidebarView, setDataSidebarView] = useState('table');
  const [mapData, setMapData] = useState(null);
  const [showMap, setShowMap] = useState(false);
  const [showTrajectoryOverlay, setShowTrajectoryOverlay] = useState(false);

  const handleMapRequest = () => {
    setDataSidebarView('map');
  };

  const handleMapData = (data, shouldShow) => {
    setMapData(data);
    setShowMap(shouldShow);
  };

  const handleMapClose = () => {
    setShowMap(false);
  };

  return (
    <div className="container">
      <Sidebar />

      <ChatContainer onMapRequest={handleMapRequest} onMapData={handleMapData} />
      <DataSidebar 
        selectedView={dataSidebarView} 
        onViewChange={setDataSidebarView}
        mapData={mapData} 
        showMap={showMap} 
        onMapClose={handleMapClose} 
        onOpenTrajectoryOverlay={() => setShowTrajectoryOverlay(true)}
        argoRows={argoRows}
      />
      {showTrajectoryOverlay && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              backgroundColor: '#fff',
              padding: '1rem',
              borderRadius: '8px',
              width: '90%',
              height: '80%',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <h2 style={{ margin: 0 }}>Trajectory Map</h2>
              <button className="view-more-btn" onClick={() => setShowTrajectoryOverlay(false)}>
                Close
              </button>
            </div>
            <div style={{ flex: 1 }}>
              <MapTrajectories />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;