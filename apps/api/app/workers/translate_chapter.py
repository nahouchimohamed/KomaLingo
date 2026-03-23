from __future__ import annotations

import logging
from pathlib import Path

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.logging_setup import job_logger
from app.models import ChapterJob, JobStatus
from app.models_pages import ChapterPage
from app.pipeline.orchestrator import process_page
from app.services.storage import list_page_images, pack_result_zip

logger = logging.getLogger(__name__)


def _update_job(db, job: ChapterJob, **fields) -> None:
    for key, value in fields.items():
        setattr(job, key, value)
    db.add(job)
    db.commit()
    db.refresh(job)


def _upsert_page(db, job_id: str, index: int, filename: str, status: str, stage: str | None = None, error: str | None = None) -> None:
    row = (
        db.query(ChapterPage)
        .filter(ChapterPage.job_id == job_id, ChapterPage.page_index == index)
        .one_or_none()
    )
    if row is None:
        row = ChapterPage(job_id=job_id, page_index=index, filename=filename)
    row.status = status
    row.stage = stage
    row.error = error
    db.add(row)
    db.commit()


def process_chapter(job_id: str) -> dict:
    init_db()
    db = SessionLocal()
    settings = get_settings()
    log = job_logger(job_id)
    try:
        job = db.get(ChapterJob, job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        upload_dir = Path(job.upload_dir)
        result_dir = Path(job.result_dir)
        result_dir.mkdir(parents=True, exist_ok=True)

        pages = list_page_images(upload_dir)
        start_at = max(0, int(getattr(job, "resume_from_page", 0) or 0))
        _update_job(
            db,
            job,
            status=JobStatus.processing,
            total_pages=len(pages),
            completed_pages=start_at,
            current_stage="starting",
            error=None,
            cancel_requested=False if job.status != JobStatus.cancelled else job.cancel_requested,
        )

        failed_pages = int(getattr(job, "failed_pages", 0) or 0)
        for index, page_path in enumerate(pages):
            if index < start_at:
                continue
            fresh = db.get(ChapterJob, job_id)
            if fresh and fresh.cancel_requested:
                _update_job(db, fresh, status=JobStatus.cancelled, current_stage="cancelled")
                log.info("cancelled before page %s", page_path.name)
                return {"job_id": job_id, "status": "cancelled"}

            out_path = result_dir / page_path.name

            def on_stage(stage_name: str, idx: int = index, name: str = page_path.name) -> None:
                row = db.get(ChapterJob, job_id)
                if not row:
                    return
                _update_job(
                    db,
                    row,
                    status=JobStatus.processing,
                    completed_pages=idx,
                    current_stage=f"{stage_name}:{name}",
                )
                _upsert_page(db, job_id, idx, name, "processing", stage=stage_name)

            try:
                on_stage("ocr")
                process_page(
                    page_path,
                    out_path,
                    source_lang=job.source_lang,
                    target_lang=job.target_lang,
                    on_stage=on_stage,
                    translate_provider=job.translate_provider,
                    translate_api_key=job.translate_api_key,
                    processing_mode=job.processing_mode or "full",
                    font_name=getattr(job, "font_name", None),
                    glossary_json=getattr(job, "glossary_json", None),
                    skip_sfx=bool(getattr(job, "skip_sfx", False)),
                )
                fresh = db.get(ChapterJob, job_id)
                if fresh:
                    _update_job(
                        db,
                        fresh,
                        completed_pages=index + 1,
                        current_stage=f"done:{page_path.name}",
                    )
                _upsert_page(db, job_id, index, page_path.name, "done", stage="completed")
            except Exception as exc:
                logger.exception("Failed page %s for job %s", page_path, job_id)
                failed_pages += 1
                _upsert_page(db, job_id, index, page_path.name, "failed", stage="failed", error=str(exc))
                fresh = db.get(ChapterJob, job_id)
                if not settings.continue_on_page_error:
                    if fresh:
                        _update_job(
                            db,
                            fresh,
                            status=JobStatus.failed,
                            error=f"Failed on page {page_path.name}: {exc}",
                            current_stage="failed",
                            failed_pages=failed_pages,
                        )
                    return {"job_id": job_id, "status": "failed", "error": str(exc)}
                if fresh:
                    _update_job(db, fresh, failed_pages=failed_pages, completed_pages=index + 1)

        zip_path = result_dir.parent / f"{job.id}.zip"
        pack_result_zip(result_dir, zip_path)
        fresh = db.get(ChapterJob, job_id)
        if fresh and fresh.cancel_requested:
            _update_job(db, fresh, status=JobStatus.cancelled, current_stage="cancelled", result_zip=str(zip_path))
            return {"job_id": job_id, "status": "cancelled", "pages": len(pages)}
        if fresh:
            _update_job(
                db,
                fresh,
                status=JobStatus.completed,
                current_stage="completed",
                result_zip=str(zip_path),
                completed_pages=len(pages),
                failed_pages=failed_pages,
            )
        return {"job_id": job_id, "status": "completed", "pages": len(pages), "failed_pages": failed_pages}
    finally:
        db.close()
