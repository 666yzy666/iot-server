from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_session
from app.emqx import parse_property_report
from app.repository import DeviceRepository
from app.schemas import DeviceListResponse, EmqxWebhookRequest, IngestResponse


app = FastAPI(title="Vitam IoT Backend")
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def preview_page() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/api/iot/emqx/property", response_model=IngestResponse)
def ingest_property(
    request: EmqxWebhookRequest,
    session: Session = Depends(get_session),
) -> IngestResponse:
    try:
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
