from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import devices_router, health_router, webhook_router

app = FastAPI(title="Vitam IoT Backend")

app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(devices_router)

STATIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
