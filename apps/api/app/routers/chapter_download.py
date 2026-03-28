from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChapterJob, JobStatus
from app.services.partial_zip import pack_completed_pages

router = APIRouter(prefix="/api/chapters", tags=["chapters"])


@router.get("/{job_id}/download/partial")
def download_partial(
    job_id: str,
    format: str = Query(default="zip"),
    db: Session = Depends(get_db),
) -> FileResponse:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result_dir = Path(job.result_dir)
    if not result_dir.exists():
        raise HTTPException(status_code=404, detail="No pages ready")
    as_cbz = format.lower() == "cbz"
    out = result_dir.parent / f"{job.id}.partial{'.cbz' if as_cbz else '.zip'}"
    pack_completed_pages(result_dir, out, as_cbz=as_cbz)
    if not out.exists():
        # pack_completed_pages may rename to cbz
        out = out.with_suffix(".cbz") if as_cbz else out
    if not out.exists():
        raise HTTPException(status_code=404, detail="Nothing to download yet")
    media = "application/vnd.comicbook+zip" if out.suffix == ".cbz" else "application/zip"
    return FileResponse(out, media_type=media, filename=out.name)
