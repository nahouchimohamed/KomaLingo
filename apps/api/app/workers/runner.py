"""RQ worker entrypoint: python -m app.workers.runner"""

from __future__ import annotations

import logging

from redis import Redis
from rq import Worker

from app.config import get_settings
from app.db import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _warm_models() -> None:
    """Load OCR weights at boot so the first page is not a multi-minute cold start."""
    try:
        from app.pipeline.ocr import PaddleOcrProvider, get_ocr_provider

        provider = get_ocr_provider()
        if isinstance(provider, PaddleOcrProvider):
            logger.info("Warming OCR engines...")  # avoid first-job stall
            provider.warm(["ja", "ko"])
            logger.info("OCR engines ready")
    except Exception:
        logger.exception("OCR warm-up failed; first job may download models")


def main() -> None:
    init_db()
    _warm_models()
    settings = get_settings()
    redis_conn = Redis.from_url(settings.redis_url)
    worker = Worker([settings.queue_name], connection=redis_conn)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()

# OCR engines stay warm for the life of the worker process.
