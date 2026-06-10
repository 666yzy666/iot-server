<template>
  <div class="layout">
    <header class="topbar">
      <div class="topbar-left">
        <h1 class="gradient-text">Vitam 设备监控</h1>
        <p class="subtitle">实时监控 · IoT 设备管理面板</p>
      </div>
      <div class="topbar-right">
        <span class="user-chip">{{ auth.user.value?.display_name || auth.user.value?.username }}</span>
        <span class="conn-status">
          <span class="status-dot" :class="{ off: connOffline }"></span>
          <span class="conn-label">{{ connOffline ? '离线' : '在线' }}</span>
        </span>
        <span class="time-display">{{ now }}</span>
        <button class="logout-btn" @click="logout">退出</button>
      </div>
    </header>

    <section class="stats">
      <StatCard :value="stats.total" label="设备总数" color="primary" />
      <StatCard :value="stats.online" label="在线" color="success" />
      <StatCard :value="stats.offline" label="离线" color="muted" />
      <StatCard :value="stats.ledOn" label="LED 开启" color="warning" />
    </section>

    <form class="bind-bar" @submit.prevent="submitBind">
      <div class="bind-copy">
        <strong>绑定设备</strong>
        <span>输入已上报入库的设备 ID</span>
      </div>
      <input v-model.trim="bindDeviceId" placeholder="例如 dev_001" />
      <button :disabled="bindLoading">{{ bindLoading ? '绑定中' : '绑定' }}</button>
      <span v-if="bindMessage" class="bind-message" :class="{ error: bindError }">{{ bindMessage }}</span>
    </form>

    <DeviceTable :items="items" />
  </div>
</template>

<script setup>
import { computed, provide, ref, onMounted, onUnmounted } from 'vue'
import StatCard from '../components/StatCard.vue'
import DeviceTable from '../components/DeviceTable.vue'
import { useDevices } from '../composables/useDevices.js'
import { useServiceInvoke } from '../composables/useServiceInvoke.js'
import { useAuth } from '../composables/useAuth.js'
import { bindDevice } from '../api/deviceApi.js'
import { useRouter } from 'vue-router'

const { items, stats, reload } = useDevices()
const { invoke, getResult } = useServiceInvoke()
const auth = useAuth()
const router = useRouter()
provide("invokeService", invoke)
provide("getServiceResult", getResult)

const now = ref('')
const connOffline = ref(false)
const bindDeviceId = ref('')
const bindLoading = ref(false)
const bindMessage = ref('')
const bindError = ref(false)
let timeTimer

function updTime() {
  now.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  connOffline.value = stats.value.total > 0 && stats.value.online === 0
}
function logout() {
  auth.logout().finally(() => router.replace('/login'))
}
async function submitBind() {
  bindMessage.value = ''
  bindError.value = false
  if (!bindDeviceId.value) {
    bindMessage.value = '请输入设备 ID'
    bindError.value = true
    return
  }
  bindLoading.value = true
  try {
    await bindDevice(bindDeviceId.value)
    bindMessage.value = '绑定成功'
    bindDeviceId.value = ''
    await reload()
  } catch (err) {
    bindMessage.value = err.message || '绑定失败'
    bindError.value = true
  } finally {
    bindLoading.value = false
  }
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
.user-chip {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 5px 9px;
  font-size: 12px;
}
.logout-btn {
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  cursor: pointer;
}
.logout-btn:hover {
  color: var(--text-primary);
  border-color: var(--primary);
}
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
.bind-bar {
  display: grid;
  grid-template-columns: minmax(150px, 1fr) minmax(180px, 260px) auto minmax(90px, auto);
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.bind-copy {
  display: grid;
  gap: 2px;
}
.bind-copy strong {
  font-size: 14px;
}
.bind-copy span,
.bind-message {
  color: var(--text-muted);
  font-size: 12px;
}
.bind-bar input {
  min-width: 0;
  border: 1px solid var(--border);
  background: var(--bg-body);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  padding: 9px 10px;
  outline: none;
}
.bind-bar input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
}
.bind-bar button {
  border: 1px solid var(--primary);
  background: var(--primary);
  color: white;
  border-radius: var(--radius-sm);
  padding: 9px 14px;
  cursor: pointer;
  font-weight: 700;
}
.bind-bar button:disabled {
  opacity: 0.65;
  cursor: wait;
}
.bind-message.error {
  color: var(--danger);
}
@media (max-width: 760px) {
  .layout { padding: 20px 14px 32px; }
  .gradient-text { font-size: 22px; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .topbar { flex-direction: column; align-items: flex-start; gap: 12px; }
  .bind-bar { grid-template-columns: 1fr; }
}
</style>
