import React, { useState, useMemo, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import "./DataSidebar.css";
import MapVisualization from "./MapVisualization";
import PlotProfileTool from "./PlotProfile";
import CompareProfilesTool from "./CompareProfilesTool";
import MapTrajectories from "./MapTrajectories";

const profiles = [];
const trajectories = [];

const DataSidebar = ({
  selectedView = "table",
  onViewChange,
  mapData = null,
  showMap = false,
  onMapClose = () => {},
  tableData = null,
  onOpenTrajectoryOverlay = () => {},
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [isMapVisible, setIsMapVisible] = useState(false);
  const [showFullTable, setShowFullTable] = useState(false);

  // Advanced preview states
  const [showProfilePreview, setShowProfilePreview] = useState(false);
  const [selectedFloatId, setSelectedFloatId] = useState("");
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [compareProfileId1, setCompareProfileId1] = useState(null);
  const [compareProfileId2, setCompareProfileId2] = useState(null);
  const [variable, setVariable] = useState("TEMP");

  const navigate = useNavigate();

  // Memoized float -> profiles mapping
  const floatToProfiles = useMemo(() => {
    const map = new Map();
    trajectories.forEach((pt) => {
      if (!pt.floatId || pt.profileId == null) return;
      const key = String(pt.floatId);
      if (!map.has(key)) map.set(key, new Set());
      map.get(key).add(pt.profileId);
    });
    const result = {};
    map.forEach((set, key) => {
      result[key] = Array.from(set);
    });
    return result;
  }, []); // trajectories is static for now

  const floatOptions = useMemo(
    () => Object.keys(floatToProfiles).sort(),
    [floatToProfiles]
  );

  const profileOptionsForSelectedFloat = useMemo(() => {
    if (!selectedFloatId) return [];
    const ids = floatToProfiles[String(selectedFloatId)] || [];
    return profiles.filter((p) => ids.includes(p.profileId));
  }, [selectedFloatId, floatToProfiles]);

  // Toggle sidebar
  const toggleSidebar = () => setCollapsed((prev) => !prev);

  // Handle view change
  const handleViewChange = (e) => {
    const newView = e.target.value;
    onViewChange?.(newView);
  };

  // Export CSV
  const handleExportCSV = useCallback(() => {
    if (!tableData?.columns || !tableData?.rows) return;

    const esc = (val) => {
      if (val === null || val === undefined) return "";
      const s = String(val);
      return s.includes('"') || s.includes(",") || s.includes("\n")
        ? `"${s.replace(/"/g, '""')}"`
        : s;
    };

    const header = tableData.columns.map(esc).join(",");
    const body = tableData.rows
      .map((row) => tableData.columns.map((col) => esc(row[col])).join(","))
      .join("\n");

    const csv = header + "\n" + body;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "floatchat_data.csv";
    a.click();
    URL.revokeObjectURL(url);
  }, [tableData]);

  // Open full map page
  const handleOpenMap = () => {
    navigate("/map", {
      state: { mapData, source: "sidebar" },
    });
  };

  // Close inline map
  const handleCloseMap = () => {
    setIsMapVisible(false);
    onMapClose();
  };

  // Auto-open map when showMap prop is true
  useEffect(() => {
    if (showMap && mapData) {
      setIsMapVisible(true);
      onViewChange?.("map");
    }
  }, [showMap, mapData, onViewChange]);

  // Close full table on Escape key
  useEffect(() => {
    if (!showFullTable) return;

    const handleEsc = (e) => {
      if (e.key === "Escape") {
        setShowFullTable(false);
      }
    };

    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [showFullTable]);

  return (
    <aside
      className={`data-sidebar ${collapsed ? "collapsed" : ""}`}
      id="rightSidebar"
      aria-label="Data overview sidebar"
    >
      <div className="data-header">
        <i className="fas fa-chart-line" aria-hidden="true"></i>
        <h2>Data Overview</h2>
      </div>

      <button
        className="collapse-btn right-toggle"
        onClick={toggleSidebar}
        aria-expanded={!collapsed}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <i
          className={`fas ${
            collapsed ? "fa-chevron-left" : "fa-chevron-right"
          }`}
          aria-hidden="true"
        ></i>
      </button>

      {/* View Selector */}
      <div className={`view-selector ${collapsed ? "hidden" : ""}`}>
        <select
          value={selectedView}
          onChange={handleViewChange}
          className="view-dropdown"
        >
          <option value="map">Map</option>
          <option value="table">Table</option>
          {/* <option value="updates">Latest Updates</option> */}
        </select>
      </div>

      {/* Collapsed Icons */}
      {collapsed && (
        <div className="collapsed-view-icons">
          <div className="collapsed-icon" title="Map">
            <i className="fas fa-map"></i>
          </div>
          <div className="collapsed-icon" title="Table">
            <i className="fas fa-table"></i>
          </div>
          
          {/* <div className="collapsed-icon" title="Latest Updates">
            <i className="fas fa-clock"></i>
          </div> */}
        </div>
      )}

      {/* Table View */}
      {selectedView === "table" && (
        <div className="data-card">
          <h3>
            <i className="fas fa-table"></i> Table
          </h3>
          <div className="table-preview">
            {tableData?.columns && tableData?.rows?.length > 0 ? (
              <>
                <div className="table-row header">
                  {tableData.columns.slice(0, 5).map((col) => (
                    <span key={col} title={col}>
                      {col.length > 12 ? col.substring(0, 12) + "..." : col}
                    </span>
                  ))}
                </div>
                {tableData.rows.slice(0, 10).map((row, i) => (
                  <div className="table-row" key={i}>
                    {tableData.columns.slice(0, 5).map((col) => {
                      const value = row[col];
                      const display =
                        value == null
                          ? "-"
                          : typeof value === "number"
                          ? value.toFixed(2)
                          : String(value).length > 15
                          ? String(value).substring(0, 15) + "..."
                          : String(value);
                      return (
                        <span key={col} title={String(value ?? "")}>
                          {display}
                        </span>
                      );
                    })}
                  </div>
                ))}
              </>
            ) : (
              <div className="no-data-message">
                <i className="fas fa-inbox"></i>
                <p>No data available</p>
                <small>Run a query to see results</small>
              </div>
            )}
          </div>

          <div className="view-more">
            {tableData?.total_rows > 0 && (
              <div className="data-stats">
                <small>
                  Showing {Math.min(10, tableData.rows.length)} of{" "}
                  {tableData.total_rows} rows
                </small>
              </div>
            )}
            <button
              className="view-more-btn"
              disabled={!tableData?.total_rows}
              onClick={() => setShowFullTable(true)}
            >
              View Full Table
            </button>
            <button
              className="view-more-btn"
              disabled={!tableData?.total_rows}
              onClick={handleExportCSV}
            >
              Export as CSV
            </button>
          </div>
        </div>
      )}

      {/* Map View */}
      {selectedView === "map" && (
        <div className="data-card">
          <h3>
            <i className="fas fa-map"></i> Map
          </h3>
          <div className="map-preview">
            <div className="map-placeholder">
              {/* <i className="fas fa-globe"></i>
              <p>Interactive Ocean Map</p> */}
              <div className="map-stats">
                {mapData ? (
                  <>
                    <span>{mapData.map_data?.length || 0} Data Points</span>
                    <span>
                      {(mapData.parameter || "temperature")
                        .charAt(0)
                        .toUpperCase() +
                        (mapData.parameter || "temperature").slice(1)}{" "}
                      Data
                    </span>
                    <span>
                      {(mapData.region || "current_location")
                        .replace(/_/g, " ")
                        .replace(/\b\w/g, (l) => l.toUpperCase())}
                    </span>
                  </>
                ) : (
                  <>
                    {/* <span>No map data</span>
                    <span>Ocean Region</span> */}
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="view-more">
            <button className="view-more-btn has-data" onClick={handleOpenMap}>
              {mapData ? "View Data Map" : "Open Map View"}
            </button>
          </div>

          <div className="view-more" style={{ marginTop: "0.5rem" }}>
            <button className="view-more-btn" onClick={onOpenTrajectoryOverlay}>
              Open Trajectory Map
            </button>
          </div>

          <div
            style={{
              marginTop: "1rem",
              minHeight: 520,
              border: "1px solid #333",
              borderRadius: 8,
              overflow: "hidden",
            }}
          >
            <MapTrajectories />
          </div>
        </div>
      )}

      {/* Updates View */}
      {/* {selectedView === "updates" && (
        <div className="data-card">
          <h3>
            <i className="fas fa-clock"></i> Latest Updates
          </h3>
          <div className="update-list"> */}
            {/* Your update items here */}
            {/* <div className="update-item">
              <div className="update-time">2 min ago</div>
              <div className="update-text">New data from Float 4902916</div>
            </div> */}
            {/* ... more items */}
          {/* </div>
          <div className="view-more">
            <button className="view-more-btn">View All Updates</button>
          </div>
        </div> */}
      {/* )}  */}

      {/* Inline Map Modal */}
      <MapVisualization
        mapData={mapData?.map_data}
        isVisible={isMapVisible}
        onClose={handleCloseMap}
        queryType={mapData?.query_type || "general"}
        parameter={mapData?.parameter || "temperature"}
      />

      {/* Full Table Modal via Portal */}
      {showFullTable &&
        createPortal(
          <div
            className="modal-backdrop"
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0,0,0,0.8)",
              backdropFilter: "blur(8px)",
              zIndex: 99999,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            onClick={(e) =>
              e.target === e.currentTarget && setShowFullTable(false)
            }
          >
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Full data table"
              style={{
                background: "#0f1b2e",
                color: "#fff",
                width: "95vw",
                height: "95vh",
                borderRadius: 12,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
              }}
            >
              <div
                style={{
                  padding: "12px 20px",
                  borderBottom: "1px solid rgba(255,255,255,0.1)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexShrink: 0,
                }}
              >
                <h3 style={{ margin: 0, fontSize: 20 }}>
                  <i className="fas fa-table" style={{ marginRight: 10 }}></i>
                  Full Table View
                </h3>
                <div>
                  <button
                    className="view-more-btn"
                    onClick={handleExportCSV}
                    style={{ marginRight: 10 }}
                  >
                    Export CSV
                  </button>
                  <button
                    className="view-more-btn"
                    onClick={() => setShowFullTable(false)}
                  >
                    Close
                  </button>
                </div>
              </div>

              <div style={{ flex: 1, overflow: "auto", padding: 16 }}>
                {tableData?.columns && tableData?.rows?.length > 0 ? (
                  <div className="full-table">
                    <div
                      className="table-row header"
                      style={{
                        position: "sticky",
                        top: 0,
                        background: "#0f1b2e",
                        zIndex: 10,
                      }}
                    >
                      {tableData.columns.map((col) => (
                        <span key={col} style={{ fontWeight: 600 }}>
                          {col}
                        </span>
                      ))}
                    </div>
                    {tableData.rows.slice(0, 5000).map((row, i) => (
                      <div className="table-row" key={i}>
                        {tableData.columns.map((col) => (
                          <span key={col} title={String(row[col] ?? "")}>
                            {row[col] != null ? String(row[col]) : "-"}
                          </span>
                        ))}
                      </div>
                    ))}
                    {tableData.rows.length > 5000 && (
                      <div
                        style={{
                          padding: "16px",
                          textAlign: "center",
                          opacity: 0.7,
                        }}
                      >
                        Showing first 5,000 rows. Use "Export CSV" for all{" "}
                        {tableData.rows.length} rows.
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="no-data-message">
                    <p>No data to display</p>
                  </div>
                )}
              </div>
            </div>
          </div>,
          document.body
        )}
    </aside>
  );
};

export default DataSidebar;
