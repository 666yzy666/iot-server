from sqlalchemy.orm import Session

from infrastructure.emqx import parse_event_report, parse_property_report, parse_reply_report
from repositories.device_repository import DeviceRepository
from schemas.device import DeviceBindResponse, DeviceListResponse, HistoryListResponse
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

    def ingest_event(self, topic: str, payload) -> IngestResponse:
        report = parse_event_report(topic, payload)
        self.repo.store_event_report(topic, report)
        self.session.commit()
        return IngestResponse(ok=True, device_id=report.device_id)

    def ingest_reply(self, topic: str, payload) -> IngestResponse:
        report = parse_reply_report(topic, payload)
        self.repo.store_reply_report(topic, report)
        self.session.commit()
        return IngestResponse(ok=True, device_id=report.device_id)

    def ingest_emqx_message(self, topic: str, payload) -> IngestResponse:
        if "/property/post" in topic:
            return self.ingest_property(topic, payload)
        if "/event/" in topic and topic.endswith("/post"):
            return self.ingest_event(topic, payload)
        if topic.endswith("_reply") or topic.endswith("/reply"):
            return self.ingest_reply(topic, payload)
        raise ValueError(f"unsupported emqx topic: {topic}")

    def list_devices(self, user_id: int | None = None) -> DeviceListResponse:
        return DeviceListResponse(items=self.repo.list_devices(user_id=user_id))

    def list_property_history(self, device_id: str, user_id: int | None = None) -> HistoryListResponse:
        return HistoryListResponse(items=self.repo.list_property_history(device_id, user_id=user_id))

    def user_owns_device(self, user_id: int, device_id: str) -> bool:
        return self.repo.user_owns_device(user_id, device_id)

    def bind_device(self, user_id: int, device_id: str) -> DeviceBindResponse:
        device_id = device_id.strip()
        if not self.repo.device_exists(device_id):
            raise LookupError("device not found")
        self.repo.bind_device_to_user(user_id, device_id)
        self.session.commit()
        return DeviceBindResponse(ok=True, device_id=device_id)
