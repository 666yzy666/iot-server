const BASE = "/api/auth";

async function postAuth(path, payload) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "认证失败");
  }
  return data;
}

export function login(username, password) {
  return postAuth("/login", { username, password });
}

export function register(username, password, displayName = "") {
  return postAuth("/register", { username, password, display_name: displayName });
}

export async function fetchMe() {
  const res = await fetch(`${BASE}/me`, { credentials: "same-origin", cache: "no-store" });
  if (!res.ok) throw new Error("未登录");
  return res.json();
}

export async function logout() {
  await fetch(`${BASE}/logout`, {
    method: "POST",
    credentials: "same-origin",
  });
}
