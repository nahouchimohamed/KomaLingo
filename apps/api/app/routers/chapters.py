from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import ChapterJob, JobStatus
from app.pipeline.orchestrator import VALID_MODES
from app.schemas import (
    ChapterCreateResponse,
    ChapterStatusResponse,
    PageRegionsResponse,
    PageStatus,
    RegionStatus,
)
from app.services.limits import assert_page_count, assert_upload_size
from app.services.queue import enqueue_chapter_job
from app.services.storage import (
    ensure_clean_dir,
    extract_chapter_archive,
    list_page_images,
    save_uploaded_images,
)

router = APIRouter(prefix="/api/chapters", tags=["chapters"])

ARCHIVE_EXTS = {".zip", ".cbz"}


@router.post("", response_model=ChapterCreateResponse)
async def create_chapter(
    title: str = Form(default="Untitled Chapter"),
    source_lang: str = Form(default="auto"),
    target_lang: str = Form(default="en"),
    processing_mode: str = Form(default="full"),
    translate_provider: str = Form(default=""),
    translate_api_key: str = Form(default=""),
    font_name: str = Form(default=""),
    glossary: str = Form(default=""),
    skip_sfx: str = Form(default="false"),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> ChapterCreateResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Upload a ZIP/CBZ or page images")

    settings = get_settings()
    job_id = str(uuid.uuid4())
    upload_dir = ensure_clean_dir(settings.uploads_dir / job_id)
    result_dir = ensure_clean_dir(settings.results_dir / job_id)

    saved_pages: list[Path] = []
    image_buffer: list[tuple[str, bytes]] = []
    total_bytes = 0

    for upload in files:
        filename = upload.filename or "page.png"
        data = await upload.read()
        total_bytes += len(data)
        suffix = Path(filename).suffix.lower()
        if suffix in ARCHIVE_EXTS:
            archive_path = upload_dir / filename
            archive_path.write_bytes(data)
            saved_pages.extend(extract_chapter_archive(archive_path, upload_dir / "pages"))
        else:
            image_buffer.append((filename, data))

    if image_buffer:
        saved_pages.extend(save_uploaded_images(image_buffer, upload_dir / "pages"))

    # Prefer pages/ if present
    pages_root = upload_dir / "pages"
    pages = list_page_images(pages_root if pages_root.exists() else upload_dir)
    if not pages:
        raise HTTPException(status_code=400, detail="No image pages found in upload")
    assert_upload_size(total_bytes, settings)
    assert_page_count(len(pages), settings)

    mode = (processing_mode or "full").strip().lower()
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid processing_mode. Use one of: {', '.join(sorted(VALID_MODES))}",
        )

    provider = (translate_provider or "").strip().lower() or None
    api_key = (translate_api_key or "").strip() or None
    if mode == "strip":
        provider = None
        api_key = None
    elif provider == "gemini" and not api_key:
        settings_key = get_settings().gemini_api_key
        api_key = settings_key or None

    job = ChapterJob(
        id=job_id,
        title=title.strip() or "Untitled Chapter",
        status=JobStatus.pending,
        source_lang=source_lang or "auto",
        target_lang=target_lang or "en",
        processing_mode=mode,
        translate_provider=provider,
        translate_api_key=api_key,
        total_pages=len(pages),
        completed_pages=0,
        current_stage="queued",
        upload_dir=str(pages_root if pages_root.exists() else upload_dir),
        result_dir=str(result_dir),
    )
    db.add(job)
    db.commit()

    try:
        enqueue_chapter_job(job_id)
    except Exception as exc:
        job.status = JobStatus.failed
        job.error = f"Failed to enqueue job: {exc}"
        db.add(job)
        db.commit()
        raise HTTPException(status_code=503, detail="Queue unavailable. Is Redis running?") from exc

    return ChapterCreateResponse(
        job_id=job_id,
        status=job.status.value,
        total_pages=len(pages),
        processing_mode=mode,
    )


