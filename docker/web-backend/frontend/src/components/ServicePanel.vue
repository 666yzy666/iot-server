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
    </td>
  </tr>
</template>

<script setup>
import { computed, inject } from "vue";

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

function doInvoke(serviceId, btn) {
  invoke(props.deviceId, serviceId, btn);
}
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
.ok { color: var(--success); }
.err { color: var(--danger); }
</style>
