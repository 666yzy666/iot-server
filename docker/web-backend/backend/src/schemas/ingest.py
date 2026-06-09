from typing import Any
from pydantic import BaseModel


class EmqxWebhookRequest(BaseModel):
    topic: str
    payload: Any
    timestamp: int | None = None


class IngestResponse(BaseModel):
    ok: bool
    device_id: str
