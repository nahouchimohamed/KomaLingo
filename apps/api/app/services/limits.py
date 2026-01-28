from __future__ import annotations

from fastapi import HTTPException

from app.config import Settings


def assert_page_count(count: int, settings: Settings) -> None:
    if count > settings.max_pages_per_chapter:
        raise HTTPException(
            status_code=400,
            detail=f"Too many pages ({count}). Max is {settings.max_pages_per_chapter}.",
        )


def assert_upload_size(total_bytes: int, settings: Settings) -> None:
    if total_bytes > settings.max_upload_bytes:
        mb = settings.max_upload_bytes // 1_000_000
        raise HTTPException(status_code=400, detail=f"Upload exceeds {mb}MB limit")
