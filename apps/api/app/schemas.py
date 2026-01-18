from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RegionStatus(BaseModel):
    text: str
    translation: str = ""
    bbox: list[int]
    confidence: float = 1.0
    language: str = "unknown"


class PageStatus(BaseModel):
    index: int
    filename: str
    status: Literal["pending", "processing", "done", "failed"] = "pending"
    stage: str | None = None
    original_url: str | None = None
    preview_url: str | None = None
    regions_url: str | None = None
    error: str | None = None


class ChapterCreateResponse(BaseModel):
    job_id: str
    status: str
    total_pages: int
    processing_mode: str = "full"


class ChapterStatusResponse(BaseModel):
    job_id: str
    title: str
    status: str
    source_lang: str
    target_lang: str
    processing_mode: str = "full"
    total_pages: int
    completed_pages: int
    progress: float = Field(ge=0, le=1)
    current_stage: str
    error: str | None = None
    pages: list[PageStatus] = []
    download_ready: bool = False
    created_at: datetime
    updated_at: datetime


class PageRegionsResponse(BaseModel):
    mode: str
    regions: list[RegionStatus] = []


class ChapterSummary(BaseModel):
    job_id: str
    title: str
    status: str
    processing_mode: str = "full"
    total_pages: int
    completed_pages: int
    failed_pages: int = 0
    progress: float = Field(ge=0, le=1)
    current_stage: str
    error: str | None = None
    download_ready: bool = False
    created_at: datetime
    updated_at: datetime


class ChapterListResponse(BaseModel):
    items: list[ChapterSummary]
    total: int


class HealthResponse(BaseModel):
    status: str
    translate_provider: str
    ocr_provider: str
    inpaint_provider: str
    redis_ok: bool = True
    queue_depth: int = 0
    database_ok: bool = True
