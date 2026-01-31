from __future__ import annotations

import re

from app.pipeline.types import TextRegion

_SFX_RE = re.compile(
    r"^(?:[A-Z]{1,6}|[ぁ-んァ-ンー]{1,4}|[ㄱ-ㅎㅏ-ㅣ가-힣]{1,3}|[!?~.…]{1,6})$"
)


def looks_like_sfx(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    if len(cleaned) <= 2 and not any(ch.isalnum() for ch in cleaned):
        return True
    return bool(_SFX_RE.match(cleaned))


def filter_sfx(regions: list[TextRegion], enabled: bool) -> list[TextRegion]:
    if not enabled:
        return regions
    return [r for r in regions if not looks_like_sfx(r.text)]
