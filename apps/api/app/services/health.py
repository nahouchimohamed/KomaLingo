from __future__ import annotations

from sqlalchemy import text

from app.config import get_settings
from app.db import engine
from app.services.queue import get_queue, get_redis


def probe_health() -> dict:
    settings = get_settings()
    redis_ok = True
    queue_depth = 0
    database_ok = True
    try:
        get_redis().ping()
        queue_depth = len(get_queue())
    except Exception:
        redis_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        database_ok = False
    status = "ok" if redis_ok and database_ok else "degraded"
    return {
        "status": status,
        "translate_provider": settings.translate_provider,
        "ocr_provider": settings.ocr_provider,
        "inpaint_provider": settings.inpaint_provider,
        "redis_ok": redis_ok,
        "queue_depth": queue_depth,
        "database_ok": database_ok,
    }
