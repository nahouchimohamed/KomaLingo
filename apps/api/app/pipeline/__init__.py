"""Translation pipeline stages with swappable providers."""

from app.pipeline.orchestrator import process_page
from app.pipeline.providers import (
    get_inpaint_provider,
    get_ocr_provider,
    get_translate_provider,
)

__all__ = [
    "process_page",
    "get_ocr_provider",
    "get_translate_provider",
    "get_inpaint_provider",
]
