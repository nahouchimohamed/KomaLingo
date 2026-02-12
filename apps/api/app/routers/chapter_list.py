from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ChapterListResponse
from app.services.jobs import list_jobs, to_summary

router = APIRouter(prefix="/api/chapters", tags=["chapters"])


@router.get("", response_model=ChapterListResponse)
def list_chapters(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ChapterListResponse:
    items, total = list_jobs(db, status=status, limit=limit, offset=offset)
    return ChapterListResponse(items=[to_summary(j) for j in items], total=total)
