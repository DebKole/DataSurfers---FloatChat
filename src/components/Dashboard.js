import React, { useState, useEffect, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
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
  const [floats, setFloats] = useState([]);
  const [floatSearch, setFloatSearch] = useState("");
  const [selectedFloat, setSelectedFloat] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [loadingFloats, setLoadingFloats] = useState(false);
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  const [error, setError] = useState(null);
  const [renderProfiles, setRenderProfiles] = useState({ ts: [], td: [], tp: [] });

  const location = useLocation();
  const initialFloatIds = location.state?.floatIds;

  useEffect(() => {
    const loadFloats = async () => {
      setLoadingFloats(true);
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/floats`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        let allFloats = data.floats || [];

        // Filter if initialFloatIds provided
        if (initialFloatIds && initialFloatIds.length > 0) {
          // Convert both to strings for comparison
          const allowed = new Set(initialFloatIds.map(String));
          allFloats = allFloats.filter(f => allowed.has(String(f)));

          // If we have filtered floats, automatically select the first one
          if (allFloats.length > 0) {
            // We can't call onSelectFloat here directly because it's defined below.
            // But we can set selectedFloat state.
            // However, onSelectFloat does more than just setting state (fetches profiles).
            // So we might need a separate effect or move onSelectFloat up.
            // For now, let's just filter the list. The user can click.
          }
        }

        setFloats(allFloats);
      } catch (e) {
        setError(e.message || String(e));
      } finally {
        setLoadingFloats(false);
      }
    };
    loadFloats();
  }, [initialFloatIds]);

  const filteredFloats = useMemo(() => {
    if (!floatSearch) return floats;
    return floats.filter((f) =>
      String(f).toLowerCase().includes(floatSearch.toLowerCase())
    );
  }, [floats, floatSearch]);

  const onSelectFloat = async (fid) => {
    setSelectedFloat(fid);
    setSelectedProfile(null);
    setRenderProfiles({ ts: [], td: [] });
    setLoadingProfiles(true);
    try {
      // 1. Fetch list of profiles for sidebar
      const res = await fetch(
        `http://127.0.0.1:8000/api/floats/${fid}/profiles`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list = (data.profiles || []).filter((p) => {
        const mc = p.measurement_count ?? p.MEASUREMENT_COUNT;
        return mc === undefined ? true : Number(mc) > 0;
      });
      setProfiles(list);

      // 2. Fetch TS Curve data for ALL cycles
      const tsRes = await fetch(
        `http://127.0.0.1:8000/api/analysis?type=ts_curve&float_id=${fid}`
      );
      const tsData = tsRes.ok ? await tsRes.json() : {};
      const tsProfiles = tsData?.analysis_result?.profiles || [];

      // 3. Fetch TD Curve data for ALL cycles
      const tdRes = await fetch(
        `http://127.0.0.1:8000/api/analysis?type=td_curve&float_id=${fid}`
      );
      const tdData = tdRes.ok ? await tdRes.json() : {};
      const tdProfiles = tdData?.analysis_result?.profiles || [];

      // 4. Fetch TP Curve data for ALL cycles (Temperature vs Pressure)
      const tpRes = await fetch(
        `http://127.0.0.1:8000/api/analysis?type=tp_curve&float_id=${fid}`
      );
      const tpData = tpRes.ok ? await tpRes.json() : {};
      const tpProfiles = tpData?.analysis_result?.profiles || [];

      setRenderProfiles({ ts: tsProfiles, td: tdProfiles, tp: tpProfiles });
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoadingProfiles(false);
    }
  };

  const onSelectProfile = (p) => {
    setSelectedProfile(p);
  };

  const handleClose = () => navigate(-1);

  // Determine the ID to filter by (if any)
  const activeCycle = selectedProfile?.cycle_number ?? selectedProfile?.CYCLE_NUMBER;

  const tsCard = (
    <div style={{ flex: "1 1 600px", minWidth: 400 }}>
      <div style={{ fontWeight: "bold", marginBottom: 4 }}>
        TS Curve {activeCycle ? `(Cycle ${activeCycle})` : "(All Cycles)"}
      </div>
      <PlotProfileTool
        profiles={renderProfiles.ts}
        profileId={activeCycle}
        xKey="salinity"
        yKey="temperature"
        xLabel="Salinity (PSU)"
        yLabel="Temperature (°C)"
      />
    </div>
  );

  const tdCard = (
    <div style={{ flex: "1 1 600px", minWidth: 400 }}>
      <div style={{ fontWeight: "bold", marginBottom: 4 }}>
        TD Profile {activeCycle ? `(Cycle ${activeCycle})` : "(All Cycles)"}
      </div>
      <PlotProfileTool
        profiles={renderProfiles.td}
        profileId={activeCycle}
        xKey="depth"
        yKey="temperature"
        xLabel="Depth (m)"
        yLabel="Temperature (°C)"
        invertY={true}
      />
    </div>
  );

  const tpCard = (
    <div style={{ flex: "1 1 600px", minWidth: 400 }}>
      <div style={{ fontWeight: "bold", marginBottom: 4 }}>
        Temperature vs Pressure {activeCycle ? `(Cycle ${activeCycle})` : "(All Cycles)"}
      </div>
      <PlotProfileTool
        profiles={renderProfiles.tp}
        profileId={activeCycle}
        xKey="temperature"
        yKey="pressure"
        xLabel="Temperature (°C)"
        yLabel="Pressure (dbar)"
        invertY={true}
      />
    </div>
  );

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: 320,
          borderRight: "1px solid rgba(255,255,255,0.1)",
          padding: 12,
          overflowY: "auto",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 12, color: '#e2e8f0' }}>Floats</div>
        <div className="search-float-container">
          <input
            type="text"
            value={floatSearch}
            onChange={(e) => setFloatSearch(e.target.value)}
            placeholder="Search float ID..."
            className="float-input-field"
            style={{
              paddingLeft: '36px',
              paddingbottom: '30px',
              marginbottom: '30px',
              background: 'rgba(26, 40, 65, 0.5)',
              color: '#e2e8f0',
              border: '1px solid rgba(49, 130, 206, 0.3)',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
            }}
          />
        </div>
        {loadingFloats ? (
          <div>Loading floats…</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {filteredFloats.map((fid) => (
              <button
                key={fid}
                className="view-more-btn"
                onClick={() => onSelectFloat(fid)}
              >
                {fid}
              </button>
            ))}
          </div>
        )}
      </div>
      <div
        style={{
          width: 360,
          borderRight: "1px solid rgba(255,255,255,0.1)",
          padding: 12,
          overflowY: "auto",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 8 }}>
          Profiles {selectedFloat ? `for ${selectedFloat}` : ""}
        </div>
        {loadingProfiles && <div>Loading profiles…</div>}
        {!loadingProfiles && profiles.length === 0 && (
          <div>No profiles with measurements were found for this float.</div>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {profiles.map((p, idx) => (
            <button
              key={idx}
              className="view-more-btn"
              onClick={() => onSelectProfile(p)}
            >
              Cycle {p.cycle_number ?? p.CYCLE_NUMBER ?? idx + 1} —{" "}
              {p.datetime ?? p.DATETIME ?? ""}
            </button>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, padding: 12, overflowY: "auto" }}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {renderProfiles.ts?.length > 0 && tsCard}
          {renderProfiles.td?.length > 0 && tdCard}
          {renderProfiles.tp?.length > 0 && tpCard}
        </div>
        {!renderProfiles.ts?.length &&
          !renderProfiles.td?.length &&
          !renderProfiles.tp?.length &&
          selectedFloat && (
            <div style={{ marginTop: 12, opacity: 0.85 }}>
              No charts to display yet for the selected float.
            </div>
          )}
      </div>
    </div>
  );
};

export default Dashboard;
