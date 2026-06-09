const BASE = "/api/devices";

export async function fetchDevices() {
  const res = await fetch(BASE, { cache: "no-store" });
  if (!res.ok) throw new Error(`fetch devices: ${res.status}`);
  return res.json();
}

export async function invokeDeviceService(deviceId, serviceId) {
  const res = await fetch(`${BASE}/${encodeURIComponent(deviceId)}/services/${serviceId}/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    throw new Error(data.detail || data.emqx_message || "publish failed");
  }
  return data;
}
