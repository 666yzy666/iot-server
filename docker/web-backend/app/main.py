from pathlib import Path
from typing import Any

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_session
from app.emqx import parse_property_report
from app.repository import DeviceRepository
from app.schemas import DeviceListResponse, EmqxWebhookRequest, HistoryListResponse, IngestResponse


app = FastAPI(title="Vitam IoT Backend")
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


def parse_webhook_body(body: dict[str, Any]) -> EmqxWebhookRequest:
    topic = body.get("topic")
    if not isinstance(topic, str) or not topic:
        raise ValueError("webhook topic is required")
    if "payload" not in body:
        raise ValueError("webhook payload is required")
    timestamp = body.get("timestamp")
    if timestamp is not None:
        try:
            timestamp = int(timestamp)
        except (TypeError, ValueError) as exc:
            raise ValueError("webhook timestamp must be integer") from exc
    return EmqxWebhookRequest(topic=topic, payload=body["payload"], timestamp=timestamp)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def preview_page() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/api/iot/emqx/property", response_model=IngestResponse)
def ingest_property(
    body: dict[str, Any] = Body(...),
    session: Session = Depends(get_session),
) -> IngestResponse:
    try:
        request = parse_webhook_body(body)
        report = parse_property_report(request.topic, request.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo = DeviceRepository(session)
    repo.store_property_report(request.topic, report)
    session.commit()
    return IngestResponse(ok=True, device_id=report.device_id)


@app.get("/api/devices", response_model=DeviceListResponse)
def list_devices(session: Session = Depends(get_session)) -> DeviceListResponse:
    repo = DeviceRepository(session)
    return DeviceListResponse(items=repo.list_devices())


@app.get("/api/devices/{device_id}/history", response_model=HistoryListResponse)
def device_history(
    device_id: str,
    session: Session = Depends(get_session),
) -> HistoryListResponse:
    repo = DeviceRepository(session)
    return HistoryListResponse(items=repo.list_property_history(device_id))
