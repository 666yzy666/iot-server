from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from api.auth import current_user
from infrastructure.database import get_session
from models.user import User
from schemas.device import DeviceListResponse, HistoryListResponse
from schemas.service import ServiceInvokeRequest, ServiceInvokeResponse
from services.device_service import DeviceService
from services.mqtt_service import MqttService

router = APIRouter(prefix="/api/devices")


@router.get("", response_model=DeviceListResponse)
def list_devices(
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> DeviceListResponse:
    return DeviceService(session).list_devices(user_id=user.id)


@router.get("/{device_id}/history", response_model=HistoryListResponse)
def device_history(
    device_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> HistoryListResponse:
    return DeviceService(session).list_property_history(device_id, user_id=user.id)


@router.post("/{device_id}/services/{service_id}/invoke", response_model=ServiceInvokeResponse)
def invoke_device_service(
    device_id: str,
    service_id: str,
    body: ServiceInvokeRequest = Body(default=ServiceInvokeRequest()),
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> ServiceInvokeResponse:
    try:
        if not DeviceService(session).user_owns_device(user.id, device_id):
            raise HTTPException(status_code=404, detail="device not found")
        return MqttService().invoke_device_service(device_id, service_id, body.cmd_id)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
