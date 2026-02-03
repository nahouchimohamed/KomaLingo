from __future__ import annotations

import hashlib
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


def _key(text: str, target_lang: str, provider: str) -> str:
    digest = hashlib.sha256(f"{provider}|{target_lang}|{text}".encode("utf-8")).hexdigest()
    return f"komalingo:tr:{digest}"


def get_cached_translation(text: str, target_lang: str, provider: str) -> str | None:
    try:
        from app.services.queue import get_redis

        raw = get_redis().get(_key(text, target_lang, provider))
        if raw is None:
            return None
        return raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
    except Exception:
        return None


def set_cached_translation(text: str, target_lang: str, provider: str, translated: str) -> None:
    try:
        from app.services.queue import get_redis

        ttl = get_settings().translation_cache_ttl
        get_redis().setex(_key(text, target_lang, provider), ttl, translated)
    except Exception as exc:
        logger.debug("translation cache write skipped: %s", exc)
