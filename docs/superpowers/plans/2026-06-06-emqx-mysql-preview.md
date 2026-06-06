# EMQX MySQL Device Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first backend loop that stores EMQX device property reports in MySQL and exposes a device preview API/page.

**Architecture:** ESP32 publishes `vitam/devices/{device_id}/property/post` to EMQX. EMQX Rule/Webhook sends the topic and payload to a FastAPI HTTP endpoint. The backend validates the message, upserts the latest device status into MySQL, optionally stores history, and exposes read APIs for a simple admin preview page.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, PyMySQL, Pydantic, pytest, httpx, MySQL 8, Baota Python project/reverse proxy, EMQX Webhook.

---

## Current Repository Context

The working tree is already being reorganized so deployment/server content lives under `docker/`.
The active runtime target is the server managed by Baota Panel. The web backend is packaged as its own Docker service so the server can `git clone`, configure `.env`, and run `bash deploy.sh`.

Relevant paths for this plan:

- `docker/web-backend/docker-compose.yml`: active one-click backend deployment for the Baota server.
- `docker/docker-compose.yml`: legacy/reference compose stack for older local development notes.
- `docker/web-backend/`: backend service directory.
- `docker/mqtt-server/`: EMQX notes/config.
- `docs/index.html`: project learning docs.
- `tests/`: existing Python test suite.

Do not use root `docker-compose.yml`; it was moved to `docker/docker-compose.yml`. The backend runtime compose file lives at `docker/web-backend/docker-compose.yml`.

## Target Data Flow

```text
ESP32
  -> MQTTS publish vitam/devices/dev_001/property/post
  -> EMQX
  -> Webhook POST http://web-backend:8000/api/iot/emqx/property
  -> FastAPI
  -> MySQL devices/device_latest_status/device_property_history
  -> GET /api/devices
  -> admin preview page
```

## File Structure

Create or modify these files:

- Create `docker/web-backend/requirements.txt`: Python dependencies.
- Create `docker/web-backend/app/__init__.py`: package marker.
- Create `docker/web-backend/app/config.py`: environment configuration.
- Create `docker/web-backend/app/database.py`: SQLAlchemy engine/session helpers.
- Create `docker/web-backend/app/models.py`: SQLAlchemy table models.
- Create `docker/web-backend/app/schemas.py`: Pydantic request/response models.
- Create `docker/web-backend/app/emqx.py`: topic parsing and payload normalization.
- Create `docker/web-backend/app/repository.py`: database writes/queries.
- Create `docker/web-backend/app/main.py`: FastAPI app and routes.
- Create `docker/web-backend/static/index.html`: first device preview page.
- Create `docker/web-backend/.env.example`: Baota/server runtime environment template.
- Modify `docker/web-backend/README.md`: Baota deployment steps.
- Modify `docs/index.html`: document EMQX Webhook to MySQL flow.
- Create `tests/web_backend/test_emqx_ingest.py`: unit tests for topic/payload handling.
- Create `tests/web_backend/test_api_contract.py`: FastAPI route tests.
- Create `tests/web_backend/test_deployment_contract.py`: Baota deployment contract tests.

---

### Task 1: Add Backend Dependencies and Package Skeleton

**Files:**
- Create: `docker/web-backend/requirements.txt`
- Create: `docker/web-backend/app/__init__.py`
- Create: `docker/web-backend/app/config.py`
- Test: `tests/web_backend/test_api_contract.py`

- [ ] **Step 1: Write the failing import/config test**

Create `tests/web_backend/test_api_contract.py`:

```python
import importlib
import os


def test_backend_package_imports():
	module = importlib.import_module("docker.web-backend.app.config")
	assert hasattr(module, "Settings")


def test_settings_read_mysql_url_from_environment(monkeypatch):
	monkeypatch.setenv(
		"DATABASE_URL",
		"mysql+pymysql://iot:iot_dev_password@mysql:3306/iot_server",
	)

	config = importlib.import_module("docker.web-backend.app.config")
	settings = config.Settings.from_env()

	assert settings.database_url == "mysql+pymysql://iot:iot_dev_password@mysql:3306/iot_server"
	assert settings.webhook_secret == ""
```

