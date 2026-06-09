<template>
  <div class="panel">
    <div class="panel-head">
      <div class="panel-title">设备列表</div>
      <div class="hint">展开后可向指定设备发布服务调用</div>
    </div>
    <table>
      <thead>
        <tr>
          <th></th>
          <th>设备 ID</th>
          <th>状态</th>
          <th>版本</th>
          <th>OTA</th>
          <th>LED</th>
          <th>最后上报</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="item in items" :key="item.device_id">
          <tr class="device-row" :class="{ open: opened === item.device_id }" @click="toggle(item.device_id)">
            <td><span class="chevron">&#8250;</span></td>
            <td><span class="device-id">{{ item.device_id || "-" }}</span></td>
            <td>
              <span class="status" :class="item.online ? 'online' : 'offline'">
                <span class="dot"></span>{{ item.online ? "在线" : "离线" }}
              </span>
            </td>
            <td>{{ item.version || "-" }}</td>
            <td>{{ item.ota_state || "-" }}</td>
            <td :class="item.led_on ? 'led-on' : 'led-off'">
              {{ item.led_on === null ? "-" : item.led_on ? "开" : "关" }}
            </td>
            <td>{{ item.last_seen || "-" }}</td>
          </tr>
          <ServicePanel v-if="opened === item.device_id" :device-id="item.device_id" />
        </template>
        <tr v-if="!items.length">
          <td colspan="7" style="text-align:center;color:var(--muted);padding:32px;">暂无设备</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref } from "vue";
import ServicePanel from "./ServicePanel.vue";

defineProps({ items: { type: Array, default: () => [] } });
const opened = ref("");

function toggle(deviceId) {
  opened.value = opened.value === deviceId ? "" : deviceId;
}
</script>

<style scoped>
.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 18px;
  border-bottom: 1px solid var(--line);
}
.panel-title { font-weight: 700; }
.hint { color: var(--muted); font-size: 13px; }
table { width: 100%; border-collapse: collapse; }
th, td {
  padding: 14px 18px;
  text-align: left;
  border-bottom: 1px solid var(--line);
  vertical-align: middle;
}
th {
  background: var(--soft);
  color: var(--muted);
  font-size: 13px;
  font-weight: 600;
}
.device-row { cursor: pointer; }
.device-row:hover td { background: #fbfdff; }
.device-id { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; }
.status { display: inline-flex; align-items: center; gap: 8px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--offline); }
.online .dot { background: var(--success); box-shadow: 0 0 0 4px rgba(22,163,74,0.12); }
.offline { color: var(--muted); }
.chevron { color: var(--muted); transition: transform 0.16s ease; display: inline-block; }
.open .chevron { transform: rotate(90deg); }
@media (max-width:760px) {
  th, td { padding: 12px; }
}
</style>
