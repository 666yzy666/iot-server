from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = ROOT / "docker" / "web-backend" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))


class EmqxIngestTests(unittest.TestCase):
    def test_parse_property_topic_extracts_device_id(self):
        from infrastructure.emqx import parse_property_topic

        device_id = parse_property_topic("vitam/devices/dev_001/property/post")

        self.assertEqual(device_id, "dev_001")

    def test_parse_property_topic_rejects_wrong_shape(self):
        from infrastructure.emqx import parse_property_topic

        with self.assertRaises(ValueError):
            parse_property_topic("vitam/devices/dev_001/service/get_status/invoke")

    def test_parse_property_report_normalizes_params(self):
        from infrastructure.emqx import EmqxPropertyReport, parse_property_report

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
        from infrastructure.emqx import parse_property_report

        with self.assertRaises(ValueError):
            parse_property_report(
                "vitam/devices/dev_001/property/post",
                {"params": {"device_id": "dev_002"}},
            )

    def test_parse_event_topic_extracts_device_and_event_id(self):
        from infrastructure.emqx import parse_event_topic

        device_id, event_id = parse_event_topic("vitam/devices/dev_001/event/button_pressed/post")

        self.assertEqual(device_id, "dev_001")
        self.assertEqual(event_id, "button_pressed")

    def test_parse_reply_topic_classifies_property_and_service_replies(self):
        from infrastructure.emqx import parse_reply_topic

        property_reply = parse_reply_topic("vitam/devices/dev_001/property/set_reply")
        service_reply = parse_reply_topic("vitam/devices/dev_001/service/reboot/reply")

        self.assertEqual(property_reply.device_id, "dev_001")
        self.assertEqual(property_reply.message_type, "property_set_reply")
        self.assertEqual(property_reply.action_id, "")
        self.assertEqual(service_reply.device_id, "dev_001")
        self.assertEqual(service_reply.message_type, "service_reply")
        self.assertEqual(service_reply.action_id, "reboot")

    def test_parse_reply_topic_rejects_empty_segments(self):
        from infrastructure.emqx import parse_reply_topic

        with self.assertRaises(ValueError):
            parse_reply_topic("vitam/devices//property/set_reply")
        with self.assertRaises(ValueError):
            parse_reply_topic("vitam/devices/dev_001/service//reply")


class DeviceRepositoryTests(unittest.TestCase):
    def test_store_property_report_updates_latest_status(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from infrastructure.emqx import parse_property_report
        from models.base import Base
        from repositories.device_repository import DeviceRepository

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

    def test_store_event_and_reply_records_device_messages(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from infrastructure.emqx import parse_event_report, parse_reply_report
        from models.base import Base
        from repositories.device_repository import DeviceRepository

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine, future=True)

        with Session() as session:
            repo = DeviceRepository(session)
            repo.store_event_report(
                "vitam/devices/dev_001/event/button_pressed/post",
                parse_event_report(
                    "vitam/devices/dev_001/event/button_pressed/post",
                    {"id": "evt-1", "params": {"button": "BOOT"}},
                ),
            )
            repo.store_reply_report(
                "vitam/devices/dev_001/service/reboot/reply",
                parse_reply_report(
                    "vitam/devices/dev_001/service/reboot/reply",
                    {"id": "cmd-1", "code": 200, "message": "success"},
                ),
            )
            session.commit()

        with Session() as session:
            repo = DeviceRepository(session)
            messages = repo.list_device_messages("dev_001")

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["message_type"], "service_reply")
        self.assertEqual(messages[0]["action_id"], "reboot")
        self.assertEqual(messages[1]["message_type"], "event")
        self.assertEqual(messages[1]["action_id"], "button_pressed")