This test is expected to fail first because Python cannot import a package path containing a hyphen. Implement Step 3 using an import helper instead of renaming the folder.

- [ ] **Step 2: Run the failing test**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: failure in `test_backend_package_imports` due to missing backend package/import path.

- [ ] **Step 3: Add backend dependencies**

Create `docker/web-backend/requirements.txt`:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
SQLAlchemy==2.0.36
PyMySQL==1.1.1
pydantic==2.10.4
python-dotenv==1.0.1
```

- [ ] **Step 4: Add package files**

Create `docker/web-backend/app/__init__.py`:

```python
"""Web backend package for IoT device ingestion and preview."""
```

Create `docker/web-backend/app/config.py`:

```python
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
	database_url: str
	webhook_secret: str

	@classmethod
	def from_env(cls) -> "Settings":
		return cls(
			database_url=os.getenv(
				"DATABASE_URL",
				"mysql+pymysql://iot:iot_dev_password@mysql:3306/iot_server",
			),
			webhook_secret=os.getenv("EMQX_WEBHOOK_SECRET", ""),
		)
```

Because `docker/web-backend` has a hyphen, tests should import app modules by inserting `docker/web-backend` into `sys.path`. Replace the import test with:

```python
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "docker" / "web-backend"
sys.path.insert(0, str(BACKEND))

from app.config import Settings


def test_settings_read_mysql_url_from_environment(monkeypatch):
	monkeypatch.setenv(
		"DATABASE_URL",
		"mysql+pymysql://iot:iot_dev_password@mysql:3306/iot_server",
	)

	settings = Settings.from_env()

	assert settings.database_url == "mysql+pymysql://iot:iot_dev_password@mysql:3306/iot_server"
	assert settings.webhook_secret == ""
```

- [ ] **Step 5: Run the test**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: existing tests pass plus the new settings test passes.

- [ ] **Step 6: Commit**

```bash
git add docker/web-backend/requirements.txt docker/web-backend/app/__init__.py docker/web-backend/app/config.py tests/web_backend/test_api_contract.py
git commit -m "Add web backend FastAPI skeleton"
```

---

### Task 2: Define EMQX Topic and Payload Parsing

**Files:**
- Create: `docker/web-backend/app/emqx.py`
- Modify: `tests/web_backend/test_emqx_ingest.py`

- [ ] **Step 1: Write failing parser tests**

Create `tests/web_backend/test_emqx_ingest.py`:

```python
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "docker" / "web-backend"
sys.path.insert(0, str(BACKEND))

from app.emqx import EmqxPropertyReport, parse_property_topic, parse_property_report


class EmqxIngestTests(unittest.TestCase):
	def test_parse_property_topic_extracts_device_id(self):
		device_id = parse_property_topic("vitam/devices/dev_001/property/post")
		self.assertEqual(device_id, "dev_001")

	def test_parse_property_topic_rejects_wrong_shape(self):
		with self.assertRaises(ValueError):
			parse_property_topic("vitam/devices/dev_001/service/get_status/invoke")

	def test_parse_property_report_normalizes_params(self):
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
		with self.assertRaises(ValueError):
			parse_property_report(
				"vitam/devices/dev_001/property/post",
				{"params": {"device_id": "dev_002"}},
			)
```

- [ ] **Step 2: Run failing parser tests**

Run:

```bash
python -m unittest tests.web_backend.test_emqx_ingest -v
```

Expected: fail because `app.emqx` does not exist.

- [ ] **Step 3: Implement parser**

Create `docker/web-backend/app/emqx.py`:

```python
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

	version = params.get("version", "")
	ota_state = params.get("ota_state", "")
	online = params.get("online")
	led_on = params.get("led_on")

	if online is not None and not isinstance(online, bool):
		raise ValueError("params.online must be boolean")
	if led_on is not None and not isinstance(led_on, bool):
		raise ValueError("params.led_on must be boolean")

	return EmqxPropertyReport(
		device_id=device_id,
		online=online,
		firmware_version=str(version),
		ota_state=str(ota_state),
		led_on=led_on,
		raw_payload=payload,
	)
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
python -m unittest tests.web_backend.test_emqx_ingest -v
```

Expected: all parser tests pass.

- [ ] **Step 5: Commit**

```bash
git add docker/web-backend/app/emqx.py tests/web_backend/test_emqx_ingest.py
git commit -m "Parse EMQX property reports"
```

---

### Task 3: Add MySQL Models and Repository

**Files:**
- Create: `docker/web-backend/app/database.py`
- Create: `docker/web-backend/app/models.py`
- Create: `docker/web-backend/app/repository.py`
- Modify: `tests/web_backend/test_emqx_ingest.py`

- [ ] **Step 1: Write repository test with SQLite**

Append to `tests/web_backend/test_emqx_ingest.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.repository import DeviceRepository


