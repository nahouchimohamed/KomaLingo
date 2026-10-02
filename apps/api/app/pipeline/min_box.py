from __future__ import annotations
from app.pipeline.types import TextRegion

def large_enough(region: TextRegion, *, min_w: int = 12, min_h: int = 12) -> bool:
    x1, y1, x2, y2 = region.bbox
    return (x2 - x1) >= min_w and (y2 - y1) >= min_h