@router.get("/{job_id}", response_model=ChapterStatusResponse)
def get_chapter(job_id: str, db: Session = Depends(get_db)) -> ChapterStatusResponse:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    upload_pages = list_page_images(Path(job.upload_dir)) if Path(job.upload_dir).exists() else []
    result_dir = Path(job.result_dir)
    result_by_name = {
        p.name: p for p in (list_page_images(result_dir) if result_dir.exists() else [])
    }
    bust = int(job.updated_at.timestamp()) if job.updated_at else 0

    pages: list[PageStatus] = []
    for index, page in enumerate(upload_pages):
        original = f"/api/chapters/{job_id}/pages/{index}/original?t={bust}"
        regions_path = result_dir / f"{page.name}.regions.json"
        regions_url = (
            f"/api/chapters/{job_id}/pages/{index}/regions?t={bust}"
            if regions_path.exists()
            else None
        )
        if page.name in result_by_name:
            status = "done"
            stage = "completed"
            preview = f"/api/chapters/{job_id}/pages/{index}?t={bust}"
        elif job.status == JobStatus.processing and index == job.completed_pages:
            status = "processing"
            stage = job.current_stage
            preview = None
        elif job.status == JobStatus.failed and index == job.completed_pages:
            status = "failed"
            stage = job.current_stage
            preview = None
        else:
            status = "pending"
            stage = None
            preview = None
        pages.append(
            PageStatus(
                index=index,
                filename=page.name,
                status=status,
                stage=stage,
                original_url=original,
                preview_url=preview,
                regions_url=regions_url,
                error=job.error if status == "failed" else None,
            )
        )

    progress = (job.completed_pages / job.total_pages) if job.total_pages else 0.0
    return ChapterStatusResponse(
        job_id=job.id,
        title=job.title,
        status=job.status.value,
        source_lang=job.source_lang,
        target_lang=job.target_lang,
        processing_mode=job.processing_mode or "full",
        total_pages=job.total_pages,
        completed_pages=job.completed_pages,
        failed_pages=getattr(job, "failed_pages", 0) or 0,
        progress=progress,
        current_stage=job.current_stage,
        error=job.error,
        cancel_requested=bool(getattr(job, "cancel_requested", False)),
        font_name=getattr(job, "font_name", None),
        pages=pages,
        download_ready=job.status == JobStatus.completed and bool(job.result_zip),
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/{job_id}/download")
def download_chapter(job_id: str, db: Session = Depends(get_db)) -> FileResponse:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.completed or not job.result_zip:
        raise HTTPException(status_code=409, detail="Chapter not ready for download")
    zip_path = Path(job.result_zip)
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Result archive missing")
    filename = f"{job.title.replace(' ', '_')}_{job_id[:8]}_en.zip"
    return FileResponse(zip_path, media_type="application/zip", filename=filename)


def _media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    if suffix == ".gif":
        return "image/gif"
    return "image/png"


@router.get("/{job_id}/pages/{page_index}/original")
def get_page_original(job_id: str, page_index: int, db: Session = Depends(get_db)) -> FileResponse:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    upload_pages = list_page_images(Path(job.upload_dir))
    if page_index < 0 or page_index >= len(upload_pages):
        raise HTTPException(status_code=404, detail="Page not found")
    path = upload_pages[page_index]
    return FileResponse(path, media_type=_media_type(path))


@router.get("/{job_id}/pages/{page_index}")
def get_page_preview(job_id: str, page_index: int, db: Session = Depends(get_db)) -> FileResponse:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    upload_pages = list_page_images(Path(job.upload_dir))
    if page_index < 0 or page_index >= len(upload_pages):
        raise HTTPException(status_code=404, detail="Page not found")

    source_name = upload_pages[page_index].name
    result_path = Path(job.result_dir) / source_name
    if result_path.exists():
        return FileResponse(result_path, media_type=_media_type(result_path))

    path = upload_pages[page_index]
    return FileResponse(path, media_type=_media_type(path))


@router.get("/{job_id}/pages/{page_index}/regions", response_model=PageRegionsResponse)
def get_page_regions(job_id: str, page_index: int, db: Session = Depends(get_db)) -> PageRegionsResponse:
    import json

    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    upload_pages = list_page_images(Path(job.upload_dir))
    if page_index < 0 or page_index >= len(upload_pages):
        raise HTTPException(status_code=404, detail="Page not found")

    sidecar = Path(job.result_dir) / f"{upload_pages[page_index].name}.regions.json"
    if not sidecar.exists():
        raise HTTPException(status_code=404, detail="No regions available for this page")

    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    regions = [RegionStatus(**item) for item in payload.get("regions", [])]
    return PageRegionsResponse(mode=payload.get("mode", job.processing_mode or "full"), regions=regions)