class DeviceRepositoryTests(unittest.TestCase):
	def test_upsert_property_report_updates_latest_status(self):
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

		self.assertEqual(len(devices), 1)
		self.assertEqual(devices[0]["device_id"], "dev_001")
		self.assertTrue(devices[0]["online"])
		self.assertEqual(devices[0]["version"], "0.1.4")
		self.assertEqual(devices[0]["ota_state"], "valid")
		self.assertTrue(devices[0]["led_on"])
```

- [ ] **Step 2: Run failing repository test**

Run:

```bash
python -m unittest tests.web_backend.test_emqx_ingest -v
```

Expected: fail because models/repository do not exist.

- [ ] **Step 3: Implement database helpers**

Create `docker/web-backend/app/database.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings


settings = Settings.from_env()
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Generator[Session, None, None]:
	session = SessionLocal()
	try:
		yield session
	finally:
		session.close()
```

- [ ] **Step 4: Implement models**

Create `docker/web-backend/app/models.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
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
	raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)


class DevicePropertyHistory(Base):
	__tablename__ = "device_property_history"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	device_id: Mapped[str] = mapped_column(String(64), index=True)
	topic: Mapped[str] = mapped_column(String(255))
	payload: Mapped[dict] = mapped_column(JSON, default=dict)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
```

- [ ] **Step 5: Implement repository**

Create `docker/web-backend/app/repository.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.emqx import EmqxPropertyReport
from app.models import Device, DeviceLatestStatus, DevicePropertyHistory, utc_now


class DeviceRepository:
	def __init__(self, session: Session):
		self.session = session

	def store_property_report(self, topic: str, report: EmqxPropertyReport) -> None:
		now = utc_now()

		device = self.session.get(Device, report.device_id)
		if device is None:
			device = Device(device_id=report.device_id, created_at=now)
			self.session.add(device)
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

	def list_devices(self) -> list[dict]:
		rows = self.session.execute(select(DeviceLatestStatus).order_by(DeviceLatestStatus.device_id)).scalars()
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
```

- [ ] **Step 6: Run repository tests**

Run:

```bash
python -m unittest tests.web_backend.test_emqx_ingest -v
```

Expected: all parser and repository tests pass.

- [ ] **Step 7: Commit**

```bash
git add docker/web-backend/app/database.py docker/web-backend/app/models.py docker/web-backend/app/repository.py tests/web_backend/test_emqx_ingest.py
git commit -m "Store device property reports"
```

---

### Task 4: Add FastAPI Routes

**Files:**
- Create: `docker/web-backend/app/schemas.py`
- Create: `docker/web-backend/app/main.py`
- Modify: `tests/web_backend/test_api_contract.py`

- [ ] **Step 1: Write route tests**

Replace `tests/web_backend/test_api_contract.py` with:

```python
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "docker" / "web-backend"
sys.path.insert(0, str(BACKEND))

from app.database import get_session
from app.main import app
from app.models import Base


class ApiContractTests(unittest.TestCase):
	def setUp(self):
		engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
		Base.metadata.create_all(engine)
		Session = sessionmaker(bind=engine, future=True)

		def override_session():
			with Session() as session:
				yield session

		app.dependency_overrides[get_session] = override_session
		self.client = TestClient(app)

	def tearDown(self):
		app.dependency_overrides.clear()

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
```

- [ ] **Step 2: Run failing route tests**

Run:

```bash
python -m unittest tests.web_backend.test_api_contract -v
```

Expected: fail because `app.main` and schemas do not exist.

- [ ] **Step 3: Add schemas**

Create `docker/web-backend/app/schemas.py`:

```python
from typing import Any

