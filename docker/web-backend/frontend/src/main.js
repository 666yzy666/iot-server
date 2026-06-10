import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import DashboardView from "./views/DashboardView.vue";
import LoginView from "./views/LoginView.vue";
import { useAuth } from "./composables/useAuth.js";
import "./assets/main.css";

const routes = [
  { path: "/", name: "dashboard", component: DashboardView },
  { path: "/login", name: "login", component: LoginView },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuth();
  if (to.name !== "login" && !auth.isAuthenticated.value) {
    return { name: "login" };
  }
  if (to.name === "login" && auth.isAuthenticated.value) {
    return { name: "dashboard" };
  }
  return true;
});

createApp(App).use(router).mount("#app");
