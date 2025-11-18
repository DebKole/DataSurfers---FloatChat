import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import './index.css';

function App() {

  const [dataSidebarView, setDataSidebarView] = useState('table');
  const [tableData, setTableData] = useState(null);

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

  const handleTableData = (data) => {
    setTableData(data);
  };

  return (
    <div className="container">
      <Sidebar />

      <ChatContainer onMapRequest={handleMapRequest} onMapData={handleMapData} onTableData={handleTableData} />
      <DataSidebar 
        selectedView={dataSidebarView} 
        onViewChange={setDataSidebarView}
        mapData={mapData} 
        showMap={showMap} 
        onMapClose={handleMapClose}
        tableData={tableData}
      />

    </div>
  );
}

export default App;