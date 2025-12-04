import React, { useState, useEffect, useMemo } from "react";
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
  const [floats, setFloats] = useState([]);
  const [floatSearch, setFloatSearch] = useState("");
  const [selectedFloat, setSelectedFloat] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [loadingFloats, setLoadingFloats] = useState(false);
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  const [error, setError] = useState(null);
  const [renderProfiles, setRenderProfiles] = useState({ ts: [], td: [] });

  useEffect(() => {
    const loadFloats = async () => {
      setLoadingFloats(true);
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/floats`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setFloats(data.floats || []);
      } catch (e) {
        setError(e.message || String(e));
      } finally {
        setLoadingFloats(false);
      }
    };
    loadFloats();
  }, []);

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
      const firstTen = list.slice(0, 10);
      const tsAll = [];
      const tdAll = [];
      for (const p of firstTen) {
        const cycle = p.cycle_number || p.CYCLE_NUMBER;
        const tsRes = await fetch(
          `http://127.0.0.1:8000/api/analysis?type=ts_curve&float_id=${fid}${
            cycle !== undefined ? `&cycle_number=${cycle}` : ""
          }`
        );
        if (tsRes.ok) {
          const tsData = await tsRes.json();
          const tsProfiles = tsData?.analysis_result?.profiles || [];
          if (tsProfiles.length) tsAll.push({ profile: p, data: tsProfiles });
        }
        const tdRes = await fetch(
          `http://127.0.0.1:8000/api/analysis?type=td_curve&float_id=${fid}${
            cycle !== undefined ? `&cycle_number=${cycle}` : ""
          }`
        );
        if (tdRes.ok) {
          const tdData = await tdRes.json();
          const tdProfiles = tdData?.analysis_result?.profiles || [];
          if (tdProfiles.length) tdAll.push({ profile: p, data: tdProfiles });
        }
      }
      setRenderProfiles({ ts: tsAll, td: tdAll });
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoadingProfiles(false);
    }
  };

  const onSelectProfile = async (p) => {
    setSelectedProfile(p);
    if (!selectedFloat || !p) return;
    const cycle = p.cycle_number || p.CYCLE_NUMBER;
    try {
      const tsRes = await fetch(
        `http://127.0.0.1:8000/api/analysis?type=ts_curve&float_id=${selectedFloat}${
          cycle !== undefined ? `&cycle_number=${cycle}` : ""
        }`
      );
      const tdRes = await fetch(
        `http://127.0.0.1:8000/api/analysis?type=td_curve&float_id=${selectedFloat}${
          cycle !== undefined ? `&cycle_number=${cycle}` : ""
        }`
      );
      const tsData = tsRes.ok ? await tsRes.json() : {};
      const tdData = tdRes.ok ? await tdRes.json() : {};
      const tsProfiles = tsData?.analysis_result?.profiles || [];
      const tdProfiles = tdData?.analysis_result?.profiles || [];
      setRenderProfiles({
        ts: tsProfiles.length ? [{ profile: p, data: tsProfiles }] : [],
        td: tdProfiles.length ? [{ profile: p, data: tdProfiles }] : [],
      });
    } catch (e) {
      setError(e.message || String(e));
    }
  };

  const handleClose = () => navigate(-1);

  const tsCards = (selectedProfile ? renderProfiles.ts : renderProfiles.ts).map(
    (entry, idx) => (
      <div key={`ts-${idx}`} style={{ flex: "1 1 300px", minWidth: 300 }}>
        <div style={{ fontWeight: "bold", marginBottom: 4 }}>
          TS Curve{" "}
          {entry.profile?.cycle_number ?? entry.profile?.CYCLE_NUMBER ?? ""}
        </div>
        <PlotProfileTool
          profiles={entry.data}
          profileId={entry.data[0]?.profileId || 1}
          xKey="salinity"
          yKey="temperature"
          xLabel="Salinity (PSU)"
          yLabel="Temperature (°C)"
        />
      </div>
    )
  );

  const tdCards = (selectedProfile ? renderProfiles.td : renderProfiles.td).map(
    (entry, idx) => (
      <div key={`td-${idx}`} style={{ flex: "1 1 300px", minWidth: 300 }}>
        <div style={{ fontWeight: "bold", marginBottom: 4 }}>
          TD Profile{" "}
          {entry.profile?.cycle_number ?? entry.profile?.CYCLE_NUMBER ?? ""}
        </div>
        <PlotProfileTool
          profiles={entry.data}
          profileId={entry.data[0]?.profileId || 1}
          xKey="depth"
          yKey="temperature"
          xLabel="Depth (m)"
          yLabel="Temperature (°C)"
          invertY={true}
        />
      </div>
    )
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
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Floats</div>
        <input
          type="text"
          value={floatSearch}
          onChange={(e) => setFloatSearch(e.target.value)}
          placeholder="Search float"
          style={{ width: "100%", marginBottom: 8 }}
        />
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
          {tsCards}
        </div>
        <div style={{ height: 12 }} />
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {tdCards}
        </div>
        {!renderProfiles.ts.length &&
          !renderProfiles.td.length &&
          selectedFloat && (
            <div style={{ marginTop: 12, opacity: 0.85 }}>
              No charts to display yet for the selected float/profile. Try
              choosing a different profile.
            </div>
          )}
      </div>
    </div>
  );
};

export default Dashboard;
