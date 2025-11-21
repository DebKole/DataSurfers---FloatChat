import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import MapPage from './components/MapPage';
import MapTrajectories from './components/MapTrajectories';
import PlotProfileTool from './components/PlotProfile';
import CompareProfilesTool from './components/CompareProfilesTool';
import './index.css';

//Main chat interface
function ChatInterface() {
  const [dataSidebarView, setDataSidebarView] = useState('table');
  const navigate = useNavigate();
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

  const handleMapRequest = () => {
    // Open the full-page Map view directly when chat requests the map
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
        onOpenTrajectoryOverlay={() => setShowTrajectoryOverlay(true)}
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
              <MapTrajectories fullScreen={true} />
            </div>
          </div>
        </div>
      )}
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