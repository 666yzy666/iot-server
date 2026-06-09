"""EMQX REST API v5 client for publishing MQTT messages."""
import base64
import json
import logging
from typing import Any

import httpx

from config.settings import Settings

logger = logging.getLogger(__name__)

SERVICE_IDS = ["get_status", "reboot"]


def _basic_auth(key: str, secret: str) -> str:
    token = base64.b64encode(f"{key}:{secret}".encode()).decode()
    return f"Basic {token}"


class EmqxApiClient:
    """Lightweight EMQX v5 REST API client for publishing MQTT messages."""

    def __init__(self, settings: Settings) -> None:
        self._url = settings.emqx_api_url.rstrip("/")
        self._auth_header = _basic_auth(settings.emqx_api_key, settings.emqx_api_secret)
        self._topic_base = settings.mqtt_topic_base.rstrip("/")
        self._http = httpx.Client(timeout=10.0)

    def service_invoke_topic(self, device_id: str, service_id: str) -> str:
        return f"{self._topic_base}/{device_id}/service/{service_id}/invoke"

    def invoke_service(self, device_id: str, service_id: str, cmd_id: str) -> dict[str, Any]:
        topic = self.service_invoke_topic(device_id, service_id)
        payload = json.dumps({"id": cmd_id, "params": {}}, ensure_ascii=False)
        resp = self._http.post(
            f"{self._url}/publish",
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json",
            },
            json={"topic": topic, "payload": payload, "qos": 1, "retain": False},
        )
        resp.raise_for_status()
        body = resp.json()
        logger.info("EMQX publish: topic=%s id=%s code=%s", topic, cmd_id, body.get("code"))
        return {
            "ok": body.get("code", 0) == 0,
            "topic": topic,
            "cmd_id": cmd_id,
            "service_id": service_id,
            "emqx_code": body.get("code"),
            "emqx_message": body.get("message", ""),
        }


_client: EmqxApiClient | None = None


def get_client(settings: Settings | None = None) -> EmqxApiClient:
    global _client
    if _client is None:
        if settings is None:
            settings = Settings.from_env()
        _client = EmqxApiClient(settings)
    return _client
