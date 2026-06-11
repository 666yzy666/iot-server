<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">设备列表</div>
      <span class="hint">展开后可向指定设备发布指令</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead class="cursor-target">
          <tr>
            <th style="width: 32px"></th>
            <th>设备 ID</th>
            <th style="width: 80px">状态</th>
            <th style="width: 80px">版本</th>
            <th style="width: 80px">OTA</th>
            <th style="width: 60px">LED</th>
            <th>最后上报</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="item in items" :key="item.device_id">
            <tr class="device-row" :class="{ open: opened === item.device_id }" @click="toggle(item.device_id)">
              <td><span class="chev">›</span></td>
              <td><span class="mono">{{ item.device_id || '-' }}</span></td>
              <td>
                <span class="badge" :class="item.online ? 'on' : 'off'">
                  <span class="dot"></span>{{ item.online ? '在线' : '离线' }}
                </span>
              </td>
              <td>{{ item.version || '-' }}</td>
              <td>{{ item.ota_state || '-' }}</td>
              <td><span :class="item.led_on ? 'led' : 'led-offled'">{{ item.led_on === null ? '-' : item.led_on ? '开' : '关' }}</span></td>
              <td class="time">{{ item.last_seen || '-' }}</td>
            </tr>
            <tr v-if="opened === item.device_id" class="expand-row">
              <td colspan="7">
                <ServicePanel :device-id="item.device_id" :device="item" />
              </td>
            </tr>
          </template>
          <tr v-if="!items.length">
            <td colspan="7" class="empty">暂无设备</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useTargetCursor } from '../composables/useTargetCursor.js'
import ServicePanel from './ServicePanel.vue'
useTargetCursor({ targetSelector: ".cursor-target", spinDuration: 2 })

defineProps({ items: { type: Array, default: () => [] } })
const opened = ref('')
function toggle(id) { opened.value = opened.value === id ? '' : id }
</script>

<style scoped>
.panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: border-color var(--transition);
}
.panel:hover { border-color: var(--primary); }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.panel-title { font-weight: 600; font-size: 15px; color: var(--text-primary); }
.hint { color: var(--text-muted); font-size: 12px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
  font-size: 13px;
}
th {
  background: var(--bg-elevated);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}
.device-row { cursor: pointer; transition: background var(--transition); }
.device-row:hover td { background: var(--bg-elevated); }
.device-row.open td { background: var(--bg-hover); }
.mono { font-family: ui-monospace, monospace; font-size: 13px; color: var(--text-secondary); }
.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600;
}
.badge.on { background: var(--success-bg); color: var(--success); border: 1px solid rgba(34,197,94,0.2); }
.badge.off { background: var(--danger-bg); color: var(--danger); border: 1px solid rgba(239,68,68,0.2); }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.badge.on .dot { background: var(--success); box-shadow: 0 0 4px var(--success); }
.badge.off .dot { background: var(--danger); }
.led { color: var(--success); font-weight: 600; }
.led-offled { color: var(--text-muted); }
.time { color: var(--text-dim); font-size: 12px; }
.chev { color: var(--text-muted); transition: transform 0.2s ease; display: inline-block; font-size: 18px; line-height: 1; }
.open .chev { transform: rotate(90deg); color: var(--primary); }
.expand-row td {
  padding: 0;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
}
.empty {
  text-align: center;
  color: var(--text-muted);
  padding: 40px !important;
}
@media (max-width: 760px) {
  th, td { padding: 10px 12px; font-size: 12px; }
}
</style>
