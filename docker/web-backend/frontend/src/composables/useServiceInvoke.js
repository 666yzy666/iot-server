import { ref } from "vue";
import { invokeDeviceService } from "../api/deviceApi.js";

export function useServiceInvoke() {
  const results = ref({});

  async function invoke(deviceId, serviceId, buttonEl) {
    if (buttonEl) buttonEl.disabled = true;
    const key = `${deviceId}:${serviceId}`;
    results.value[key] = { status: "sending", message: `正在发布 ${serviceId}...` };
    try {
      const data = await invokeDeviceService(deviceId, serviceId);
      results.value[key] = {
        status: "ok",
        message: `已发布：${data.topic}，cmd_id=${data.cmd_id}`,
      };
    } catch (err) {
      results.value[key] = { status: "err", message: `发布失败：${err.message}` };
    } finally {
      if (buttonEl) buttonEl.disabled = false;
    }
  }

  function getResult(deviceId, serviceId) {
    return results.value[`${deviceId}:${serviceId}`] || null;
  }

  return { invoke, getResult };
}
