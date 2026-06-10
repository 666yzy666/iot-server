const BASE = "/api/auth";

async function postAuth(path, payload) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
