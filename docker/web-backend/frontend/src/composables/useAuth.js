import { computed, ref } from "vue";
import { login as loginApi, register as registerApi } from "../api/authApi.js";

const STORAGE_KEY = "vitam_auth";
const token = ref("");
const user = ref(null);

function loadAuth() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    token.value = saved.access_token || "";
    user.value = saved.user || null;
  } catch {
    localStorage.removeItem(STORAGE_KEY);
  }
}

function saveAuth(data) {
  token.value = data.access_token;
  user.value = data.user;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

loadAuth();

export function useAuth() {
  async function login(username, password) {
    const data = await loginApi(username, password);
    saveAuth(data);
    return data;
  }

  async function register(username, password, displayName) {
    const data = await registerApi(username, password, displayName);
    saveAuth(data);
    return data;
  }

  function logout() {
    token.value = "";
    user.value = null;
    localStorage.removeItem(STORAGE_KEY);
  }

  return {
    token,
    user,
    isAuthenticated: computed(() => Boolean(token.value)),
    login,
    register,
    logout,
  };
}

export function authHeaders() {
  return token.value ? { Authorization: `Bearer ${token.value}` } : {};
}
