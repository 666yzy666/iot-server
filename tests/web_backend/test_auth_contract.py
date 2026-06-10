from pathlib import Path
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = ROOT / "docker" / "web-backend" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))


class AuthContractTests(unittest.TestCase):
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
        self.client = TestClient(app, base_url="https://testserver")

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def _register(self, username="alice", password="q958849334"):
        return self.client.post(
            "/api/auth/register",
            json={"username": username, "password": password, "display_name": "Alice"},
        )

    def test_register_hashes_password_and_login_returns_token(self):
        from infrastructure.database import get_session
        from models.user import User

        response = self._register()

        self.assertEqual(response.status_code, 200)
        self.assertIn("vitam_session=", response.headers["set-cookie"])
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        self.assertIn("SameSite=lax", response.headers["set-cookie"])
        body = response.json()
        self.assertEqual(body["user"]["username"], "alice")
        self.assertNotIn("password", body["user"])
        self.assertTrue(body["access_token"])

        with next(self.app.dependency_overrides[get_session]()) as session:
            user = session.query(User).filter_by(username="alice").one()
            self.assertNotEqual(user.password_hash, "q958849334")
            self.assertTrue(user.password_salt)

        login = self.client.post(
            "/api/auth/login",
            json={"username": "alice", "password": "q958849334"},
        )

        self.assertEqual(login.status_code, 200)
        self.assertIn("vitam_session=", login.headers["set-cookie"])
        self.assertIn("HttpOnly", login.headers["set-cookie"])
        self.assertEqual(login.json()["user"]["username"], "alice")
        self.assertTrue(login.json()["access_token"])

    def test_cookie_session_can_access_devices_without_bearer_token(self):
        from infrastructure.database import get_session
        from models.device import Device, DeviceLatestStatus
        from models.user import UserDeviceBinding

        register = self._register("alice")
        with next(self.app.dependency_overrides[get_session]()) as session:
            session.add_all(
                [
                    Device(device_id="dev_cookie"),
                    DeviceLatestStatus(device_id="dev_cookie", online=True),
                    UserDeviceBinding(user_id=1, device_id="dev_cookie"),
                ]
            )
            session.commit()

        self.client.cookies.update(register.cookies)
        response = self.client.get("/api/devices")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([i["device_id"] for i in response.json()["items"]], ["dev_cookie"])

    def test_login_rejects_wrong_password(self):
        self._register()

        response = self.client.post(
            "/api/auth/login",
            json={"username": "alice", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)

    def test_devices_are_filtered_by_logged_in_user(self):
        from infrastructure.database import get_session
        from models.device import Device, DeviceLatestStatus
        from models.user import UserDeviceBinding

        alice = self._register("alice").json()["access_token"]
        bob = self._register("bob", "bob-secret-123").json()["access_token"]

        with next(self.app.dependency_overrides[get_session]()) as session:
            session.add_all(
                [
                    Device(device_id="dev_alice"),
                    DeviceLatestStatus(device_id="dev_alice", online=True),
                    Device(device_id="dev_bob"),
                    DeviceLatestStatus(device_id="dev_bob", online=True),
                    UserDeviceBinding(user_id=1, device_id="dev_alice"),
                    UserDeviceBinding(user_id=2, device_id="dev_bob"),
                ]
            )
            session.commit()

        alice_devices = self.client.get(
            "/api/devices",
            headers={"Authorization": f"Bearer {alice}"},
        )
        bob_devices = self.client.get(
            "/api/devices",
            headers={"Authorization": f"Bearer {bob}"},
        )

        self.assertEqual(alice_devices.status_code, 200)
        self.assertEqual([i["device_id"] for i in alice_devices.json()["items"]], ["dev_alice"])
        self.assertEqual(bob_devices.status_code, 200)
        self.assertEqual([i["device_id"] for i in bob_devices.json()["items"]], ["dev_bob"])

    def test_devices_require_login(self):
        response = self.client.get("/api/devices")

        self.assertEqual(response.status_code, 401)

    def test_user_can_bind_existing_device_by_device_id(self):
        from infrastructure.database import get_session
        from models.device import Device, DeviceLatestStatus

        token = self._register("alice").json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with next(self.app.dependency_overrides[get_session]()) as session:
            session.add_all(
                [
                    Device(device_id="dev_001"),
                    DeviceLatestStatus(device_id="dev_001", online=True, version="0.1.4"),
                ]
            )
            session.commit()

        bind = self.client.post(
            "/api/devices/bind",
            json={"device_id": "dev_001"},
            headers=headers,
        )

        self.assertEqual(bind.status_code, 200)
        self.assertEqual(bind.json(), {"ok": True, "device_id": "dev_001"})

        devices = self.client.get("/api/devices", headers=headers)
        self.assertEqual([i["device_id"] for i in devices.json()["items"]], ["dev_001"])

    def test_bind_device_is_idempotent_for_same_user(self):
        from infrastructure.database import get_session
        from models.device import Device, DeviceLatestStatus
        from models.user import UserDeviceBinding

        token = self._register("alice").json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with next(self.app.dependency_overrides[get_session]()) as session:
            session.add_all([Device(device_id="dev_001"), DeviceLatestStatus(device_id="dev_001")])
            session.commit()

        first = self.client.post("/api/devices/bind", json={"device_id": "dev_001"}, headers=headers)
        second = self.client.post("/api/devices/bind", json={"device_id": "dev_001"}, headers=headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        with next(self.app.dependency_overrides[get_session]()) as session:
            rows = session.query(UserDeviceBinding).filter_by(user_id=1, device_id="dev_001").all()
            self.assertEqual(len(rows), 1)

    def test_bind_rejects_unknown_device(self):
        token = self._register("alice").json()["access_token"]

        response = self.client.post(
            "/api/devices/bind",
            json={"device_id": "missing_device"},
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("device not found", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
