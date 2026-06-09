from typing import Any
from pydantic import BaseModel, Field


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


class HistoryItem(BaseModel):
    device_id: str
    topic: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
