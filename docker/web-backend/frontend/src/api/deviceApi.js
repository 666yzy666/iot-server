import { authHeaders } from "../composables/useAuth.js";

const BASE = "/api/devices";

export async function fetchDevices() {
  const res = await fetch(BASE, { cache: "no-store", headers: authHeaders() });
  if (!res.ok) throw new Error(`fetch devices: ${res.status}`);
  return res.json();
}

export async function fetchDeviceHistory(deviceId) {
  const res = await fetch(`${BASE}/${encodeURIComponent(deviceId)}/history`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`fetch history: ${res.status}`);
  return res.json();
}

export async function invokeDeviceService(deviceId, serviceId) {
  const res = await fetch(`${BASE}/${encodeURIComponent(deviceId)}/services/${serviceId}/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({}),
  });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    throw new Error(data.detail || data.emqx_message || "publish failed");
  }
  return data;
}
