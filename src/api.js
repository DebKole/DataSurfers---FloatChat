const API_BASE_URL = 'http://localhost:8000';

export async function fetchTsCurve(floatId, limit = 5) {
  const url = `${API_BASE_URL}/api/ts_curve?float_id=${encodeURIComponent(floatId)}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchTsCurveEnhanced(floatId, limit = 5) {
  const url = `${API_BASE_URL}/api/ts_curve_enhanced?float_id=${encodeURIComponent(floatId)}&limit=${limit}`;
  const res = await fetch(url);
  
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`HTTP ${res.status}: ${errorText || 'Failed to fetch TS curve'}`);
  }
  
  // Get the response as a blob
  const blob = await res.blob();
  
  // Convert the blob to a data URL
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export async function fetchTdCurve(floatId, limit = 200) {
  const url = `${API_BASE_URL}/api/td_curve?float_id=${encodeURIComponent(floatId)}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function compareTdCurves(floatIdA, floatIdB, limit = 200) {
  const url = `${API_BASE_URL}/api/compare_td?float_id_a=${encodeURIComponent(floatIdA)}&float_id_b=${encodeURIComponent(floatIdB)}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function compareTsCurves(floatIdA, floatIdB, limit = 200) {
  const url = `${API_BASE_URL}/api/compare_ts?float_id_a=${encodeURIComponent(floatIdA)}&float_id_b=${encodeURIComponent(floatIdB)}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
