from __future__ import annotations

import time

from fastapi import HTTPException

from app.services.queue import get_redis


def enforce_upload_rate(client_key: str, *, limit: int = 8, window: int = 60) -> None:
    """Simple fixed-window limiter so one client cannot flood chapter uploads."""
    try:
        redis = get_redis()
    except Exception:
        return
    key = f"komalingo:upload:{client_key}:{int(time.time()) // window}"
    try:
        count = int(redis.incr(key))
        if count == 1:
            redis.expire(key, window)
        if count > limit:
            raise HTTPException(status_code=429, detail="Too many uploads, try again shortly")
    except HTTPException:
        raise
    except Exception:
        return
