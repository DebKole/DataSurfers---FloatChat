const API_BASE_URL = "http://192.168.29.129:8000";

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

export async function fetchIndianOceanFloats(limit = 50) {
  const url = `${API_BASE_URL}/floats/indian-ocean?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