from pydantic import BaseModel, Field


class EmqxWebhookRequest(BaseModel):
	topic: str
	payload: dict[str, Any]
	timestamp: int | None = None


class IngestResponse(BaseModel):
	ok: bool
	device_id: str


class DeviceItem(BaseModel):
	device_id: str
	online: bool | None
	version: str = ""
	ota_state: str = ""
	led_on: bool | None = None
	last_seen: str = ""
	raw_payload: dict[str, Any] = Field(default_factory=dict)


class DeviceListResponse(BaseModel):
	items: list[DeviceItem]
```

- [ ] **Step 4: Add FastAPI app**

Create `docker/web-backend/app/main.py`:

```python
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.emqx import parse_property_report
from app.models import Base
from app.database import engine
from app.repository import DeviceRepository
from app.schemas import DeviceListResponse, EmqxWebhookRequest, IngestResponse


app = FastAPI(title="IoT Server Backend")


@app.on_event("startup")
def create_tables() -> None:
	Base.metadata.create_all(engine)


@app.get("/health")
def health() -> dict[str, bool]:
	return {"ok": True}


@app.post("/api/iot/emqx/property", response_model=IngestResponse)
def ingest_property(request: EmqxWebhookRequest, session: Session = Depends(get_session)) -> IngestResponse:
	try:
		report = parse_property_report(request.topic, request.payload)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc

	repo = DeviceRepository(session)
	repo.store_property_report(request.topic, report)
	session.commit()
	return IngestResponse(ok=True, device_id=report.device_id)


@app.get("/api/devices", response_model=DeviceListResponse)
def list_devices(session: Session = Depends(get_session)) -> DeviceListResponse:
	repo = DeviceRepository(session)
	return DeviceListResponse(items=repo.list_devices())
```

- [ ] **Step 5: Run route tests**

Run:

```bash
python -m unittest tests.web_backend.test_api_contract -v
```

Expected: route tests pass.

- [ ] **Step 6: Run full tests**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add docker/web-backend/app/schemas.py docker/web-backend/app/main.py tests/web_backend/test_api_contract.py
git commit -m "Add EMQX webhook API"
```

---

### Task 5: Add Baota Runtime Configuration

**Files:**
- Create: `docker/web-backend/.env.example`
- Create: `tests/web_backend/test_deployment_contract.py`
- Modify: `docker/web-backend/README.md`

- [ ] **Step 1: Write Baota deployment contract tests**

Create `tests/web_backend/test_deployment_contract.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = ROOT / "docker" / "web-backend" / ".env.example"
README = ROOT / "docker" / "web-backend" / "README.md"
DOCKERFILE = ROOT / "docker" / "web-backend" / "Dockerfile"
COMPOSE = ROOT / "docker" / "web-backend" / "docker-compose.yml"
DEPLOY = ROOT / "docker" / "web-backend" / "deploy.sh"


class DeploymentContractTests(unittest.TestCase):
	def test_env_example_targets_baota_mysql_and_api_runtime(self):
		text = ENV_EXAMPLE.read_text(encoding="utf-8")
		self.assertIn("DATABASE_URL=mysql+pymysql://iot_server:iot_dev_password@host.docker.internal:3306/iot_server", text)
		self.assertIn("EMQX_WEBHOOK_SECRET=hyrain_emqx_webhook_secret_example", text)
		self.assertIn("APP_PORT=8000", text)

	def test_readme_documents_baota_docker_deploy(self):
		text = README.read_text(encoding="utf-8")
		self.assertIn("宝塔", text)
		self.assertIn("Docker", text)
		self.assertIn("bash deploy.sh", text)
		self.assertIn("api.hyrain.xyz", text)

	def test_docker_deploy_files_are_defined(self):
		dockerfile = DOCKERFILE.read_text(encoding="utf-8")
		compose = COMPOSE.read_text(encoding="utf-8")
		deploy = DEPLOY.read_text(encoding="utf-8")

		self.assertIn("FROM python:3.12-slim", dockerfile)
		self.assertIn('CMD ["uvicorn", "app.main:app"', dockerfile)
		self.assertIn("host.docker.internal:host-gateway", compose)
		self.assertIn('"127.0.0.1:${APP_PORT:-8000}:8000"', compose)
		self.assertIn("python -m app.init_db", deploy)
		self.assertIn("docker compose --env-file .env up -d --build", deploy)
```

