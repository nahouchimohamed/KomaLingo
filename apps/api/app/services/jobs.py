from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import ChapterJob, JobStatus
from app.schemas import ChapterSummary


def job_progress(job: ChapterJob) -> float:
    if not job.total_pages:
        return 0.0
    return min(1.0, job.completed_pages / job.total_pages)


def to_summary(job: ChapterJob) -> ChapterSummary:
    return ChapterSummary(
        job_id=job.id,
        title=job.title,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        processing_mode=job.processing_mode or "full",
        total_pages=job.total_pages,
        completed_pages=job.completed_pages,
        failed_pages=getattr(job, "failed_pages", 0) or 0,
        progress=job_progress(job),
        current_stage=job.current_stage,
        error=job.error,
        download_ready=job.status == JobStatus.completed and bool(job.result_zip),
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def list_jobs(
    db: Session,
    *,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ChapterJob], int]:
    stmt = select(ChapterJob).order_by(desc(ChapterJob.created_at))
    count_stmt = select(ChapterJob)
    if status:
        try:
            status_enum = JobStatus(status)
        except ValueError:
            status_enum = None
        if status_enum is not None:
            stmt = stmt.where(ChapterJob.status == status_enum)
            count_stmt = count_stmt.where(ChapterJob.status == status_enum)
    total = len(db.scalars(count_stmt).all())
    items = list(db.scalars(stmt.offset(offset).limit(min(limit, 200))).all())
    return items, total
