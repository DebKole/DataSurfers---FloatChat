import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import DataSidebar from './components/DataSidebar';
import MapTrajectories from './components/MapTrajectories';
import PlotProfileTool from './components/PlotProfile';
import CompareProfilesTool from './components/CompareProfilesTool';
import './index.css';

import { useArgoDemoData } from './useargodemodata';

function App() {
  const argoRows = useArgoDemoData();

  const [dataSidebarView, setDataSidebarView] = useState('table');
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
    setDataSidebarView('map');
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
      {/* Simple TS/TD demo panel using PlotProfileTool and FastAPI trend_api */}
      <div
        style={{
          position: 'fixed',
          bottom: '1rem',
          right: '1rem',
          backgroundColor: 'rgba(255,255,255,0.95)',
          padding: '0.75rem',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          zIndex: 5000,
          maxWidth: '420px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <strong>TS / TD Demo</strong>
          <button
            className="view-more-btn"
            style={{ padding: '0.15rem 0.5rem', fontSize: '0.75rem' }}
            onClick={() => {
              setTsProfiles([]);
              setTdProfiles([]);
              setCompareProfiles([]);
              setCompareTsProfiles([]);
              setTsError(null);
              setTdError(null);
              setCompareError(null);
              setCompareTsError(null);
            }}
          >
            Clear
          </button>
        </div>
        <div style={{ marginTop: '0.25rem' }}>
          <label style={{ color: '#003366' }}>
            Float ID:{' '}
            <input
              type="text"
              value={demoFloatId}
              onChange={(e) => setDemoFloatId(e.target.value)}
              style={{ width: '120px' }}
            />
          </label>
        </div>
        <div style={{ marginTop: '0.25rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <div>
            <label style={{ color: '#003366' }}>
              Compare A:{' '}
              <input
                type="text"
                value={compareFloatIdA}
                onChange={(e) => setCompareFloatIdA(e.target.value)}
                style={{ width: '110px' }}
              />
            </label>
          </div>
          <div>
            <label style={{ color: '#003366' }}>
              Compare B:{' '}
              <input
                type="text"
                value={compareFloatIdB}
                onChange={(e) => setCompareFloatIdB(e.target.value)}
                style={{ width: '110px' }}
              />
            </label>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem', flexWrap: 'wrap' }}>
          <button className="view-more-btn" onClick={handleTestTsCurve} disabled={tsLoading}>
            {tsLoading ? 'Loading TS…' : 'Fetch TS Curve'}
          </button>
          <button className="view-more-btn" onClick={handleTestTdCurve} disabled={tdLoading}>
            {tdLoading ? 'Loading TD…' : 'Fetch TD Profile'}
          </button>
          <button className="view-more-btn" onClick={handleCompareTdProfiles} disabled={compareLoading}>
            {compareLoading ? 'Comparing…' : 'Compare TD Profiles'}
          </button>
          <button className="view-more-btn" onClick={handleCompareTsProfiles} disabled={compareTsLoading}>
            {compareTsLoading ? 'Comparing TS…' : 'Compare TS Profiles'}
          </button>
        </div>
        {(tsError || tdError || compareError || compareTsError) && (
          <div style={{ color: 'red', marginTop: '0.25rem' }}>
            {tsError && <div>TS Error: {tsError}</div>}
            {tdError && <div>TD Error: {tdError}</div>}
            {compareError && <div>Compare Error: {compareError}</div>}
            {compareTsError && <div>Compare TS Error: {compareTsError}</div>}
          </div>
        )}

        {tsProfiles.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <PlotProfileTool
              profiles={tsProfiles}
              profileId={1}
              xKey="salinity"
              yKey="temperature"
              xLabel="Salinity (PSU)"
              yLabel="Temperature (°C)"
            />
          </div>
        )}
        {tdProfiles.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <PlotProfileTool
              profiles={tdProfiles}
              profileId={1}
              xKey="depth"
              yKey="temperature"
              xLabel="Depth (m)"
              yLabel="Temperature (°C)"
              invertY={true}
            />
          </div>
        )}
        {compareProfiles.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <CompareProfilesTool
              profiles={compareProfiles}
              profileIds={compareProfiles.map((p) => p.profileId)}
              variable="TEMP"
            />
          </div>
        )}
        {compareTsProfiles.length >= 1 && (
          <div style={{ marginTop: '0.5rem' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>TS Comparison</div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {compareTsProfiles.slice(0, 2).map((profile) => (
                <div key={profile.profileId} style={{ flex: '1 1 200px', minWidth: '200px' }}>
                  <PlotProfileTool
                    profiles={[profile]}
                    profileId={profile.profileId}
                    xKey="salinity"
                    yKey="temperature"
                    xLabel={`Salinity (PSU) – ${profile.label || profile.profileId}`}
                    yLabel="Temperature (°C)"
                  />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

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