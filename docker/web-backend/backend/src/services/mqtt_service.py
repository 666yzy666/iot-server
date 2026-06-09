from infrastructure import emqx_api
from schemas.service import ServiceInvokeResponse

_cmd_id_counter: int = 0


class MqttService:
    def invoke_device_service(self, device_id: str, service_id: str, cmd_id: str | None = None) -> ServiceInvokeResponse:
        if service_id not in emqx_api.SERVICE_IDS:
            raise ValueError(f"unsupported service: {service_id}")
        generated_cmd_id = cmd_id or self._next_cmd_id()
        result = emqx_api.get_client().invoke_service(device_id, service_id, generated_cmd_id)
        return ServiceInvokeResponse(
            ok=result["ok"],
            device_id=device_id,
            service_id=service_id,
            topic=result["topic"],
            cmd_id=result["cmd_id"],
            emqx_code=result.get("emqx_code"),
            emqx_message=result.get("emqx_message", ""),
        )

    def _next_cmd_id(self) -> str:
        global _cmd_id_counter
        _cmd_id_counter += 1
        return f"web-{_cmd_id_counter:04d}"
