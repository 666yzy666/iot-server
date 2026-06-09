<template>
  <tr class="services-row">
    <td colspan="7">
      <div class="services-grid">
        <div class="service-card" v-for="svc in serviceList" :key="svc.id">
          <div>
            <h3>{{ svc.name }}</h3>
            <p>{{ svc.desc }}</p>
            <p class="mono">service_id={{ svc.id }}</p>
          </div>
          <button @click.stop="doInvoke(svc.id, $event.currentTarget)">发布</button>
          <p v-if="getResult(deviceId, svc.id)" class="service-result">
            <span :class="getResult(deviceId, svc.id).status === 'ok' ? 'ok' : 'err'">
              {{ getResult(deviceId, svc.id).message }}
            </span>
          </p>
        </div>
      </div>
      <div class="history">
        <div class="history-head">
          <span>最近上报</span>
          <button class="ghost" @click.stop="loadHistory">刷新</button>
        </div>
        <div v-if="historyError" class="history-error">{{ historyError }}</div>
        <div v-else-if="historyItems.length" class="history-list">
          <div class="history-item" v-for="item in historyItems" :key="`${item.created_at}-${item.topic}`">
            <span class="time">{{ item.created_at || "-" }}</span>
            <span class="topic">{{ item.topic }}</span>
          </div>
        </div>
        <div v-else class="history-empty">暂无上报记录</div>
      </div>
    </td>
  </tr>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from "vue";
import { fetchDeviceHistory } from "../api/deviceApi.js";

const props = defineProps({
  deviceId: { type: String, required: true },
  services: { type: Array, default: () => [] },
});

const serviceList = computed(() =>
  props.services.length > 0
    ? props.services
    : [
        { id: "get_status", name: "查询状态", desc: "触发设备上报最新属性" },
        { id: "reboot", name: "重启设备", desc: "设备回复后延迟重启" },
      ]
);

const invoke = inject("invokeService");
const getResult = inject("getServiceResult");
const historyItems = ref([]);
const historyError = ref("");

function doInvoke(serviceId, btn) {
  invoke(props.deviceId, serviceId, btn);
}

async function loadHistory() {
  historyError.value = "";
  try {
    const data = await fetchDeviceHistory(props.deviceId);
    historyItems.value = data.items || [];
  } catch (error) {
    historyError.value = error.message || "加载失败";
  }
}

onMounted(loadHistory);
watch(() => props.deviceId, loadHistory);
</script>

<style scoped>
.services-row td {
  background: #fbfdff;
  padding: 0;
}
.services-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding: 18px;
}
.service-card {
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 8px;
  padding: 14px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}
.service-card h3 { margin: 0; font-size: 15px; }
.service-card p { margin: 5px 0 0; color: var(--muted); font-size: 13px; }
.service-card .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }
.service-result {
  grid-column: 1 / -1;
  margin-top: 8px;
  font-size: 12px;
}
.history {
  border-top: 1px solid var(--line);
  padding: 14px 18px 18px;
}
.history-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  margin-bottom: 10px;
}
.ghost {
  background: transparent;
  color: var(--accent);
  border-color: var(--line);
  padding: 6px 10px;
}
.history-list {
  display: grid;
  gap: 8px;
}
.history-item {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 12px;
  color: var(--muted);
  font-size: 12px;
}
.topic {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.history-empty,
.history-error {
  color: var(--muted);
  font-size: 12px;
}
.ok { color: var(--success); }
.err { color: var(--danger); }
</style>
