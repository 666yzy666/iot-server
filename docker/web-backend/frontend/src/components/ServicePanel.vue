<template>
  <div class="svc-panel">
    <!-- Service Cards -->
    <div class="svc-grid">
      <div class="svc-card" v-for="svc in serviceList" :key="svc.id">
        <div class="svc-info">
          <div class="svc-name">{{ svc.name }}</div>
          <div class="svc-desc">{{ svc.desc }}</div>
          <div class="svc-mono">service_id = {{ svc.id }}</div>
        </div>
        <button class="invoke-btn" @click.stop="doInvoke(svc.id, $event.currentTarget)" :disabled="sending === svc.id">
          {{ sending === svc.id ? '发送中…' : '发布' }}
        </button>
      </div>
    </div>

    <!-- Request Log -->
    <div class="log-section" v-if="requestLog.length">
      <div class="log-head">
        <span>请求日志</span>
        <button class="ghost-btn" @click.stop="clearLog">清除</button>
      </div>
      <div class="log-list">
        <div class="log-row" v-for="(entry, i) in requestLog" :key="i">
          <span class="log-time">{{ entry.time }}</span>
          <span class="log-svc">{{ entry.serviceId }}</span>
          <span class="log-status" :class="entry.status">{{ entry.status === 'ok' ? '成功' : '失败' }}</span>
          <span class="log-msg">{{ entry.message }}</span>
        </div>
      </div>
    </div>

    <!-- History -->
    <div class="history">
      <div class="history-head">
        <span>最近上报</span>
        <button class="ghost-btn" @click.stop="loadHistory">刷新</button>
      </div>
      <div v-if="historyError" class="history-empty">{{ historyError }}</div>
      <div v-else-if="historyItems.length" class="history-list">
        <div class="history-row" v-for="item in historyItems" :key="item.created_at + item.topic">
          <span class="h-time">{{ item.created_at ? new Date(item.created_at).toLocaleString('zh-CN') : '-' }}</span>
          <span class="h-topic">{{ item.topic }}</span>
        </div>
      </div>
      <div v-else class="history-empty">暂无上报记录</div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { fetchDeviceHistory } from '../api/deviceApi.js'

const props = defineProps({
  deviceId: { type: String, required: true },
  services: { type: Array, default: () => [] },
})
const serviceList = computed(() =>
  props.services.length
    ? props.services
    : [
        { id: 'get_status', name: '查询状态', desc: '触发设备上报最新属性' },
        { id: 'reboot', name: '重启设备', desc: '设备回复后延迟重启' },
      ]
)
const invoke = inject('invokeService')
const getResult = inject('getServiceResult')
const historyItems = ref([])
const historyError = ref('')
const sending = ref('')
const requestLog = ref([])

function nowStr() {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

async function doInvoke(svcId, btn) {
  sending.value = svcId
  const time = nowStr()
  requestLog.value.unshift({ time, serviceId: svcId, status: 'sending', message: '正在发送...' })
  try {
    await invoke(props.deviceId, svcId, btn)
    const r = getResult(props.deviceId, svcId)
    if (r) {
      requestLog.value[0].status = r.status === 'ok' ? 'ok' : 'err'
      requestLog.value[0].message = r.message
    }
  } catch (e) {
    requestLog.value[0].status = 'err'
    requestLog.value[0].message = e.message || '请求失败'
  }
  sending.value = ''
}

function clearLog() { requestLog.value = [] }

async function loadHistory() {
  historyError.value = ''
  try {
    const data = await fetchDeviceHistory(props.deviceId)
    historyItems.value = data.items || []
  } catch (e) { historyError.value = e.message || '加载失败' }
}
onMounted(loadHistory)
watch(() => props.deviceId, loadHistory)
</script>

<style scoped>
.svc-panel { padding: 20px; }
.svc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-bottom: 14px; }
.svc-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  transition: border-color var(--transition);
}
.svc-card:hover { border-color: var(--primary); }
.svc-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.svc-desc { color: var(--text-muted); font-size: 12px; margin-top: 4px; }
.svc-mono { font-size: 11px; font-family: ui-monospace, monospace; color: var(--text-dim); margin-top: 4px; }
.invoke-btn {
  flex-shrink: 0;
  padding: 8px 18px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--primary);
  background: linear-gradient(135deg, var(--primary-dim), var(--primary));
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
  white-space: nowrap;
  font-family: var(--font);
}
.invoke-btn:hover { box-shadow: var(--glow); transform: translateY(-1px); }
.invoke-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; box-shadow: none; }

/* ===== Request Log ===== */
.log-section {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 14px;
  overflow: hidden;
}
.log-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 600;
}
.log-list {
  max-height: 180px;
  overflow-y: auto;
  font-size: 11px;
  font-family: ui-monospace, monospace;
}
.log-row {
  display: grid;
  grid-template-columns: 64px 80px 40px 1fr;
  gap: 8px;
  padding: 6px 14px;
  border-bottom: 1px solid var(--border-subtle);
  align-items: center;
}
.log-row:last-child { border-bottom: none; }
.log-row:hover { background: var(--bg-elevated); }
.log-time { color: var(--text-dim); }
.log-svc { color: var(--text-primary); font-weight: 500; }
.log-status { font-weight: 600; }
.log-status.ok { color: var(--success); }
.log-status.err { color: var(--danger); }
.log-status.sending { color: var(--warning); }
.log-msg {
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== History ===== */
.history {
  border-top: 1px solid var(--border);
  padding-top: 14px;
}
.history-head { display: flex; justify-content: space-between; align-items: center; font-weight: 600; margin-bottom: 10px; font-size: 13px; }
.ghost-btn {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  cursor: pointer;
  transition: all var(--transition);
  font-family: var(--font);
}
.ghost-btn:hover { border-color: var(--primary); color: var(--primary); }
.history-list {
  max-height: 360px;
  overflow-y: auto;
  display: grid;
  gap: 4px;
}
.history-list::-webkit-scrollbar { width: 4px; }
.history-list::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.history-row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 12px;
  color: var(--text-muted);
  font-size: 12px;
  padding: 4px 0;
}
.h-topic {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-family: ui-monospace, monospace;
}
.history-empty, .history-error { color: var(--text-muted); font-size: 12px; padding: 12px 0; }
@media (max-width: 760px) {
  .svc-grid { grid-template-columns: 1fr; }
  .history-row { grid-template-columns: 100px 1fr; }
  .log-row { grid-template-columns: 56px 70px 34px 1fr; font-size: 10px; }
}
</style>
