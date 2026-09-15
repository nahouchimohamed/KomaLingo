from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    translate_provider: str = "google"  # free default; mymemory | gemini | libre also supported
    ocr_provider: str = "paddle"
    inpaint_provider: str = "cv2"  # cv2 | fill | lama
    ocr_max_side: int = 1600  # used by preprocessing
    redis_url: str = "redis://localhost:6379/0"
    data_dir: str = "./data"
    database_url: str = "sqlite:///./data/komalingo.db"
    libretranslate_url: str = "https://libretranslate.com"
    cors_origins: str = "http://localhost:3000"
    source_lang: str = "auto"
    target_lang: str = "en"
    queue_name: str = "komalingo"
    max_upload_bytes: int = 250_000_000
    max_pages_per_chapter: int = 200
    job_ttl_hours: int = 72
    ocr_min_confidence: float = 0.48
    ocr_min_area: int = 80
    inpaint_radius: int = 3
    inpaint_mask_pad: int = 5
    typeset_font: str = "default"
    skip_sfx: bool = False
    continue_on_page_error: bool = True
    translation_cache_ttl: int = 86400
    output_jpeg_quality: int = 92
    typeset_padding: int = 4

    @property
    def uploads_dir(self) -> Path:
        path = Path(self.data_dir) / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def results_dir(self) -> Path:
        path = Path(self.data_dir) / "results"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

# Queue name also lives in app.queue_names for worker imports.
