from __future__ import annotations

import json
import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

from app.pipeline.detect import detect_text_regions
from app.pipeline.inpaint import get_inpaint_provider
from app.pipeline.translate import get_translate_provider
from app.pipeline.types import PageResult, TextRegion
from app.pipeline.typeset import render_translations

logger = logging.getLogger(__name__)

StageCallback = Callable[[str], None]

VALID_MODES = frozenset({"full", "strip", "translate_only"})


def _regions_payload(regions: list[TextRegion]) -> list[dict]:
    return [
        {
            "text": region.text,
            "translation": region.translation,
            "bbox": list(region.bbox),
            "confidence": region.confidence,
            "language": region.language,
        }
        for region in regions
    ]


def _write_regions_sidecar(output_path: Path, regions: list[TextRegion], mode: str) -> None:
    sidecar = output_path.with_suffix(output_path.suffix + ".regions.json")
    sidecar.write_text(
        json.dumps({"mode": mode, "regions": _regions_payload(regions)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def process_page(
    image_path: Path,
    output_path: Path,
    source_lang: str = "auto",
    target_lang: str = "en",
    on_stage: StageCallback | None = None,
    translate_provider: str | None = None,
    translate_api_key: str | None = None,
    processing_mode: str = "full",
) -> PageResult:
    """Run the selected pipeline mode for one page.

    Modes:
      full            — OCR → translate → inpaint → typeset (default)
      strip           — OCR → inpaint only (text removed, no translation)
      translate_only  — OCR → translate, keep original art, write regions JSON
    """

    def stage(name: str) -> None:
        if on_stage:
            on_stage(name)

    mode = (processing_mode or "full").strip().lower()
    if mode not in VALID_MODES:
        mode = "full"

    stage("ocr")
    regions = detect_text_regions(image_path, source_lang=source_lang)
    logger.info("Detected %d regions in %s (mode=%s)", len(regions), image_path.name, mode)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not regions:
        output_path.write_bytes(image_path.read_bytes())
        if mode == "translate_only":
            _write_regions_sidecar(output_path, [], mode)
        stage("done")
        return PageResult(regions=[], output_path=str(output_path))

    if mode == "strip":
        with tempfile.TemporaryDirectory(prefix="komalingo_") as tmp:
            cleaned = Path(tmp) / f"clean{image_path.suffix or '.png'}"
            stage("inpaint")
            get_inpaint_provider().erase(image_path, regions, cleaned)
            output_path.write_bytes(cleaned.read_bytes())
        stage("done")
        return PageResult(regions=regions, output_path=str(output_path))

    stage("translate")
    translator = get_translate_provider(override=translate_provider, api_key=translate_api_key)
    regions = translator.translate_regions(regions, target_lang=target_lang)

    if mode == "translate_only":
        output_path.write_bytes(image_path.read_bytes())
        _write_regions_sidecar(output_path, regions, mode)
        stage("done")
        return PageResult(regions=regions, output_path=str(output_path))

    with tempfile.TemporaryDirectory(prefix="komalingo_") as tmp:
        cleaned = Path(tmp) / f"clean{image_path.suffix or '.png'}"
        stage("inpaint")
        get_inpaint_provider().erase(image_path, regions, cleaned)
        stage("typeset")
        render_translations(cleaned, regions, output_path)

    stage("done")
    return PageResult(regions=regions, output_path=str(output_path))
