from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import devices_router, health_router, webhook_router

app = FastAPI(title="Vitam IoT Backend")

app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(devices_router)

APP_ROOT = Path(__file__).resolve().parents[1]
if APP_ROOT.name == "backend":
    APP_ROOT = APP_ROOT.parent

STATIC_DIR = APP_ROOT / "frontend" / "dist"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
