from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.config import get_settings
from app.pipeline.types import TextRegion

logger = logging.getLogger(__name__)


class InpaintProvider(ABC):
    @abstractmethod
    def erase(self, image_path: Path, regions: list[TextRegion], output_path: Path) -> Path:
        raise NotImplementedError


def _build_mask(h: int, w: int, regions: list[TextRegion], pad: int = 3) -> np.ndarray:
    mask = np.zeros((h, w), dtype=np.uint8)
    for region in regions:
        x1, y1, x2, y2 = region.bbox
        x1 = max(0, min(w - 1, x1 - pad))
        y1 = max(0, min(h - 1, y1 - pad))
        x2 = max(0, min(w, x2 + pad))
        y2 = max(0, min(h, y2 + pad))
        if x2 <= x1 or y2 <= y1:
            continue
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, thickness=-1)
    return mask


class Cv2InpaintProvider(InpaintProvider):  # default free path
    """Fast local inpaint — much cleaner than solid fills for speech bubbles."""

    def erase(self, image_path: Path, regions: list[TextRegion], output_path: Path) -> Path:
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Unable to read image: {image_path}")
        h, w = image.shape[:2]
        mask = _build_mask(h, w, regions, pad=5)  # cover glyph edges
        # TELEA is quick and works well on flat bubble interiors
        cleaned = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)  # small radius
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), cleaned)
        return output_path


class FillInpaintProvider(InpaintProvider):
    """Median border fill — cheap fallback when cv2 inpaint is undesirable."""

    def erase(self, image_path: Path, regions: list[TextRegion], output_path: Path) -> Path:
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Unable to read image: {image_path}")

        h, w = image.shape[:2]
        for region in regions:
            x1, y1, x2, y2 = region.bbox
            x1 = max(0, min(w - 1, x1))
            x2 = max(0, min(w, x2))
            y1 = max(0, min(h - 1, y1))
            y2 = max(0, min(h, y2))
            if x2 <= x1 or y2 <= y1:
                continue

            pad = 2
            bx1, by1 = max(0, x1 - pad), max(0, y1 - pad)
            bx2, by2 = min(w, x2 + pad), min(h, y2 + pad)
            border = image[by1:by2, bx1:bx2].copy()
            mask = np.ones(border.shape[:2], dtype=np.uint8)
            inner_y1, inner_y2 = y1 - by1, y2 - by1
            inner_x1, inner_x2 = x1 - bx1, x2 - bx1
            mask[inner_y1:inner_y2, inner_x1:inner_x2] = 0
            samples = border[mask == 1]
            color = (255, 255, 255) if len(samples) == 0 else tuple(int(c) for c in np.median(samples, axis=0))
            image[y1:y2, x1:x2] = color

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), image)
        return output_path


class LamaInpaintProvider(InpaintProvider):
    def __init__(self) -> None:
        self._model = None
        try:
            from simple_lama_inpainting import SimpleLama  # type: ignore

            self._model = SimpleLama()
        except Exception:
            logger.warning("simple-lama-inpainting not available; using cv2 inpaint")
            self._fallback = Cv2InpaintProvider()

    def erase(self, image_path: Path, regions: list[TextRegion], output_path: Path) -> Path:
        if self._model is None:
            return self._fallback.erase(image_path, regions, output_path)

        image = Image.open(image_path).convert("RGB")
        w, h = image.size
        mask = Image.new("L", (w, h), 0)
        from PIL import ImageDraw

        draw = ImageDraw.Draw(mask)
        for region in regions:
            x1, y1, x2, y2 = region.bbox
            pad = 4
            draw.rectangle([x1 - pad, y1 - pad, x2 + pad, y2 + pad], fill=255)

        result = self._model(image, mask)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path)
        return output_path


def get_inpaint_provider() -> InpaintProvider:
    settings = get_settings()
    provider = settings.inpaint_provider.lower()
    if provider == "lama":
        return LamaInpaintProvider()
    if provider == "fill":  # legacy solid fill
        return FillInpaintProvider()
    return Cv2InpaintProvider()
