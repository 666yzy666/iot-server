from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database import get_session
from schemas.device import DeviceListResponse
from schemas.service import ServiceInvokeRequest, ServiceInvokeResponse
from services.device_service import DeviceService
from services.mqtt_service import MqttService

router = APIRouter(prefix="/api/devices")


@router.get("", response_model=DeviceListResponse)
def list_devices(session: Session = Depends(get_session)) -> DeviceListResponse:
    return DeviceService(session).list_devices()


@router.post("/{device_id}/services/{service_id}/invoke", response_model=ServiceInvokeResponse)
def invoke_device_service(
    device_id: str,
    service_id: str,
    body: ServiceInvokeRequest = Body(default=ServiceInvokeRequest()),
) -> ServiceInvokeResponse:
    try:
        return MqttService().invoke_device_service(device_id, service_id, body.cmd_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
