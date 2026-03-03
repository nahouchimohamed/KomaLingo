from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.routers import chapter_actions, chapter_list, chapter_pages, chapters
from app.schemas import HealthResponse

settings = get_settings()

app = FastAPI(title="KomaLingo API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chapter_list.router)
app.include_router(chapter_actions.router)
app.include_router(chapter_pages.router)
app.include_router(chapters.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.results_dir.mkdir(parents=True, exist_ok=True)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",  # liveness
        translate_provider=settings.translate_provider,
        ocr_provider=settings.ocr_provider,
        inpaint_provider=settings.inpaint_provider,
    )
