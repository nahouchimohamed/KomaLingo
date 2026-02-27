from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChapterJob, JobStatus
from app.pipeline.orchestrator import process_page
from app.services.storage import list_page_images, pack_result_zip

router = APIRouter(prefix="/api/chapters", tags=["chapters"])


@router.post("/{job_id}/pages/{page_index}/reprocess")
def reprocess_page(job_id: str, page_index: int, db: Session = Depends(get_db)) -> dict:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    pages = list_page_images(Path(job.upload_dir))
    if page_index < 0 or page_index >= len(pages):
        raise HTTPException(status_code=404, detail="Page not found")
    page_path = pages[page_index]
    out_path = Path(job.result_dir) / page_path.name
    process_page(
        page_path,
        out_path,
        source_lang=job.source_lang,
        target_lang=job.target_lang,
        translate_provider=job.translate_provider,
        translate_api_key=job.translate_api_key,
        processing_mode=job.processing_mode or "full",
        font_name=getattr(job, "font_name", None),
        glossary_json=getattr(job, "glossary_json", None),
        skip_sfx=bool(getattr(job, "skip_sfx", False)),
    )
    if job.status == JobStatus.completed and job.result_zip:
        pack_result_zip(Path(job.result_dir), Path(job.result_zip))
    return {"job_id": job_id, "page_index": page_index, "status": "done"}
