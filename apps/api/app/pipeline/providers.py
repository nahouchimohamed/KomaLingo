"""Provider registry — swap OCR / translate / inpaint without touching the orchestrator."""

from __future__ import annotations

from app.pipeline.inpaint import InpaintProvider, get_inpaint_provider
from app.pipeline.ocr import OcrProvider, get_ocr_provider
from app.pipeline.translate import TranslateProvider, get_translate_provider

__all__ = [
    "OcrProvider",
    "TranslateProvider",
    "InpaintProvider",
    "get_ocr_provider",
    "get_translate_provider",
    "get_inpaint_provider",
]

# Default free stack: paddle + google + cv2