- [ ] **Step 2: Run failing deployment tests**

Run:

```bash
python -m unittest tests.web_backend.test_deployment_contract -v
```

Expected: fail because `.env.example`, Dockerfile, compose, deploy script, and Baota deployment notes do not exist yet.

- [ ] **Step 3: Add environment template**

Create `docker/web-backend/.env.example`:

```text
DATABASE_URL=mysql+pymysql://iot_server:iot_dev_password@host.docker.internal:3306/iot_server
EMQX_WEBHOOK_SECRET=hyrain_emqx_webhook_secret_example
APP_PORT=8000
```

- [ ] **Step 4: Add Docker runtime files**

Create `docker/web-backend/Dockerfile`, `docker/web-backend/docker-compose.yml`, and `docker/web-backend/deploy.sh`.

`docker-compose.yml` binds the backend to host `127.0.0.1:${APP_PORT:-8000}` and uses `host.docker.internal:host-gateway` so the container can access Baota MySQL running on the server host.

- [ ] **Step 5: Update Baota deployment notes**

Append this section to `docker/web-backend/README.md`:

```markdown
## Runtime

当前推荐运行方式是 Docker。服务器上 git clone 后，进入本目录，配置 `.env`，执行 `bash deploy.sh` 即可构建镜像、初始化数据库表并启动容器。

MySQL 仍然使用宝塔面板创建和管理。容器通过 `host.docker.internal` 访问服务器宿主机上的 MySQL。

```bash
cp .env.example .env
vim .env
bash deploy.sh
```

宝塔网站中新建 `api.hyrain.xyz`，开启 HTTPS，反向代理到 `http://127.0.0.1:8000`。
```

- [ ] **Step 6: Run deployment tests**

Run:

```bash
python -m unittest tests.web_backend.test_deployment_contract -v
```

Expected: deployment tests pass.

- [ ] **Step 7: Commit**

```bash
git add docker/web-backend/.env.example docker/web-backend/Dockerfile docker/web-backend/docker-compose.yml docker/web-backend/deploy.sh docker/web-backend/README.md tests/web_backend/test_deployment_contract.py
git commit -m "Add Baota Docker backend runtime"
```

---

### Task 6: Add Device Preview Page

**Files:**
- Create: `docker/web-backend/static/index.html`
- Modify: `docker/web-backend/app/main.py`
- Modify: `tests/web_backend/test_api_contract.py`

- [ ] **Step 1: Write static page route test**

Append to `tests/web_backend/test_api_contract.py`:

```python
	def test_preview_page_serves_html(self):
		response = self.client.get("/")
		self.assertEqual(response.status_code, 200)
		self.assertIn("Vitam Device Preview", response.text)
		self.assertIn("/api/devices", response.text)
