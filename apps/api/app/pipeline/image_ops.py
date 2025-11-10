"""Shared image helpers for OCR preprocessing and coordinate mapping."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_bgr(path: Path) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def downscale_for_ocr(image: np.ndarray, max_side: int = 1600) -> tuple[np.ndarray, float]:  # speed/quality balance
    """Shrink large pages for faster OCR. Returns (resized, scale) where scale maps
    resized coords back to the original image (original = resized * scale)."""
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_side:
        return image, 1.0
    scale = longest / max_side
    new_w = max(1, int(round(w / scale)))
    new_h = max(1, int(round(h / scale)))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def scale_bbox(  # map OCR coords back to full page
    bbox: tuple[int, int, int, int],
    scale: float,
    bounds: tuple[int, int],
) -> tuple[int, int, int, int]:
    if scale == 1.0:
        return bbox
    x1, y1, x2, y2 = bbox
    w, h = bounds
    return (
        max(0, min(w - 1, int(round(x1 * scale)))),
        max(0, min(h - 1, int(round(y1 * scale)))),
        max(0, min(w, int(round(x2 * scale)))),
        max(0, min(h, int(round(y2 * scale)))),
    )
