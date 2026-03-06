from __future__ import annotations

import json
import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

from app.pipeline.detect import detect_text_regions
from app.pipeline.glossary import apply_glossary, parse_glossary
from app.pipeline.inpaint import get_inpaint_provider
from app.pipeline.sfx import filter_sfx
from app.pipeline.translate import get_translate_provider
from app.pipeline.types import PageResult, TextRegion
from app.pipeline.typeset import render_translations

logger = logging.getLogger(__name__)

StageCallback = Callable[[str], None]

VALID_MODES = frozenset({"full", "strip", "translate_only", "ocr_only", "typeset_from_json"})


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


def _load_regions_sidecar(image_path: Path, output_path: Path) -> list[TextRegion]:
    for candidate in (
        output_path.with_suffix(output_path.suffix + ".regions.json"),
        image_path.with_suffix(image_path.suffix + ".regions.json"),
    ):
        if candidate.exists():
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            regions: list[TextRegion] = []
            for item in payload.get("regions", []):
                regions.append(
                    TextRegion(
                        text=item.get("text", ""),
                        bbox=tuple(item.get("bbox", [0, 0, 0, 0])),
                        confidence=float(item.get("confidence", 1.0)),
                        translation=item.get("translation", ""),
                        language=item.get("language", "unknown"),
                    )
                )
            return regions
    return []


def process_page(
    image_path: Path,
    output_path: Path,
    source_lang: str = "auto",
    target_lang: str = "en",
    on_stage: StageCallback | None = None,
    translate_provider: str | None = None,
    translate_api_key: str | None = None,
    processing_mode: str = "full",
    font_name: str | None = None,
    glossary_json: str | None = None,
    skip_sfx: bool = False,
) -> PageResult:
    """Run the selected pipeline mode for one page."""

    def stage(name: str) -> None:
        if on_stage:
            on_stage(name)

    mode = (processing_mode or "full").strip().lower()
    if mode not in VALID_MODES:
        mode = "full"
    glossary = parse_glossary(glossary_json)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if mode == "typeset_from_json":
        stage("typeset")
        regions = _load_regions_sidecar(image_path, output_path)
        if not regions:
            output_path.write_bytes(image_path.read_bytes())
            stage("done")
            return PageResult(regions=[], output_path=str(output_path))
        for region in regions:
            region.translation = apply_glossary(region.translation or region.text, glossary)
        with tempfile.TemporaryDirectory(prefix="komalingo_") as tmp:
            cleaned = Path(tmp) / f"clean{image_path.suffix or '.png'}"
            stage("inpaint")
            get_inpaint_provider().erase(image_path, regions, cleaned)
            render_translations(cleaned, regions, output_path, font_name=font_name)
        _write_regions_sidecar(output_path, regions, mode)
        stage("done")
        return PageResult(regions=regions, output_path=str(output_path))

    stage("ocr")
    regions = detect_text_regions(image_path, source_lang=source_lang)
    regions = filter_sfx(regions, skip_sfx)
    logger.info("Detected %d regions in %s (mode=%s)", len(regions), image_path.name, mode)

    if not regions:
        output_path.write_bytes(image_path.read_bytes())
        _write_regions_sidecar(output_path, [], mode)
        stage("done")
        return PageResult(regions=[], output_path=str(output_path))

    if mode == "ocr_only":
        output_path.write_bytes(image_path.read_bytes())
        _write_regions_sidecar(output_path, regions, mode)
        stage("done")
        return PageResult(regions=regions, output_path=str(output_path))

    if mode == "strip":
        with tempfile.TemporaryDirectory(prefix="komalingo_") as tmp:
            cleaned = Path(tmp) / f"clean{image_path.suffix or '.png'}"
            stage("inpaint")
            get_inpaint_provider().erase(image_path, regions, cleaned)
            output_path.write_bytes(cleaned.read_bytes())
        _write_regions_sidecar(output_path, regions, mode)
        stage("done")
        return PageResult(regions=regions, output_path=str(output_path))

    stage("translate")
    translator = get_translate_provider(override=translate_provider, api_key=translate_api_key)
    regions = translator.translate_regions(regions, target_lang=target_lang)
    for region in regions:
        region.translation = apply_glossary(region.translation or region.text, glossary)

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
        render_translations(cleaned, regions, output_path, font_name=font_name)

    _write_regions_sidecar(output_path, regions, mode)
    stage("done")
    return PageResult(regions=regions, output_path=str(output_path))