```

- [ ] **Step 2: Run failing page test**

Run:

```bash
python -m unittest tests.web_backend.test_api_contract -v
```

Expected: fail because `/` route does not serve the preview page.

- [ ] **Step 3: Add static page**

Create `docker/web-backend/static/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>Vitam Device Preview</title>
	<style>
		body { font-family: Arial, sans-serif; margin: 24px; background: #f7f8fa; color: #1f2937; }
		main { max-width: 1080px; margin: 0 auto; }
		table { width: 100%; border-collapse: collapse; background: white; }
		th, td { padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: left; }
		th { background: #eef2f7; }
		.online { color: #059669; font-weight: 700; }
		.offline { color: #9ca3af; font-weight: 700; }
	</style>
</head>
<body>
	<main>
		<h1>Vitam Device Preview</h1>
		<table>
			<thead>
				<tr>
					<th>设备 ID</th>
					<th>在线</th>
					<th>版本</th>
					<th>OTA</th>
					<th>LED</th>
					<th>最后上报</th>
				</tr>
			</thead>
			<tbody id="devices"></tbody>
		</table>
	</main>
	<script>
		async function loadDevices() {
			const response = await fetch('/api/devices');
			const data = await response.json();
			const rows = data.items.map((item) => `
				<tr>
					<td>${item.device_id}</td>
					<td class="${item.online ? 'online' : 'offline'}">${item.online ? '在线' : '离线'}</td>
					<td>${item.version || ''}</td>
					<td>${item.ota_state || ''}</td>
					<td>${item.led_on === null ? '' : (item.led_on ? '开' : '关')}</td>
					<td>${item.last_seen || ''}</td>
				</tr>
			`).join('');
			document.getElementById('devices').innerHTML = rows;
		}
		loadDevices();
		setInterval(loadDevices, 5000);
	</script>
</body>
</html>
```

- [ ] **Step 4: Serve preview page**

Modify `docker/web-backend/app/main.py`:

```python
from pathlib import Path

from fastapi.responses import HTMLResponse

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@app.get("/", response_class=HTMLResponse)
def preview_page() -> str:
	return (STATIC_DIR / "index.html").read_text(encoding="utf-8")
```

Place these imports and route alongside the existing app routes.

- [ ] **Step 5: Run route tests**

Run:

```bash
python -m unittest tests.web_backend.test_api_contract -v
```

Expected: page and API tests pass.

- [ ] **Step 6: Commit**

```bash
git add docker/web-backend/static/index.html docker/web-backend/app/main.py tests/web_backend/test_api_contract.py
git commit -m "Add device preview page"
```

---

### Task 7: Document EMQX Webhook and Baota Deployment

**Files:**
- Modify: `docker/web-backend/README.md`
- Modify: `docs/index.html`
- Create: `tests/web_backend/test_docs_contract.py`

- [ ] **Step 1: Write docs contract tests**

Create `tests/web_backend/test_docs_contract.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DocsContractTests(unittest.TestCase):
	def test_web_backend_readme_documents_emqx_webhook(self):
		text = (ROOT / "docker" / "web-backend" / "README.md").read_text(encoding="utf-8")
		self.assertIn("https://api.hyrain.xyz/api/iot/emqx/property", text)
		self.assertIn('SELECT topic, payload, timestamp FROM "vitam/devices/+/property/post"', text)
		self.assertIn("宝塔", text)

	def test_project_docs_reference_mysql_preview_flow(self):
		text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
		self.assertIn("EMQX Webhook", text)
		self.assertIn("device_latest_status", text)
		self.assertIn("docker/web-backend", text)
```

- [ ] **Step 2: Run failing docs tests**

Run:

```bash
python -m unittest tests.web_backend.test_docs_contract -v
```

Expected: fail until README/docs mention the exact webhook flow.

- [ ] **Step 3: Update web-backend README**

Add this section to `docker/web-backend/README.md`:

````markdown
## EMQX Webhook 入库

EMQX 规则 SQL:

```sql
SELECT topic, payload, timestamp FROM "vitam/devices/+/property/post"
```

Webhook:

```text
POST https://api.hyrain.xyz/api/iot/emqx/property
```

请求体:

```json
{
	"topic": "${topic}",
	"payload": "${payload}",
	"timestamp": "${timestamp}"
}
```

后端写入:

- `devices`: 设备基础信息。
- `device_latest_status`: 后台概览读取的最新状态。
- `device_property_history`: 原始属性上报历史。

## 宝塔部署

1. 服务器上 `git clone` 项目。
2. 进入 `docker/web-backend`。
3. 复制 `.env.example` 为 `.env`，填写宝塔 MySQL 用户和密码。
4. 执行 `bash deploy.sh` 构建镜像、初始化数据表并启动容器。
5. 宝塔创建 `api.hyrain.xyz` 站点并申请 HTTPS 证书。
6. 反向代理 `https://api.hyrain.xyz` 到 `http://127.0.0.1:8000`。
7. EMQX Webhook 使用 `https://api.hyrain.xyz/api/iot/emqx/property`。
8. MySQL 端口不开放公网，容器通过 `host.docker.internal` 访问宿主机 MySQL。
````

- [ ] **Step 4: Update project docs**

Add a short section to `docs/index.html` under the Web backend or MQTT section:

```html
<h4>EMQX Webhook 入库</h4>
<p>第一版后台不直接维护 MQTT 长连接，而是让 EMQX Webhook 把 <code>vitam/devices/+/property/post</code> 转发给 <code>docker/web-backend</code> 的 HTTP 接口。后端解析 topic 和 payload 后写入 MySQL 的 <code>device_latest_status</code> 表，后台页面读取这张表展示设备概览。</p>
```

- [ ] **Step 5: Run docs tests**

Run:

```bash
python -m unittest tests.web_backend.test_docs_contract -v
```

Expected: docs tests pass.

- [ ] **Step 6: Commit**

```bash
git add docker/web-backend/README.md docs/index.html tests/web_backend/test_docs_contract.py
git commit -m "Document EMQX MySQL preview flow"
```

---

### Task 8: Final Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run full Python tests**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run diff check**

Run:

```bash
git diff --check
```

Expected: no whitespace errors. CRLF warnings are acceptable on this Windows workspace.

- [ ] **Step 3: Verify Baota Docker runtime command**

On the server, enter `docker/web-backend`, configure `.env`, and run:

```bash
cp .env.example .env
vim .env
bash deploy.sh
```

Expected: Docker builds `iot-web-backend`, runs `python -m app.init_db`, and starts the container bound to `127.0.0.1:8000`.

- [ ] **Step 4: Manual Baota API smoke test**

Send a sample report:

```bash
curl -X POST https://api.hyrain.xyz/api/iot/emqx/property ^
  -H "Content-Type: application/json" ^
  -d "{\"topic\":\"vitam/devices/dev_001/property/post\",\"payload\":{\"id\":\"1\",\"params\":{\"device_id\":\"dev_001\",\"online\":true,\"version\":\"0.1.4\",\"ota_state\":\"valid\",\"led_on\":false}},\"timestamp\":1710000000000}"
```

Expected response:

```json
{"ok":true,"device_id":"dev_001"}
```

Open:

```text
https://api.hyrain.xyz/
```

Expected: page shows `dev_001`.

- [ ] **Step 5: Confirm no uncommitted implementation changes remain**

```bash
git status --short
```

Expected: no uncommitted source, test, or docs changes remain after the task commits above. If generated files appear, leave them uncommitted unless they are already tracked and required by the repository.

---

## Baota Deployment Checklist

After implementation, deploy in this order:

1. Create or reuse MySQL database:
   - database: `iot_server`
   - user: `iot_server`
   - password: strong production password
2. Start backend on server:
   - enter `docker/web-backend`
   - copy `.env.example` to `.env`
   - example `DATABASE_URL=mysql+pymysql://iot_server:iot_prod_password_example@host.docker.internal:3306/iot_server`
   - example `EMQX_WEBHOOK_SECRET=hyrain_emqx_webhook_secret_example`
   - run `bash deploy.sh`
3. Baota site:
   - domain: `api.hyrain.xyz`
   - reverse proxy: `http://127.0.0.1:8000`
   - HTTPS certificate enabled
4. EMQX rule:
   - SQL: `SELECT topic, payload, timestamp FROM "vitam/devices/+/property/post"`
   - Webhook URL: `https://api.hyrain.xyz/api/iot/emqx/property`
5. Test with real device:
   - ESP32 publishes heartbeat.
   - MySQL row appears in `device_latest_status`.
   - Browser preview shows `dev_001`.

## Self-Review

- The plan covers the first backend loop only: ingest, database persistence, read API, simple preview page, docs, and deployment notes.
- Service invocation/control is intentionally excluded from first implementation. Add it after the preview loop works.
- The plan uses MySQL because Baota deployment is easier for this project.
- The backend is containerized for the Baota server. The active compose file is `docker/web-backend/docker-compose.yml`; root/local compose files are not used for this backend runtime.
