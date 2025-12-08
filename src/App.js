import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import MapPage from './components/MapPage';
import MapTrajectories from './components/MapTrajectories';
import PlotProfileTool from './components/PlotProfile';
import CompareProfilesTool from './components/CompareProfilesTool';
import './index.css';

// Main chat interface
function ChatInterface() {
  const [dataSidebarView, setDataSidebarView] = useState('table');
  const navigate = useNavigate();
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

  const handleMapRequest = () => {
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
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
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
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
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
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
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
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
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

  return (
    <div className="app-container">
      <Sidebar />
      <ChatContainer 
        onMapRequest={handleMapRequest} 
        onMapData={handleMapData} 
        onTableData={handleTableData} 
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
              <button 
                className="close-button" 
                onClick={() => setShowTrajectoryOverlay(false)}
              >
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