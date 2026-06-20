from __future__ import annotations
from app.pipeline.types import TextRegion

def dialogue_score(region: TextRegion) -> float:
    text = (region.text or "").strip()
    if not text:
        return 0.0
    letters = sum(ch.isalnum() for ch in text)
    punct = sum(ch in "!?~.…" for ch in text)
    area = max(1, (region.bbox[2] - region.bbox[0]) * (region.bbox[3] - region.bbox[1]))
    density = letters / max(len(text), 1)
    return region.confidence * 0.6 + density * 0.3 + min(area / 20000.0, 0.2) - punct * 0.02
