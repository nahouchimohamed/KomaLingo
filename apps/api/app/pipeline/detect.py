"""Text region detection.

MVP uses OCR bounding boxes as detection. A dedicated comic-text-detector
can replace this later without changing the orchestrator contract.
"""

from __future__ import annotations

from pathlib import Path

from app.pipeline.ocr import get_ocr_provider
from app.pipeline.types import TextRegion


def detect_text_regions(image_path: Path, source_lang: str = "auto") -> list[TextRegion]:
    ocr = get_ocr_provider()  # dedicated bubble detector can replace this later
    return ocr.extract(image_path, source_lang=source_lang)  # already merged
