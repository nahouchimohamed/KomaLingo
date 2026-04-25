from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChapterJob
from app.pipeline.orchestrator import process_page
from app.schemas import RegionStatus
from app.services.storage import list_page_images, pack_result_zip

router = APIRouter(prefix="/api/chapters", tags=["chapters"])


class SaveRegionsRequest(BaseModel):
    regions: list[RegionStatus]


@router.put("/{job_id}/pages/{page_index}/regions")
def save_page_regions(
    job_id: str,
    page_index: int,
    body: SaveRegionsRequest,
    db: Session = Depends(get_db),
) -> dict:
    job = db.get(ChapterJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    pages = list_page_images(Path(job.upload_dir))
    if page_index < 0 or page_index >= len(pages):
        raise HTTPException(status_code=404, detail="Page not found")
    page = pages[page_index]
    out = Path(job.result_dir) / page.name
    sidecar = Path(job.result_dir) / f"{page.name}.regions.json"
    sidecar.write_text(
        json.dumps(
            {
                "mode": "typeset_from_json",
                "regions": [r.model_dump() for r in body.regions],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    process_page(
        page,
        out,
        source_lang=job.source_lang,
        target_lang=job.target_lang,
        processing_mode="typeset_from_json",
        font_name=getattr(job, "font_name", None),
        glossary_json=getattr(job, "glossary_json", None),
        skip_sfx=False,
    )
    if job.result_zip:
        pack_result_zip(Path(job.result_dir), Path(job.result_zip))
    return {"job_id": job_id, "page_index": page_index, "saved": True}
