import React from 'react';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import './index.css';

function App() {
  return (
    <div className="container">
      <Sidebar />
      <ChatContainer />
      <DataSidebar />
    </div>
  );
}

export default App;