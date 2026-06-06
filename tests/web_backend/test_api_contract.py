from pathlib import Path
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "docker" / "web-backend"
sys.path.insert(0, str(BACKEND))


class ApiContractTests(unittest.TestCase):
    def test_settings_read_mysql_url_from_environment(self):
        from app.config import Settings

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

        from app.database import get_session
        from app.main import app
        from app.models import Base

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

    def test_preview_page_serves_html(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Vitam Device Preview", response.text)
        self.assertIn("/api/devices", response.text)
