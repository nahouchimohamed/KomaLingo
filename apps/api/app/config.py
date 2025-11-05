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
