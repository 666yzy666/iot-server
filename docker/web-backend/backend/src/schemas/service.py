from pydantic import BaseModel


class ServiceInvokeRequest(BaseModel):
    cmd_id: str | None = None


class ServiceInvokeResponse(BaseModel):
    ok: bool
    device_id: str
    service_id: str
    topic: str
    cmd_id: str
    emqx_code: int | None = None
    emqx_message: str = ""
