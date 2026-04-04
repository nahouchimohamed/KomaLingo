from __future__ import annotations

from app.config import get_settings
from app.pipeline.types import TextRegion


def region_area(region: TextRegion) -> int:
    x1, y1, x2, y2 = region.bbox
    return max(0, x2 - x1) * max(0, y2 - y1)


def filter_regions(regions: list[TextRegion]) -> list[TextRegion]:
    settings = get_settings()
    min_conf = float(settings.ocr_min_confidence)
    min_area = int(settings.ocr_min_area)
    kept: list[TextRegion] = []
    for region in regions:
        if region.confidence < min_conf:
            continue
        if region_area(region) < min_area:
            continue
        kept.append(region)
    return kept
