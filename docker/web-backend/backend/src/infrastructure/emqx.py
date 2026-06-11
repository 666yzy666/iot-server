from dataclasses import dataclass
import json
from typing import Any


@dataclass(frozen=True)
class EmqxPropertyReport:
    device_id: str
    online: bool | None
    firmware_version: str
    ota_state: str
    led_on: bool | None
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class EmqxEventReport:
    device_id: str
    event_id: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class EmqxReplyReport:
    device_id: str
    message_type: str
    action_id: str
    raw_payload: dict[str, Any]


def _normalize_payload(payload: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("payload must be a JSON object") from exc
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


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


def parse_event_topic(topic: str) -> tuple[str, str]:
    parts = topic.split("/")
    if len(parts) != 6:
        raise ValueError(f"invalid event topic: {topic}")
    if parts[0] != "vitam" or parts[1] != "devices":
        raise ValueError(f"invalid event topic prefix: {topic}")
    if parts[3] != "event" or parts[5] != "post":
        raise ValueError(f"invalid event topic suffix: {topic}")
    if not parts[2]:
        raise ValueError("device_id is empty")
    if not parts[4]:
        raise ValueError("event_id is empty")
    return parts[2], parts[4]


def parse_reply_topic(topic: str) -> EmqxReplyReport:
    parts = topic.split("/")
    if len(parts) == 5 and parts[0] == "vitam" and parts[1] == "devices":
        if parts[2] and parts[3] == "property" and parts[4] in {"set_reply", "get_reply"}:
            return EmqxReplyReport(
                device_id=parts[2],
                message_type=f"property_{parts[4]}",
                action_id="",
                raw_payload={},
            )
    if len(parts) == 6 and parts[0] == "vitam" and parts[1] == "devices":
        if parts[2] and parts[3] == "service" and parts[4] and parts[5] == "reply":
            return EmqxReplyReport(
                device_id=parts[2],
                message_type="service_reply",
                action_id=parts[4],
                raw_payload={},
            )
    raise ValueError(f"invalid reply topic: {topic}")


def parse_property_report(topic: str, payload: dict[str, Any]) -> EmqxPropertyReport:
    device_id = parse_property_topic(topic)
    payload = _normalize_payload(payload)
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


def parse_event_report(topic: str, payload: dict[str, Any]) -> EmqxEventReport:
    device_id, event_id = parse_event_topic(topic)
    payload = _normalize_payload(payload)
    return EmqxEventReport(device_id=device_id, event_id=event_id, raw_payload=payload)


def parse_reply_report(topic: str, payload: dict[str, Any]) -> EmqxReplyReport:
    parsed = parse_reply_topic(topic)
    payload = _normalize_payload(payload)
    return EmqxReplyReport(
        device_id=parsed.device_id,
        message_type=parsed.message_type,
        action_id=parsed.action_id,
        raw_payload=payload,
    )
