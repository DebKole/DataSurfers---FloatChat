const API_BASE_URL = "http://192.168.1.10:8000";

export async function pingBackend() {
  const url = `${API_BASE_URL}/`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function sendChatMessage(query) {
  const url = `${API_BASE_URL}/`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchTsCurve(floatId) {
  const url = `${API_BASE_URL}/api/ts_curve?float_id=${encodeURIComponent(floatId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function getTsCurvePngUrl(floatId) {
  return `${API_BASE_URL}/api/ts_curve_png?float_id=${encodeURIComponent(floatId)}`;
}

export async function fetchTdCurve(floatId) {
  const url = `${API_BASE_URL}/api/td_curve?float_id=${encodeURIComponent(floatId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function getTdCurvePngUrl(floatId) {
  return `${API_BASE_URL}/api/td_curve_png?float_id=${encodeURIComponent(floatId)}`;
}

export async function fetchIndianOceanFloats(limit = 50) {
  const url = `${API_BASE_URL}/floats/indian-ocean?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchCompareTs(floatIdA, floatIdB, limit = 200) {
  const url = `${API_BASE_URL}/api/compare_ts?float_id_a=${encodeURIComponent(floatIdA)}&float_id_b=${encodeURIComponent(floatIdB)}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchCompareTd(floatIdA, floatIdB, limit = 200) {
  const url = `${API_BASE_URL}/api/compare_td?float_id_a=${encodeURIComponent(floatIdA)}&float_id_b=${encodeURIComponent(floatIdB)}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function getCompareTsPngUrl(floatIdA, floatIdB, limit = 200) {
  return `${API_BASE_URL}/api/compare_ts_png?float_id_a=${encodeURIComponent(floatIdA)}&float_id_b=${encodeURIComponent(floatIdB)}&limit=${limit}`;
}

export function getCompareTdPngUrl(floatIdA, floatIdB, limit = 200) {
  return `${API_BASE_URL}/api/compare_td_png?float_id_a=${encodeURIComponent(floatIdA)}&float_id_b=${encodeURIComponent(floatIdB)}&limit=${limit}`;
}

export function getFloatsPngUrl(limit = 50) {
  return `${API_BASE_URL}/floats/indian-ocean-png?limit=${limit}`;
}

export async function fetchTrajectoriesInRadius(lat, lon, radius = 2000, limit = 100) {
  const url = `${API_BASE_URL}/floats/trajectories/radius?lat=${lat}&lon=${lon}&radius=${radius}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
