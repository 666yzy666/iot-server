import { ref, onMounted, onUnmounted } from "vue";
import { fetchDevices } from "../api/deviceApi.js";

export function useDevices() {
  const items = ref([]);
  const stats = ref({ total: 0, online: 0, offline: 0, ledOn: 0 });
  let timer = null;

  async function load() {
    try {
      const data = await fetchDevices();
      items.value = data.items || [];
      const online = items.value.filter((i) => i.online).length;
      stats.value = {
        total: items.value.length,
        online,
        offline: items.value.length - online,
        ledOn: items.value.filter((i) => i.led_on === true).length,
      };
    } catch {
      // keep stale data on error
    }
  }

  onMounted(() => {
    load();
    timer = setInterval(load, 5000);
  });

  onUnmounted(() => {
    if (timer) clearInterval(timer);
  });

  return { items, stats, reload: load };
}
