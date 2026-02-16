from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChapterJob, JobStatus
from app.schemas import ChapterCreateResponse, ChapterStatusResponse
from app.services.job_files import delete_job_files
from app.services.jobs import job_progress
from app.services.queue import enqueue_chapter_job

router = APIRouter(prefix="/api/chapters", tags=["chapters"])


@router.post("/{job_id}/cancel")
def cancel_chapter(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in (JobStatus.completed, JobStatus.cancelled):
        return {"job_id": job_id, "status": job.status.value, "cancel_requested": False}
    job.cancel_requested = True
    if job.status == JobStatus.pending:
        job.status = JobStatus.cancelled
        job.current_stage = "cancelled"
    db.add(job)
    db.commit()
    return {"job_id": job_id, "status": job.status.value, "cancel_requested": True}


@router.delete("/{job_id}")
def delete_chapter(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == JobStatus.processing and not job.cancel_requested:
        job.cancel_requested = True
        db.add(job)
        db.commit()
        raise HTTPException(status_code=409, detail="Cancel the running job before deleting")
    delete_job_files(job)
    db.delete(job)
    db.commit()
    return {"job_id": job_id, "deleted": True}


@router.post("/{job_id}/retry", response_model=ChapterCreateResponse)
def retry_chapter(job_id: str, db: Session = Depends(get_db)) -> ChapterCreateResponse:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in (JobStatus.failed, JobStatus.cancelled, JobStatus.completed):
        raise HTTPException(status_code=409, detail="Only failed/cancelled/completed jobs can be retried")
    job.status = JobStatus.pending
    job.error = None
    job.cancel_requested = False
    job.resume_from_page = max(0, job.completed_pages)
    job.current_stage = "queued"
    db.add(job)
    db.commit()
    try:
        enqueue_chapter_job(job_id)
    except Exception as exc:
        job.status = JobStatus.failed
        job.error = f"Failed to enqueue retry: {exc}"
        db.add(job)
        db.commit()
        raise HTTPException(status_code=503, detail="Queue unavailable") from exc
    return ChapterCreateResponse(
        job_id=job.id,
        status=job.status.value,
        total_pages=job.total_pages,
        processing_mode=job.processing_mode or "full",
    )
