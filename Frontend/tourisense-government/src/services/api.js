export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api";
export const getAdminToken = () => localStorage.getItem("tourisense-token") || localStorage.getItem("wanderly-token");

export async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getAdminToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  let body = {};
  try { body = await response.json(); } catch { /* endpoint returned an empty/non-JSON body */ }
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status}).`);
  return body;
}
