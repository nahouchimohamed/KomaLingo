from __future__ import annotations

from app.pipeline.types import TextRegion


def sort_regions(regions: list[TextRegion], source_lang: str = "auto") -> list[TextRegion]:
    """Japanese pages often read right-to-left across panels; Korean/Ltr stay left-to-right."""
    rtl = source_lang == "ja"

    def key(r: TextRegion):
        x1, y1, x2, y2 = r.bbox
        # row by top, then x depending on direction
        return (y1 // max(1, (y2 - y1)), -x1 if rtl else x1)

    return sorted(regions, key=key)
