from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.emqx import EmqxEventReport, EmqxPropertyReport, EmqxReplyReport
from models.device import Device, DeviceLatestStatus, DeviceMessageHistory, DevicePropertyHistory, utc_now
from models.user import UserDeviceBinding


class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session

    def store_property_report(self, topic: str, report: EmqxPropertyReport) -> None:
        now = utc_now()

        device = self._ensure_device(report.device_id, now)
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

    def _ensure_device(self, device_id: str, now) -> Device:
        device = self.session.get(Device, device_id)
        if device is None:
            device = Device(device_id=device_id, created_at=now)
            self.session.add(device)
        return device

    def store_event_report(self, topic: str, report: EmqxEventReport) -> None:
        now = utc_now()
        device = self._ensure_device(report.device_id, now)
        device.updated_at = now

        self.session.add(
            DeviceMessageHistory(
                device_id=report.device_id,
                message_type="event",
                action_id=report.event_id,
                topic=topic,
                payload=report.raw_payload,
                created_at=now,
            )
        )

    def store_reply_report(self, topic: str, report: EmqxReplyReport) -> None:
        now = utc_now()
        device = self._ensure_device(report.device_id, now)
        device.updated_at = now

        self.session.add(
            DeviceMessageHistory(
                device_id=report.device_id,
                message_type=report.message_type,
                action_id=report.action_id,
                topic=topic,
                payload=report.raw_payload,
                created_at=now,
            )
        )

    def list_devices(self, user_id: int | None = None) -> list[dict]:
        stmt = select(DeviceLatestStatus).order_by(DeviceLatestStatus.device_id)
        if user_id is not None:
            stmt = (
                stmt.join(
                    UserDeviceBinding,
                    UserDeviceBinding.device_id == DeviceLatestStatus.device_id,
                )
                .where(UserDeviceBinding.user_id == user_id)
                .order_by(DeviceLatestStatus.device_id)
            )
        rows = self.session.execute(
            stmt
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

    def user_owns_device(self, user_id: int, device_id: str) -> bool:
        return (
            self.session.execute(
                select(UserDeviceBinding.id).where(
                    UserDeviceBinding.user_id == user_id,
                    UserDeviceBinding.device_id == device_id,
                )
            ).first()
            is not None
        )

    def device_exists(self, device_id: str) -> bool:
        return self.session.get(Device, device_id) is not None

    def bind_device_to_user(self, user_id: int, device_id: str) -> None:
        if self.user_owns_device(user_id, device_id):
            return
        self.session.add(UserDeviceBinding(user_id=user_id, device_id=device_id))

    def list_property_history(
        self,
        device_id: str,
        limit: int = 20,
        user_id: int | None = None,
    ) -> list[dict]:
        stmt = select(DevicePropertyHistory).where(DevicePropertyHistory.device_id == device_id)
        if user_id is not None:
            stmt = stmt.join(
                UserDeviceBinding,
                UserDeviceBinding.device_id == DevicePropertyHistory.device_id,
            ).where(UserDeviceBinding.user_id == user_id)
        rows = self.session.execute(
            stmt.order_by(DevicePropertyHistory.created_at.desc(), DevicePropertyHistory.id.desc()).limit(limit)
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

    def list_device_messages(self, device_id: str, limit: int = 20) -> list[dict]:
        rows = self.session.execute(
            select(DeviceMessageHistory)
            .where(DeviceMessageHistory.device_id == device_id)
            .order_by(DeviceMessageHistory.created_at.desc(), DeviceMessageHistory.id.desc())
            .limit(limit)
        ).scalars()
        return [
            {
                "device_id": row.device_id,
                "message_type": row.message_type,
                "action_id": row.action_id,
                "topic": row.topic,
                "payload": row.payload,
                "created_at": row.created_at.isoformat() if row.created_at else "",
            }
            for row in rows
        ]
