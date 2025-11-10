"""Merge nearby OCR line boxes into bubble-like groups for cleaner translation."""

from __future__ import annotations

from app.pipeline.types import TextRegion


def _overlap_or_near(a: TextRegion, b: TextRegion, gap: float) -> bool:
    ax1, ay1, ax2, ay2 = a.bbox
    bx1, by1, bx2, by2 = b.bbox
    # Expand slightly then test intersection
    ax1 -= gap
    ay1 -= gap
    ax2 += gap
    ay2 += gap
    return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)


def merge_text_regions(regions: list[TextRegion], gap_ratio: float = 0.5) -> list[TextRegion]:  # tighter bubble groups
    """Cluster spatially close OCR hits so one bubble becomes one translation unit."""
    if len(regions) <= 1:
        return regions

    heights = [max(1, r.bbox[3] - r.bbox[1]) for r in regions]
    median_h = sorted(heights)[len(heights) // 2]
    gap = max(8.0, median_h * gap_ratio)

    # Reading order helps stable merges
    ordered = sorted(regions, key=lambda r: (r.bbox[1], r.bbox[0]))  # reading order
    clusters: list[list[TextRegion]] = []

    for region in ordered:
        placed = False
        for cluster in clusters:
            if any(_overlap_or_near(region, other, gap) for other in cluster):
                cluster.append(region)
                placed = True
                break
        if not placed:
            clusters.append([region])

    merged: list[TextRegion] = []
    for cluster in clusters:
        cluster = sorted(cluster, key=lambda r: (r.bbox[1], r.bbox[0]))
        xs1 = [r.bbox[0] for r in cluster]
        ys1 = [r.bbox[1] for r in cluster]
        xs2 = [r.bbox[2] for r in cluster]
        ys2 = [r.bbox[3] for r in cluster]
        text = " ".join(r.text.strip() for r in cluster if r.text.strip())  # one bubble string
        if not text:
            continue
        conf = sum(r.confidence for r in cluster) / len(cluster)
        lang = cluster[0].language
        # Prefer majority script guess
        langs = [r.language for r in cluster if r.language in ("ja", "ko")]
        if langs:
            lang = max(set(langs), key=langs.count)  # ja/ko vote
        merged.append(
            TextRegion(
                text=text,
                bbox=(min(xs1), min(ys1), max(xs2), max(ys2)),
                confidence=conf,
                language=lang,
            )
        )
    return merged
