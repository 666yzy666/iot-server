<template>
  <div class="layout">
    <header class="topbar">
      <div class="topbar-left">
        <h1 class="gradient-text">Vitam 设备监控</h1>
        <p class="subtitle">实时监控 · IoT 设备管理面板</p>
      </div>
      <div class="topbar-right">
        <span class="conn-status">
          <span class="status-dot" :class="{ off: connOffline }"></span>
          <span class="conn-label">{{ connOffline ? '离线' : '在线' }}</span>
        </span>
        <span class="time-display">{{ now }}</span>
      </div>
    </header>

    <section class="stats">
      <StatCard :value="stats.total" label="设备总数" color="primary" />
      <StatCard :value="stats.online" label="在线" color="success" />
      <StatCard :value="stats.offline" label="离线" color="muted" />
      <StatCard :value="stats.ledOn" label="LED 开启" color="warning" />
    </section>

    <DeviceTable :items="items" />
  </div>
</template>

<script setup>
import { computed, provide, ref, onMounted, onUnmounted } from 'vue'
import StatCard from '../components/StatCard.vue'
import DeviceTable from '../components/DeviceTable.vue'
import { useDevices } from '../composables/useDevices.js'
import { useServiceInvoke } from '../composables/useServiceInvoke.js'

const { items, stats } = useDevices()
const { invoke, getResult } = useServiceInvoke()
provide("invokeService", invoke)
provide("getServiceResult", getResult)

const now = ref('')
const connOffline = ref(false)
let timeTimer

function updTime() {
  now.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  connOffline.value = stats.value.total > 0 && stats.value.online === 0
}
onMounted(() => { updTime(); timeTimer = setInterval(updTime, 1000) })
onUnmounted(() => { clearInterval(timeTimer) })
</script>

<style scoped>
.layout {
  max-width: 1120px;
  margin: 0 auto;
  padding: 28px 24px 48px;
  position: relative;
  z-index: 3;
}
.topbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 32px;
}
.gradient-text {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  background: var(--gradient);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientShift 4s ease infinite;
  margin: 0;
}
@keyframes gradientShift {
  0%,100% { background-position: 0% 50% }
  50% { background-position: 100% 50% }
}
.subtitle {
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 4px;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.conn-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 6px var(--success);
  animation: pulse 2s infinite;
}
.status-dot.off {
  background: var(--offline);
  box-shadow: none;
  animation: none;
}
@keyframes pulse {
  0%,100% { opacity: 1 }
  50% { opacity: 0.5 }
}
.time-display {
  font-size: 13px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
@media (max-width: 760px) {
  .layout { padding: 20px 14px 32px; }
  .gradient-text { font-size: 22px; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .topbar { flex-direction: column; align-items: flex-start; gap: 12px; }
}
</style>
