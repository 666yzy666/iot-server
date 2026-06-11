from typing import Any

from pydantic import BaseModel, Field


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


class PropertySetRequest(BaseModel):
    cmd_id: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class PropertySetResponse(BaseModel):
    ok: bool
    device_id: str
    topic: str
    cmd_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    emqx_code: int | None = None
    emqx_message: str = ""
