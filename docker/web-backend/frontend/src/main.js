import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import DashboardView from "./views/DashboardView.vue";
import "./assets/main.css";

const routes = [
  { path: "/", name: "dashboard", component: DashboardView },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

createApp(App).use(router).mount("#app");
