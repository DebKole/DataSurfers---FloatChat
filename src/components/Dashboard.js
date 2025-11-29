import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";
import PlotProfileTool from "./PlotProfile";
import CompareProfilesTool from "./CompareProfilesTool";

const Dashboard = ({ onClose }) => {
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    totalProfiles: 0,
    avgTemperature: 0,
    avgSalinity: 0,
    dataQuality: 0,
    globalCoverage: 0,
  });
  const [demoFloatId, setDemoFloatId] = useState("5906527");
  const [compareFloatIdA, setCompareFloatIdA] = useState("5906527");
  const [compareFloatIdB, setCompareFloatIdB] = useState("1901744");
  const [tsProfiles, setTsProfiles] = useState([]);
  const [tdProfiles, setTdProfiles] = useState([]);
  const [compareTdProfiles, setCompareTdProfiles] = useState([]);
  const [compareTsProfiles, setCompareTsProfiles] = useState([]);
  const [tsLoading, setTsLoading] = useState(false);
  const [tdLoading, setTdLoading] = useState(false);
  const [compareTdLoading, setCompareTdLoading] = useState(false);
  const [compareTsLoading, setCompareTsLoading] = useState(false);
  const [tsError, setTsError] = useState(null);
  const [tdError, setTdError] = useState(null);
  const [compareTdError, setCompareTdError] = useState(null);
  const [compareTsError, setCompareTsError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCSVData();
  }, []);

  // Auto-load graphs with default values when dashboard loads
  useEffect(() => {
    if (!loading) {
      // Fetch TS and TD curves for the default Float ID
      if (demoFloatId) {
        handleFetchTsCurve();
        handleFetchTdCurve();
      }
      // Fetch comparison graphs for default Compare A and B
      if (compareFloatIdA && compareFloatIdB) {
        handleCompareTd();
        handleCompareTs();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  const loadCSVData = async () => {
    try {
      const response = await fetch("/argo_demo.csv");
      const csvText = await response.text();
      const parsedData = parseCSV(csvText);
      calculateStats(parsedData);
      setLoading(false);
    } catch (error) {
      console.error("Error loading CSV data:", error);
      setLoading(false);
    }
  };

  const parseCSV = (csvText) => {
    const lines = csvText.split("\n");
    const headers = lines[0].split(",").map((header) => header.trim());

    const data = [];
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue;

      const values = lines[i].split(",");
      const row = {};

      headers.forEach((header, index) => {
        row[header] = values[index] ? values[index].trim() : "";
      });

      data.push(row);
    }

    return data;
  };

  const calculateStats = (data) => {
    if (data.length === 0) return;

    const temperatures = data
      .filter((row) => row.TEMPERATURE && !isNaN(parseFloat(row.TEMPERATURE)))
      .map((row) => parseFloat(row.TEMPERATURE));

    const avgTemp =
      temperatures.length > 0
        ? temperatures.reduce((sum, temp) => sum + temp, 0) /
          temperatures.length
        : 0;

    const salinities = data
      .filter((row) => row.SALINITY && !isNaN(parseFloat(row.SALINITY)))
      .map((row) => parseFloat(row.SALINITY));

    const avgSalinity =
      salinities.length > 0
        ? salinities.reduce((sum, sal) => sum + sal, 0) / salinities.length
        : 0;

    setStats({
      totalProfiles: data.length,
      avgTemperature: avgTemp.toFixed(2),
      avgSalinity: avgSalinity.toFixed(2),
      dataQuality: 98.7,
      globalCoverage: 96.2,
    });
  };

  const handleFetchTsCurve = async () => {
    setTsLoading(true);
    setTsError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/ts_curve?float_id=${demoFloatId}`
      );
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

  const handleFetchTdCurve = async () => {
    setTdLoading(true);
    setTdError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/td_curve?float_id=${demoFloatId}`
      );
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

  const handleCompareTd = async () => {
    setCompareTdLoading(true);
    setCompareTdError(null);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/compare_td?float_id_a=${compareFloatIdA}&float_id_b=${compareFloatIdB}`
      );
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setCompareTdProfiles(data.profiles || []);
    } catch (err) {
      setCompareTdError(err.message || String(err));
      setCompareTdProfiles([]);
    } finally {
      setCompareTdLoading(false);
    }
  };

  const handleCompareTs = async () => {
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

  const handleClose = () => {
    if (typeof onClose === "function") {
      onClose();
    } else {
      navigate(-1);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-overlay">
        <div className="dashboard-modal">
          <div className="dashboard-loading">Loading dashboard data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-overlay">
      <div className="dashboard-modal">
        <button
          className="dashboard-close"
          onClick={handleClose}
          aria-label="Close dashboard"
        >
          ×
        </button>
        <section className="dashboard-section">
          <h2>Dashboard</h2>
          <p>Overview of global oceanographic data</p>
        </section>

        {/* Charts Section */}
        <div className="charts-section">
          <div className="chart-container full-width">
            <div className="graph-title">Live TS / TD and Comparison</div>
            <div className="graph-subtitle">
              Profiles fetched from backend trend API
            </div>
            {/* <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
              <label>
                Float ID:
                <input
                  type="text"
                  value={demoFloatId}
                  onChange={(e) => setDemoFloatId(e.target.value)}
                  style={{ marginLeft: '0.25rem' }}
                />
              </label>
              <label>
                Compare A:
                <input
                  type="text"
                  value={compareFloatIdA}
                  onChange={(e) => setCompareFloatIdA(e.target.value)}
                  style={{ marginLeft: '0.25rem' }}
                />
              </label>
              <label>
                Compare B:
                <input
                  type="text"
                  value={compareFloatIdB}
                  onChange={(e) => setCompareFloatIdB(e.target.value)}
                  style={{ marginLeft: '0.25rem' }}
                />
              </label>
            </div> */}
            <div className="float-input-container">
              <div className="float-input-group">
                <label className="float-input-label">Float ID</label>
                <input
                  type="text"
                  className="float-input-field"
                  value={demoFloatId}
                  onChange={(e) => setDemoFloatId(e.target.value)}
                  placeholder="e.g., 5906527"
                />
              </div>
              <div className="float-input-group">
                <label className="float-input-label">Compare A</label>
                <input
                  type="text"
                  className="float-input-field"
                  value={compareFloatIdA}
                  onChange={(e) => setCompareFloatIdA(e.target.value)}
                  placeholder="e.g., 5906527"
                />
              </div>
              <div className="float-input-group">
                <label className="float-input-label">Compare B</label>
                <input
                  type="text"
                  className="float-input-field"
                  value={compareFloatIdB}
                  onChange={(e) => setCompareFloatIdB(e.target.value)}
                  placeholder="e.g., 1901744"
                />
              </div>
            </div>
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                flexWrap: "wrap",
                marginTop: "1.5rem",
                marginBottom: "0.5rem",
              }}
            >
              <button
                className="view-more-btn"
                onClick={() => {
                  if (demoFloatId) {
                    handleFetchTsCurve();
                    handleFetchTdCurve();
                  }
                  if (compareFloatIdA && compareFloatIdB) {
                    handleCompareTd();
                    handleCompareTs();
                  }
                }}
              >
                Show Graphs
              </button>
              <button
                className="view-more-btn"
                onClick={() => {
                  setTsProfiles([]);
                  setTdProfiles([]);
                  setCompareTdProfiles([]);
                  setCompareTsProfiles([]);
                  setTsError(null);
                  setTdError(null);
                  setCompareTdError(null);
                  setCompareTsError(null);
                }}
              >
                Clear
              </button>
            </div>

            {(tsError || tdError || compareTdError || compareTsError) && (
              <div style={{ color: "red", marginBottom: "0.5rem" }}>
                {tsError && <div>TS Error: {tsError}</div>}
                {tdError && <div>TD Error: {tdError}</div>}
                {compareTdError && (
                  <div>Compare TD Error: {compareTdError}</div>
                )}
                {compareTsError && (
                  <div>Compare TS Error: {compareTsError}</div>
                )}
              </div>
            )}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
              {tsProfiles.length > 0 && (
                <div style={{ flex: "1 1 300px", minWidth: "300px", maxWidth: "100%" }}>
                  <div style={{ fontWeight: "bold", marginBottom: "0.25rem" }}>
                    TS Curve
                  </div>
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
                <div style={{ flex: "1 1 300px", minWidth: "300px", maxWidth: "100%" }}>
                  <div style={{ fontWeight: "bold", marginBottom: "0.25rem" }}>
                    TD Profile
                  </div>
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
            </div>
            {compareTdProfiles.length > 0 && (
              <div style={{ marginTop: "0.75rem" }}>
                <div style={{ fontWeight: "bold", marginBottom: "0.25rem" }}>
                  TD Comparison
                </div>
                <CompareProfilesTool
                  profiles={compareTdProfiles}
                  profileIds={compareTdProfiles.map((p) => p.profileId)}
                  variable="TEMP"
                />
              </div>
            )}
            {compareTsProfiles.length >= 1 && (
              <div style={{ marginTop: "0.75rem" }}>
                <div style={{ fontWeight: "bold", marginBottom: "0.25rem" }}>
                  TS Comparison
                </div>
                <div
                  style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}
                >
                  {compareTsProfiles.slice(0, 2).map((profile) => (
                    <div
                      key={profile.profileId}
                      style={{ flex: "1 1 260px", minWidth: "260px" }}
                    >
                      <PlotProfileTool
                        profiles={[profile]}
                        profileId={profile.profileId}
                        xKey="salinity"
                        yKey="temperature"
                        xLabel={`Salinity (PSU) – ${
                          profile.label || profile.profileId
                        }`}
                        yLabel="Temperature (°C)"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
