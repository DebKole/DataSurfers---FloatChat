import React, { useState, useEffect } from "react";
import "./FloatMetadata.css";

const FloatMetadata = ({ floatId }) => {
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("main");

  useEffect(() => {
    if (floatId) {
      fetchMetadata();
    }
  }, [floatId]);

  const fetchMetadata = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/floats/${floatId}/metadata`);
      if (res.ok) {
        const data = await res.json();
        setMetadata(data);
      }
    } catch (e) {
      console.error("Failed to fetch metadata:", e);
    } finally {
      setLoading(false);
    }
  };

  if (!floatId) {
    return (
      <div className="metadata-placeholder">
        Select a float to view its metadata
      </div>
    );
  }

  if (loading) {
    return <div className="metadata-loading">Loading metadata...</div>;
  }

  if (!metadata) {
    return <div className="metadata-error">Failed to load metadata</div>;
  }

  const { about, deployment, cycle } = metadata;

  return (
    <div className="float-metadata">
      <div className="metadata-tabs">
        <button
          className={`tab-btn ${activeTab === "main" ? "active" : ""}`}
          onClick={() => setActiveTab("main")}
        >
          MAIN INFORMATION
        </button>
        <button
          className={`tab-btn ${activeTab === "all" ? "active" : ""}`}
          onClick={() => setActiveTab("all")}
        >
          ALL METADATA
        </button>
      </div>

      <div className="metadata-content">
        {activeTab === "main" && (
          <>
            <div className="metadata-section">
              <h3 className="section-title">About Float</h3>
              <div className="metadata-grid">
                <MetadataItem label="WMO" value={about?.wmo || floatId} />
                <MetadataItem label="Platform maker" value={about?.platformMaker} />
                <MetadataItem label="Float serial number" value={about?.serialNumber} />
                <MetadataItem label="Platform type" value={about?.platformType} />
                <MetadataItem label="Transmission system" value={about?.transmissionSystem} />
                <MetadataItem label="PTT" value={about?.ptt} />
                <MetadataItem label="Owner" value={about?.owner} />
                <MetadataItem label="Data Centre" value={about?.dataCentre} />
                <MetadataItem label="Sensors" value={about?.sensors} />
              </div>
            </div>

            <div className="metadata-section">
              <h3 className="section-title">Deployment</h3>
              <div className="metadata-grid">
                <MetadataItem label="Launched" value={deployment?.launched} />
                <MetadataItem label="Deployment Latitude" value={deployment?.latitude} />
                <MetadataItem label="Deployment Longitude" value={deployment?.longitude} />
                <MetadataItem label="Ship" value={deployment?.ship} />
                <MetadataItem label="Cruise" value={deployment?.cruise} />
                <MetadataItem label="Project" value={deployment?.project} />
                <MetadataItem label="Principal Investigator" value={deployment?.principalInvestigator} />
              </div>
            </div>

            <div className="metadata-section">
              <h3 className="section-title">Cycle Activity</h3>
              <div className="metadata-grid">
                <MetadataItem label="Status" value={cycle?.status} highlight={cycle?.status === "Active"} />
                <MetadataItem label="Age" value={cycle?.age} />
                <MetadataItem label="Last profile date" value={cycle?.lastProfileDate} />
                <MetadataItem label="Cycle" value={cycle?.cycleNumber} />
                <MetadataItem label="Last Surface Data" value={cycle?.lastSurfaceData} />
                <MetadataItem label="Last Bottom Data" value={cycle?.lastBottomData} />
              </div>
            </div>
          </>
        )}

        {activeTab === "all" && (
          <div className="metadata-section">
            <h3 className="section-title">All Metadata</h3>
            <div className="metadata-list">
              {Object.entries(metadata.raw || {}).map(([key, value]) => (
                <div key={key} className="metadata-row">
                  <span className="metadata-key">{key}</span>
                  <span className="metadata-value">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const MetadataItem = ({ label, value, highlight }) => (
  <div className="metadata-item">
    <div className="metadata-label">{label}</div>
    <div className={`metadata-value ${highlight ? "highlight" : ""}`}>
      {value || "N/A"}
    </div>
  </div>
);

export default FloatMetadata;
