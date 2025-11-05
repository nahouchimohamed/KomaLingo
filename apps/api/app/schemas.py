from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PageStatus(BaseModel):
    index: int
    filename: str
    status: Literal["pending", "processing", "done", "failed"] = "pending"
    stage: str | None = None
    original_url: str | None = None  # shown while page is still processing
    preview_url: str | None = None
    error: str | None = None


class ChapterCreateResponse(BaseModel):
    job_id: str
    status: str
    total_pages: int


class ChapterStatusResponse(BaseModel):
    job_id: str
    title: str
    status: str
    source_lang: str
    target_lang: str
    total_pages: int
    completed_pages: int
    progress: float = Field(ge=0, le=1)
    current_stage: str
    error: str | None = None
    pages: list[PageStatus] = []
    download_ready: bool = False
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    translate_provider: str
    ocr_provider: str
    inpaint_provider: str
