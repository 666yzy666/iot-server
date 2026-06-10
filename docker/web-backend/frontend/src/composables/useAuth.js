import { computed, ref } from "vue";
import { fetchMe, login as loginApi, logout as logoutApi, register as registerApi } from "../api/authApi.js";

const STORAGE_KEY = "vitam_auth";
const user = ref(null);

function loadAuth() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    user.value = saved.user || null;
  } catch {
    localStorage.removeItem(STORAGE_KEY);
  }
}

function saveAuth(data) {
  user.value = data.user;
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ user: data.user }));
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

  async function refreshMe() {
    const profile = await fetchMe();
    user.value = profile;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ user: profile }));
    return profile;
  }

  async function logout() {
    await logoutApi();
    user.value = null;
    localStorage.removeItem(STORAGE_KEY);
  }

  return {
    user,
    isAuthenticated: computed(() => Boolean(user.value)),
    login,
    register,
    refreshMe,
    logout,
  };
}

export function authHeaders() {
  return {};
}
