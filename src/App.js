import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import MapPage from './components/MapPage';
import MapTrajectories from './components/MapTrajectories';
import PlotProfileTool from './components/PlotProfile';
import CompareProfilesTool from './components/CompareProfilesTool';
import './index.css';

// ---------------- MAIN CHAT INTERFACE ----------------
function ChatInterface() {
  const [dataSidebarView, setDataSidebarView] = useState('map');
  const [showChatHistory, setShowChatHistory] = useState(false);
  const navigate = useNavigate();

  // ---------------- CHAT HISTORY ----------------
  const [chatHistory, setChatHistory] = useState([
    {
      id: 1,
      title: 'Ocean Temperature Analysis',
      date: '2024-01-15',
      preview: 'Analyzing temperature trends in Pacific...',
    },
    {
      id: 2,
      title: 'Salinity Data Query',
      date: '2024-01-14',
      preview: 'Looking at salinity levels in Arctic...',
    },
    {
      id: 3,
      title: 'Deep Ocean Exploration',
      date: '2024-01-13',
      preview: 'Exploring abyssal zone characteristics...',
    },
    {
      id: 4,
      title: 'Current Patterns Study',
      date: '2024-01-12',
      preview: 'Understanding ocean current patterns...',
    },
  ]);
  const [activeChatId, setActiveChatId] = useState(null);

  // Keep BOTH versions of the handler
  const handleSelectChat = (chat) => {
    setActiveChatId(chat.id);
    console.log('Selected chat from history:', chat);
    // future: load messages for chat id
  };

  // Keep BOTH: table data AND map/trajectory/demo features
  const [tableData, setTableData] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [showMap, setShowMap] = useState(false);
  const [showTrajectoryOverlay, setShowTrajectoryOverlay] = useState(false);

  const [demoFloatId, setDemoFloatId] = useState('5906527');

  const [tsProfiles, setTsProfiles] = useState([]);
  const [tsLoading, setTsLoading] = useState(false);
  const [tsError, setTsError] = useState(null);

  const [tdProfiles, setTdProfiles] = useState([]);
  const [tdLoading, setTdLoading] = useState(false);
  const [tdError, setTdError] = useState(null);

  const [compareFloatIdA, setCompareFloatIdA] = useState('5906527');
  const [compareFloatIdB, setCompareFloatIdB] = useState('1901744');
  const [compareProfiles, setCompareProfiles] = useState([]);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState(null);

  const [compareTsProfiles, setCompareTsProfiles] = useState([]);
  const [compareTsLoading, setCompareTsLoading] = useState(false);
  const [compareTsError, setCompareTsError] = useState(null);

  // ---------------- ACTION HANDLERS ----------------
  const handleMapRequest = () => {
    // always navigate to full-page map view
    navigate('/map', { state: { source: 'chat' } });
  };

  const handleMapData = (data, shouldShow) => {
    setMapData(data);
    setShowMap(shouldShow);
  };

  const handleMapClose = () => {
    setShowMap(false);
  };

  const handleTestTsCurve = async () => {
    setTsLoading(true);
    setTsError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/ts_curve?float_id=${demoFloatId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setTsProfiles(data.profiles || []);
    } catch (err) {
      setTsError(err.message || String(err));
      setTsProfiles([]);
    } finally {
      setTsLoading(false);
    }
  };

  const handleTestTdCurve = async () => {
    setTdLoading(true);
    setTdError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/td_curve?float_id=${demoFloatId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setTdProfiles(data.profiles || []);
    } catch (err) {
      setTdError(err.message || String(err));
      setTdProfiles([]);
    } finally {
      setTdLoading(false);
    }
  };

  const handleCompareTdProfiles = async () => {
    setCompareLoading(true);
    setCompareError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/compare_td?float_id_a=${compareFloatIdA}&float_id_b=${compareFloatIdB}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setCompareProfiles(data.profiles || []);
    } catch (err) {
      setCompareError(err.message || String(err));
      setCompareProfiles([]);
    } finally {
      setCompareLoading(false);
    }
  };

  const handleCompareTsProfiles = async () => {
    setCompareTsLoading(true);
    setCompareTsError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/compare_ts?float_id_a=${compareFloatIdA}&float_id_b=${compareFloatIdB}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setCompareTsProfiles(data.profiles || []);
    } catch (err) {
      setCompareTsError(err.message || String(err));
      setCompareTsProfiles([]);
    } finally {
      setCompareTsLoading(false);
    }
  };

  const handleTableData = (data) => {
    setTableData(data);
  };

  const toggleChatHistory = () => {
    setShowChatHistory(prev => !prev);
  };

  return (
    <div className="app-container">

      <ChatContainer
        onMapRequest={handleMapRequest}
        onMapData={handleMapData}
        onTableData={handleTableData}
        showChatHistory={showChatHistory}
        onToggleChatHistory={toggleChatHistory}
        chatHistory={chatHistory}
        onSelectChat={handleSelectChat}
      />

      <DataSidebar
        selectedView={dataSidebarView}
        onViewChange={setDataSidebarView}
        mapData={mapData}
        showMap={showMap}
        onMapClose={handleMapClose}
        tableData={tableData}
        onOpenTrajectoryOverlay={() => setShowTrajectoryOverlay(true)}
      />

      {showTrajectoryOverlay && (
        <div className="trajectory-overlay">
          <div className="trajectory-modal">
            <div className="trajectory-header">
              <h2>Trajectory Map</h2>
              <button className="close-button" onClick={() => setShowTrajectoryOverlay(false)}>
                Close
              </button>
            </div>
            <div className="trajectory-content">
              <MapTrajectories fullScreen={true} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------- MAIN APP ROUTES ----------------
function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<ChatInterface />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/map" element={<MapPage />} />
      </Routes>
    </div>
  );
}

export default App;
