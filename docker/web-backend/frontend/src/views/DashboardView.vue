<template>
  <main class="shell">
    <header class="topbar">
      <div class="brand">
        <h1>Vitam 设备监控</h1>
        <p>点击设备行展开控制服务</p>
      </div>
      <div class="refresh">每 5 秒自动刷新</div>
    </header>

    <section class="stats">
      <StatCard :value="stats.total" label="设备总数" />
      <StatCard :value="stats.online" label="在线设备" />
      <StatCard :value="stats.offline" label="离线设备" />
      <StatCard :value="stats.ledOn" label="LED 开启" />
    </section>

    <DeviceTable :items="items" />
  </main>
</template>

<script setup>
import { provide } from "vue";
import StatCard from "../components/StatCard.vue";
import DeviceTable from "../components/DeviceTable.vue";
import { useDevices } from "../composables/useDevices.js";
import { useServiceInvoke } from "../composables/useServiceInvoke.js";

const { items, stats } = useDevices();
const { invoke, getResult } = useServiceInvoke();

provide("invokeService", invoke);
provide("getServiceResult", getResult);
</script>

<style scoped>
.shell { max-width: 1120px; margin: 0 auto; padding: 28px 20px 48px; }
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}
.brand h1 { margin: 0; font-size: 28px; }
.brand p { margin: 6px 0 0; color: var(--muted); }
.refresh { color: var(--muted); font-size: 13px; }
.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}
@media (max-width:760px) {
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
