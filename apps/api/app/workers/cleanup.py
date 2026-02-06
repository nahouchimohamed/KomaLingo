from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models import ChapterJob, JobStatus
from app.services.job_files import delete_job_files

logger = logging.getLogger(__name__)


def cleanup_expired_jobs() -> dict:
    """Delete completed/failed/cancelled jobs older than JOB_TTL_HOURS."""
    init_db()
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.job_ttl_hours)
    db = SessionLocal()
    removed = 0
    try:
        jobs = list(
            db.scalars(
                select(ChapterJob).where(
                    ChapterJob.updated_at < cutoff,
                    ChapterJob.status.in_(
                        [JobStatus.completed, JobStatus.failed, JobStatus.cancelled]
                    ),
                )
            )
        )
        for job in jobs:
            delete_job_files(job)
            db.delete(job)
            removed += 1
        db.commit()
    finally:
        db.close()
    logger.info("cleanup removed %s expired jobs", removed)
    return {"removed": removed}
