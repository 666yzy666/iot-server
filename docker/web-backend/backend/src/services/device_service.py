from sqlalchemy.orm import Session

from infrastructure.emqx import parse_property_report
from repositories.device_repository import DeviceRepository
from schemas.device import DeviceListResponse, HistoryListResponse
from schemas.ingest import IngestResponse


class DeviceService:
    def __init__(self, session: Session):
        self.repo = DeviceRepository(session)
        self.session = session

    def ingest_property(self, topic: str, payload) -> IngestResponse:
        report = parse_property_report(topic, payload)
        self.repo.store_property_report(topic, report)
        self.session.commit()
        return IngestResponse(ok=True, device_id=report.device_id)

    def list_devices(self) -> DeviceListResponse:
        return DeviceListResponse(items=self.repo.list_devices())

    def list_property_history(self, device_id: str) -> HistoryListResponse:
        return HistoryListResponse(items=self.repo.list_property_history(device_id))
