from sqlalchemy import select
from sqlalchemy.orm import Session

from app.emqx import EmqxPropertyReport
from app.models import Device, DeviceLatestStatus, DevicePropertyHistory, utc_now


class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session

    def store_property_report(self, topic: str, report: EmqxPropertyReport) -> None:
        now = utc_now()

        device = self.session.get(Device, report.device_id)
        if device is None:
            device = Device(device_id=report.device_id, created_at=now)
            self.session.add(device)
        device.updated_at = now

        status = self.session.get(DeviceLatestStatus, report.device_id)
        if status is None:
            status = DeviceLatestStatus(device_id=report.device_id)
            self.session.add(status)

        status.online = report.online
        status.version = report.firmware_version
        status.ota_state = report.ota_state
        status.led_on = report.led_on
        status.last_seen = now
        status.raw_payload = report.raw_payload

        self.session.add(
            DevicePropertyHistory(
                device_id=report.device_id,
                topic=topic,
                payload=report.raw_payload,
                created_at=now,
            )
        )

    def list_devices(self) -> list[dict]:
        rows = self.session.execute(
            select(DeviceLatestStatus).order_by(DeviceLatestStatus.device_id)
        ).scalars()
        return [
            {
                "device_id": row.device_id,
                "online": row.online,
                "version": row.version,
                "ota_state": row.ota_state,
                "led_on": row.led_on,
                "last_seen": row.last_seen.isoformat() if row.last_seen else "",
                "raw_payload": row.raw_payload,
            }
            for row in rows
        ]

    def list_property_history(self, device_id: str) -> list[dict]:
        rows = self.session.execute(
            select(DevicePropertyHistory)
            .where(DevicePropertyHistory.device_id == device_id)
            .order_by(DevicePropertyHistory.created_at)
        ).scalars()
        return [
            {
                "device_id": row.device_id,
                "topic": row.topic,
                "payload": row.payload,
                "created_at": row.created_at.isoformat() if row.created_at else "",
            }
            for row in rows
        ]
