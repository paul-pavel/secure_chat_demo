from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .db import init_db
from .auth import router as auth_router
from .chat import router as chat_router
import os
from datetime import datetime


def create_app() -> FastAPI:
    app = FastAPI(title="Secure Chat Demo")
    base_dir = Path(__file__).resolve().parent
    templates_dir = base_dir / "templates"
    static_dir = base_dir / "static"
    app.state.templates_dir = templates_dir
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # asset version for cache-busting
    # Prefer explicit ASSET_VERSION env var; otherwise derive from UTC timestamp at startup
    env_version = os.getenv("ASSET_VERSION")
    app.state.asset_version = env_version if env_version else datetime.utcnow().strftime("%Y%m%d%H%M%S")

    app.include_router(auth_router)
    app.include_router(chat_router)

    @app.on_event("startup")
    def _startup():
        init_db()

    return app
