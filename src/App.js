import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import MapPage from './components/MapPage';
import './index.css';

//Main chat interface
function ChatInterface() {
  const [dataSidebarView, setDataSidebarView] = useState('table');
  const navigate = useNavigate();

  const handleMapRequest = () => {
    // Open the full-page Map view directly when chat requests the map
    navigate('/map', { state: { source: 'chat' } });
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
function App() {
  const [showFAQ, setShowFAQ] = useState(false); //Add state
  return (
    
    <Router>
      <Routes>
        <Route path="/" element={<ChatInterface />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/map" element={<MapPage />} />

      </Routes>
    </Router>
    
  );
}

export default App;