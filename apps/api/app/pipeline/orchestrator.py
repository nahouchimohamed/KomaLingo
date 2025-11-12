from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

from app.pipeline.detect import detect_text_regions
from app.pipeline.inpaint import get_inpaint_provider
from app.pipeline.translate import get_translate_provider
from app.pipeline.types import PageResult
from app.pipeline.typeset import render_translations

logger = logging.getLogger(__name__)

StageCallback = Callable[[str], None]


def process_page(
    image_path: Path,
    output_path: Path,
    source_lang: str = "auto",
    target_lang: str = "en",
    on_stage: StageCallback | None = None,
    translate_provider: str | None = None,  # job-level
    translate_api_key: str | None = None,
) -> PageResult:
    """Run detect → OCR → translate → inpaint → typeset for one page."""

    def stage(name: str) -> None:
        if on_stage:
            on_stage(name)

    stage("ocr")
    regions = detect_text_regions(image_path, source_lang=source_lang)
    logger.info("Detected %d regions in %s", len(regions), image_path.name)

    if not regions:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_path.read_bytes())
        stage("done")
        return PageResult(regions=[], output_path=str(output_path))

    stage("translate")
    translator = get_translate_provider(override=translate_provider, api_key=translate_api_key)
    regions = translator.translate_regions(regions, target_lang=target_lang)

    with tempfile.TemporaryDirectory(prefix="komalingo_") as tmp:
        cleaned = Path(tmp) / f"clean{image_path.suffix or '.png'}"
        stage("inpaint")
        inpaint = get_inpaint_provider()
        inpaint.erase(image_path, regions, cleaned)
        stage("typeset")
        render_translations(cleaned, regions, output_path)

    stage("done")
    return PageResult(regions=regions, output_path=str(output_path))
