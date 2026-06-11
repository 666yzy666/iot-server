from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config.settings import Settings
from infrastructure.database import get_session
from schemas.ingest import EmqxWebhookRequest, IngestResponse
from services.device_service import DeviceService

router = APIRouter()


def parse_webhook_body(request_body: dict[str, Any]) -> EmqxWebhookRequest:
    topic = request_body.get("topic")
    if not isinstance(topic, str) or not topic:
        raise ValueError("webhook topic is required")
    if "payload" not in request_body:
        raise ValueError("webhook payload is required")
    timestamp = request_body.get("timestamp")
    if timestamp is not None:
        try:
            timestamp = int(timestamp)
        except (TypeError, ValueError) as exc:
            raise ValueError("webhook timestamp must be integer") from exc
    return EmqxWebhookRequest(topic=topic, payload=request_body["payload"], timestamp=timestamp)


def verify_webhook_secret(request: Request) -> None:
    secret = Settings.from_env().webhook_secret
    if secret and request.headers.get("x-emqx-webhook-secret") != secret:
        raise HTTPException(status_code=401, detail="invalid webhook secret")


@router.post("/api/iot/emqx/property", response_model=IngestResponse)
async def ingest_property(
    request: Request,
    session: Session = Depends(get_session),
) -> IngestResponse:
    verify_webhook_secret(request)
    try:
        request_body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="request body must be JSON") from exc
    if not isinstance(request_body, dict):
        raise HTTPException(status_code=400, detail="request body must be an object")
    try:
        webhook = parse_webhook_body(request_body)
        return DeviceService(session).ingest_property(webhook.topic, webhook.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/webhook/emqx", response_model=IngestResponse)
async def ingest_emqx_message(
    request: Request,
    session: Session = Depends(get_session),
) -> IngestResponse:
    verify_webhook_secret(request)
    try:
        request_body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="request body must be JSON") from exc
    if not isinstance(request_body, dict):
        raise HTTPException(status_code=400, detail="request body must be an object")
    try:
        webhook = parse_webhook_body(request_body)
        return DeviceService(session).ingest_emqx_message(webhook.topic, webhook.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
