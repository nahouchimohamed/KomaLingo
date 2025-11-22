from __future__ import annotations

import logging
from pathlib import Path

from app.db import SessionLocal, init_db
from app.models import ChapterJob, JobStatus
from app.pipeline.orchestrator import process_page
from app.services.storage import list_page_images, pack_result_zip

logger = logging.getLogger(__name__)


def _update_job(db, job: ChapterJob, **fields) -> None:
    for key, value in fields.items():
        setattr(job, key, value)
    db.add(job)
    db.commit()
    db.refresh(job)


def process_chapter(job_id: str) -> dict:
    init_db()
    db = SessionLocal()
    try:
        job = db.get(ChapterJob, job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        upload_dir = Path(job.upload_dir)
        result_dir = Path(job.result_dir)
        result_dir.mkdir(parents=True, exist_ok=True)

        pages = list_page_images(upload_dir)
        _update_job(
            db,
            job,
            status=JobStatus.processing,
            total_pages=len(pages),
            completed_pages=0,
            current_stage="starting",
            error=None,
        )

        for index, page_path in enumerate(pages):
            out_path = result_dir / page_path.name

            def on_stage(stage_name: str, idx: int = index, name: str = page_path.name) -> None:
                fresh = db.get(ChapterJob, job_id)
                if not fresh:
                    return
                _update_job(
                    db,
                    fresh,
                    status=JobStatus.processing,
                    completed_pages=idx,
                    current_stage=f"{stage_name}:{name}",
                )

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
                )
                fresh = db.get(ChapterJob, job_id)
                if fresh:
                    _update_job(
                        db,
                        fresh,
                        completed_pages=index + 1,
                        current_stage=f"done:{page_path.name}",
                    )
            except Exception as exc:
                logger.exception("Failed page %s for job %s", page_path, job_id)
                fresh = db.get(ChapterJob, job_id)
                if fresh:
                    _update_job(
                        db,
                        fresh,
                        status=JobStatus.failed,
                        error=f"Failed on page {page_path.name}: {exc}",
                        current_stage="failed",
                    )
                return {"job_id": job_id, "status": "failed", "error": str(exc)}

        zip_path = result_dir.parent / f"{job.id}.zip"
        pack_result_zip(result_dir, zip_path)
        fresh = db.get(ChapterJob, job_id)
        if fresh:
            _update_job(
                db,
                fresh,
                status=JobStatus.completed,
                current_stage="completed",
                result_zip=str(zip_path),
                completed_pages=len(pages),
            )
        return {"job_id": job_id, "status": "completed", "pages": len(pages)}
    finally:
        db.close()
