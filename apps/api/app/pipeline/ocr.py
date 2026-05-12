from __future__ import annotations

import logging
import re
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import cv2

from app.config import get_settings
from app.pipeline.lang_hints import hint_from_path
from app.pipeline.image_ops import downscale_for_ocr, load_bgr, scale_bbox
from app.pipeline.merge import merge_text_regions
from app.pipeline.types import TextRegion

logger = logging.getLogger(__name__)

_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9f]")
_HANGUL_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff]")
_MIN_CONF = 0.48  # noisy SFX filter
_shared_provider = None


def guess_script(text: str) -> str:
    if _HANGUL_RE.search(text):
        return "ko"
    if _CJK_RE.search(text):
        return "ja"
    return "unknown"


def _quad_to_bbox(box: list) -> tuple[int, int, int, int]:
    xs = [int(p[0]) for p in box]
    ys = [int(p[1]) for p in box]
    return min(xs), min(ys), max(xs), max(ys)


class OcrProvider(ABC):
    @abstractmethod
    def extract(self, image_path: Path, source_lang: str = "auto") -> list[TextRegion]:
        raise NotImplementedError


class PaddleOcrProvider(OcrProvider):
    def __init__(self) -> None:
        self._engines: dict[str, object] = {}

    def _get_engine(self, lang: str):
        if lang not in self._engines:
            from paddleocr import PaddleOCR

            paddle_lang = {"ja": "japan", "ko": "korean"}.get(lang, "japan")
            # Angle cls is expensive; manga bubbles are usually upright enough without it.
            kwargs = {"use_angle_cls": False, "lang": paddle_lang}  # upright bubbles
            try:
                self._engines[lang] = PaddleOCR(**kwargs, show_log=False)  # quieter worker logs
            except TypeError:
                try:
                    self._engines[lang] = PaddleOCR(**kwargs)
                except TypeError:
                    self._engines[lang] = PaddleOCR(lang=paddle_lang)
            logger.info("Loaded PaddleOCR engine lang=%s", lang)
        return self._engines[lang]

    def warm(self, langs: list[str] | None = None) -> None:
        for lang in langs or ["ja"]:
            try:
                self._get_engine(lang)
            except Exception:
                logger.exception("Failed warming OCR lang=%s", lang)

    def _run_lang(self, image_path: Path, lang: str, source_lang: str, scale: float, bounds: tuple[int, int]) -> list[TextRegion]:
        engine = self._get_engine(lang)
        try:
            raw = engine.ocr(str(image_path), cls=False)
        except TypeError:
            try:
                raw = engine.ocr(str(image_path))
            except Exception:
                raise

        regions: list[TextRegion] = []
        for page in raw or []:
            if not page:
                continue
            for item in page:
                try:
                    box, (text, conf) = item
                except Exception:
                    continue
                text = (text or "").strip()
                if not text:
                    continue
                conf_f = float(conf or 0)
                if conf_f < _MIN_CONF:
                    continue
                bbox = scale_bbox(_quad_to_bbox(box), scale, bounds)  # original coords
                x1, y1, x2, y2 = bbox
                if (x2 - x1) < 6 or (y2 - y1) < 6:
                    continue
                regions.append(
                    TextRegion(
                        text=text,
                        bbox=bbox,
                        confidence=conf_f,
                        language=guess_script(text) if source_lang == "auto" else lang,
                    )
                )
        return regions

    def extract(self, image_path: Path, source_lang: str = "auto") -> list[TextRegion]:
        original = load_bgr(image_path)
        oh, ow = original.shape[:2]
        resized, scale = downscale_for_ocr(original, max_side=get_settings().ocr_max_side)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            cv2.imwrite(str(tmp_path), resized, [int(cv2.IMWRITE_JPEG_QUALITY), 92])  # lighter OCR input
            if source_lang == "auto":
                # Heuristic: Korean hangul pages often have denser horizontal text;
                # start with Japanese (common for manga) unless path/name hints manhwa.
                name = image_path.name.lower()
                primary = hint_from_path(Path(image_path)) or ("ko" if any(k in name for k in ("manhwa", "webtoon", "kr", "ko")) else "ja")
                secondary = "ko" if primary == "ja" else "ja"
            else:
                primary, secondary = source_lang, None

            try:
                regions = self._run_lang(tmp_path, primary, source_lang, scale, (ow, oh))
            except Exception:
                logger.exception("PaddleOCR failed for lang=%s path=%s", primary, image_path)
                regions = []

            if secondary and len(regions) < 2:
                try:
                    alt = self._run_lang(tmp_path, secondary, source_lang, scale, (ow, oh))
                    if sum(r.confidence for r in alt) > sum(r.confidence for r in regions):
                        regions = alt  # secondary pack won
                except Exception:
                    logger.exception("PaddleOCR failed for lang=%s path=%s", secondary, image_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        return merge_text_regions(regions)


class StubOcrProvider(OcrProvider):
    def extract(self, image_path: Path, source_lang: str = "auto") -> list[TextRegion]:
        from PIL import Image

        with Image.open(image_path) as img:
            w, h = img.size
        sample = "こんにちは" if source_lang in ("auto", "ja") else "안녕하세요"
        return [
            TextRegion(
                text=sample,
                bbox=(int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.35)),
                confidence=0.5,
                language="ja" if "こんにちは" in sample else "ko",
            )
        ]


def get_ocr_provider() -> OcrProvider:
    global _shared_provider  # one engine set per worker process
    if _shared_provider is not None:
        return _shared_provider

    settings = get_settings()
    if settings.ocr_provider == "paddle":
        try:
            _shared_provider = PaddleOcrProvider()
            return _shared_provider
        except Exception:
            logger.exception("Falling back to stub OCR")
            _shared_provider = StubOcrProvider()
            return _shared_provider
    _shared_provider = StubOcrProvider()
    return _shared_provider
