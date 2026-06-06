from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EmqxPropertyReport:
    device_id: str
    online: bool | None
    firmware_version: str
    ota_state: str
    led_on: bool | None
    raw_payload: dict[str, Any]


def parse_property_topic(topic: str) -> str:
    parts = topic.split("/")
    if len(parts) != 5:
        raise ValueError(f"invalid property topic: {topic}")
    if parts[0] != "vitam" or parts[1] != "devices":
        raise ValueError(f"invalid property topic prefix: {topic}")
    if parts[3] != "property" or parts[4] != "post":
        raise ValueError(f"invalid property topic suffix: {topic}")
    if not parts[2]:
        raise ValueError("device_id is empty")
    return parts[2]


def parse_property_report(topic: str, payload: dict[str, Any]) -> EmqxPropertyReport:
    device_id = parse_property_topic(topic)
    params = payload.get("params")
    if not isinstance(params, dict):
        raise ValueError("payload.params must be an object")

    payload_device_id = params.get("device_id", device_id)
    if payload_device_id != device_id:
        raise ValueError(f"payload device_id {payload_device_id} does not match topic {device_id}")

    online = params.get("online")
    led_on = params.get("led_on")
    if online is not None and not isinstance(online, bool):
        raise ValueError("params.online must be boolean")
    if led_on is not None and not isinstance(led_on, bool):
        raise ValueError("params.led_on must be boolean")

    return EmqxPropertyReport(
        device_id=device_id,
        online=online,
        firmware_version=str(params.get("version", "")),
        ota_state=str(params.get("ota_state", "")),
        led_on=led_on,
        raw_payload=payload,
    )
