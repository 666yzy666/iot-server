from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "docker" / "web-backend"
sys.path.insert(0, str(BACKEND))


class EmqxIngestTests(unittest.TestCase):
    def test_parse_property_topic_extracts_device_id(self):
        from app.emqx import parse_property_topic

        device_id = parse_property_topic("vitam/devices/dev_001/property/post")

        self.assertEqual(device_id, "dev_001")

    def test_parse_property_topic_rejects_wrong_shape(self):
        from app.emqx import parse_property_topic

        with self.assertRaises(ValueError):
            parse_property_topic("vitam/devices/dev_001/service/get_status/invoke")

    def test_parse_property_report_normalizes_params(self):
        from app.emqx import EmqxPropertyReport, parse_property_report

        report = parse_property_report(
            "vitam/devices/dev_001/property/post",
            {
                "id": "2",
                "version": "1.0",
                "params": {
                    "device_id": "dev_001",
                    "online": True,
                    "version": "0.1.4",
                    "ota_state": "valid",
                    "led_on": False,
                },
            },
        )

        self.assertIsInstance(report, EmqxPropertyReport)
        self.assertEqual(report.device_id, "dev_001")
        self.assertTrue(report.online)
        self.assertEqual(report.firmware_version, "0.1.4")
        self.assertEqual(report.ota_state, "valid")
        self.assertFalse(report.led_on)

    def test_parse_property_report_rejects_device_mismatch(self):
        from app.emqx import parse_property_report

        with self.assertRaises(ValueError):
            parse_property_report(
                "vitam/devices/dev_001/property/post",
                {"params": {"device_id": "dev_002"}},
            )


class DeviceRepositoryTests(unittest.TestCase):
    def test_store_property_report_updates_latest_status(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.emqx import parse_property_report
        from app.models import Base
        from app.repository import DeviceRepository

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine, future=True)

        report = parse_property_report(
            "vitam/devices/dev_001/property/post",
            {
                "id": "2",
                "params": {
                    "device_id": "dev_001",
                    "online": True,
                    "version": "0.1.4",
                    "ota_state": "valid",
                    "led_on": True,
                },
            },
        )

        with Session() as session:
            repo = DeviceRepository(session)
            repo.store_property_report("vitam/devices/dev_001/property/post", report)
            session.commit()

        with Session() as session:
            repo = DeviceRepository(session)
            devices = repo.list_devices()
            history = repo.list_property_history("dev_001")

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["device_id"], "dev_001")
        self.assertTrue(devices[0]["online"])
        self.assertEqual(devices[0]["version"], "0.1.4")
        self.assertEqual(devices[0]["ota_state"], "valid")
        self.assertTrue(devices[0]["led_on"])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["topic"], "vitam/devices/dev_001/property/post")
