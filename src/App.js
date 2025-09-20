import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import './index.css';

function App() {

  const [dataSidebarView, setDataSidebarView] = useState('table');

  const handleMapRequest = () => {
    setDataSidebarView('map');
  };

  const [mapData, setMapData] = useState(null);
  const [showMap, setShowMap] = useState(false);

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
      />

    </div>
  );
}

export default App;