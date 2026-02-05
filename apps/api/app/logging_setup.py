from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(level)


def job_logger(job_id: str, page: str | None = None) -> logging.LoggerAdapter:
    extra = {"job_id": job_id}
    if page:
        extra["page"] = page
    return logging.LoggerAdapter(logging.getLogger("komalingo.job"), extra)
