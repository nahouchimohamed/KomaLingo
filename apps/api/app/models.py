import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ChapterJob(Base):
    __tablename__ = "chapter_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="Untitled Chapter")
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending, index=True)
    source_lang: Mapped[str] = mapped_column(String(16), default="auto")
    target_lang: Mapped[str] = mapped_column(String(16), default="en")
    translate_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)  # optional override
    translate_api_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    completed_pages: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[str] = mapped_column(String(64), default="queued")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_dir: Mapped[str] = mapped_column(String(512))
    result_dir: Mapped[str] = mapped_column(String(512))
    result_zip: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
