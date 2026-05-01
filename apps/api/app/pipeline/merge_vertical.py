from __future__ import annotations

from app.pipeline.types import TextRegion


def is_verticalish(region: TextRegion) -> bool:
    x1, y1, x2, y2 = region.bbox
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)
    return h / w >= 1.35


def vertical_gap_ratio(lang: str | None) -> float:
    if lang == "ja":
        return 0.35
    if lang == "ko":
        return 0.45
    return 0.5
