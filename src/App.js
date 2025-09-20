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

  return (
    <div className="container">
      <Sidebar />
      <ChatContainer onMapRequest={handleMapRequest} />
      <DataSidebar selectedView={dataSidebarView} onViewChange={setDataSidebarView} />
    </div>
  );
}

export default App;