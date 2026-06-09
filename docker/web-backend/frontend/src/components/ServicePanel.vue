<template>
  <div class="svc-panel">
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
    <div v-if="resultMsg" class="result-banner" :class="resultOk ? 'ok' : 'err'">{{ resultMsg }}</div>
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
const resultMsg = ref('')
const resultOk = ref(true)

async function doInvoke(svcId, btn) {
  sending.value = svcId
  resultMsg.value = ''
  await invoke(props.deviceId, svcId, btn)
  const r = getResult(props.deviceId, svcId)
  if (r) { resultMsg.value = r.message; resultOk.value = r.status === 'ok' }
  sending.value = ''
}

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
.result-banner {
  font-size: 12px;
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  margin-bottom: 14px;
}
.result-banner.ok { background: var(--success-bg); color: var(--success); }
.result-banner.err { background: var(--danger-bg); color: var(--danger); }
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
.history-list { display: grid; gap: 6px; }
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
}
</style>
