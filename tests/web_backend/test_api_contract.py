from pathlib import Path
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = ROOT / "docker" / "web-backend" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))


class ApiContractTests(unittest.TestCase):
    def test_settings_read_mysql_url_from_environment(self):
        from config.settings import Settings

        settings = Settings.from_env()

        self.assertEqual(
            settings.database_url,
            "mysql+pymysql://iot:iot_dev_password@127.0.0.1:3306/iot_server",
        )
        self.assertEqual(settings.webhook_secret, "")
        self.assertEqual(settings.app_host, "127.0.0.1")
        self.assertEqual(settings.app_port, 8000)


class ApiRouteTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from infrastructure.database import get_session
        from main import app
        from models.base import Base

        engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine, future=True)

        def override_session():
            with Session() as session:
                yield session

        app.dependency_overrides[get_session] = override_session
        self.app = app
        self.client = TestClient(app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def test_health(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})

    def test_ingest_property_and_list_devices(self):
        response = self.client.post(
            "/api/iot/emqx/property",
            json={
                "topic": "vitam/devices/dev_001/property/post",
                "payload": {
                    "id": "2",
                    "params": {
                        "device_id": "dev_001",
                        "online": True,
                        "version": "0.1.4",
                        "ota_state": "valid",
                        "led_on": False,
                    },
                },
                "timestamp": 1710000000000,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "device_id": "dev_001"})

        devices = self.client.get("/api/devices")
        self.assertEqual(devices.status_code, 200)
        body = devices.json()
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["items"][0]["device_id"], "dev_001")
        self.assertTrue(body["items"][0]["online"])
        self.assertEqual(body["items"][0]["version"], "0.1.4")

        history = self.client.get("/api/devices/dev_001/history")
        self.assertEqual(history.status_code, 200)
        history_body = history.json()
        self.assertEqual(len(history_body["items"]), 1)
        self.assertEqual(history_body["items"][0]["device_id"], "dev_001")
        self.assertEqual(
            history_body["items"][0]["topic"],
            "vitam/devices/dev_001/property/post",
        )

    def test_ingest_emqx_default_webhook_payload_string(self):
        response = self.client.post(
            "/api/iot/emqx/property",
            json={
                "event": "message.publish",
                "clientid": "dev_001",
                "topic": "vitam/devices/dev_001/property/post",
                "payload": (
                    '{"id":"2","version":"1.0","params":{'
                    '"device_id":"dev_001","online":true,'
                    '"version":"0.1.4","ota_state":"valid"}}'
                ),
                "timestamp": 1710000000000,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "device_id": "dev_001"})

    def test_ingest_rejects_missing_topic_with_readable_error(self):
        response = self.client.post(
            "/api/iot/emqx/property",
            json={
                "event": "message.publish",
                "payload": '{"params":{"device_id":"dev_001"}}',
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("topic", response.json()["detail"])

    def test_preview_page_conditionally_serves_frontend(self):
        from main import STATIC_DIR

        self.assertEqual(STATIC_DIR, ROOT / "docker" / "web-backend" / "frontend" / "dist")

        response = self.client.get("/")
        if STATIC_DIR.is_dir():
            self.assertEqual(response.status_code, 200)
            self.assertIn("Vitam", response.text)
        else:
            self.assertEqual(response.status_code, 404)

    def test_invoke_device_service_publishes_to_device_topic(self):
        from main import app
        from infrastructure.emqx_api import get_client

        class FakeEmqxClient:
            def invoke_service(self, device_id, service_id, cmd_id):
                return {
                    "ok": True,
                    "topic": f"vitam/devices/{device_id}/service/{service_id}/invoke",
                    "cmd_id": cmd_id,
                    "service_id": service_id,
                    "emqx_code": 0,
                    "emqx_message": "",
                }

        original_get_client = get_client
        from infrastructure import emqx_api
        emqx_api._client = None

        def fake_get_client(settings=None):
            return FakeEmqxClient()

        import infrastructure.emqx_api as api_mod
        original = api_mod.get_client
        api_mod.get_client = fake_get_client
        app.dependency_overlays_cleared = True
        try:
            response = self.client.post(
                "/api/devices/dev_001/services/get_status/invoke",
                json={"cmd_id": "cmd-test-001"},
            )
        finally:
            api_mod.get_client = original

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["device_id"], "dev_001")
        self.assertEqual(body["service_id"], "get_status")
        self.assertEqual(body["cmd_id"], "cmd-test-001")
        self.assertEqual(body["topic"], "vitam/devices/dev_001/service/get_status/invoke")

    def test_invoke_device_service_rejects_unknown_service(self):
        response = self.client.post(
            "/api/devices/dev_001/services/set_led/invoke",
            json={},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("unsupported service", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
