from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DeviceLatestStatus(Base):
    __tablename__ = "device_latest_status"

    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    online: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    version: Mapped[str] = mapped_column(String(32), default="")
    ota_state: Mapped[str] = mapped_column(String(32), default="")
    led_on: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class DevicePropertyHistory(Base):
    __tablename__ = "device_property_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    topic: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
