from typing import Any

from pydantic import BaseModel, Field


class EmqxWebhookRequest(BaseModel):
    topic: str
    payload: Any
    timestamp: int | None = None


class IngestResponse(BaseModel):
    ok: bool
    device_id: str


class DeviceItem(BaseModel):
    device_id: str
    online: bool | None
    version: str = ""
    ota_state: str = ""
    led_on: bool | None = None
    last_seen: str = ""
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class DeviceListResponse(BaseModel):
    items: list[DeviceItem]
