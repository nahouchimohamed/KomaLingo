from __future__ import annotations

from pathlib import Path


def hint_from_path(path: Path) -> str | None:
    name = path.name.lower()
    if any(k in name for k in ("manhwa", "webtoon", "kr", "ko")):
        return "ko"
    if any(k in name for k in ("manhua", "zh", "cn", "chinese")):
        return "zh"
    if any(k in name for k in ("manga", "jp", "ja")):
        return "ja"
    return None
