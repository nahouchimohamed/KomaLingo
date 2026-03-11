from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.pipeline.fonts import candidates_for
from app.pipeline.types import TextRegion

FONT_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "fonts" / "ComicNeue-Bold.ttf",
    Path(__file__).resolve().parents[2] / "fonts" / "NotoSans-Bold.ttf",
    Path(__file__).resolve().parents[2] / "fonts" / "NotoSans-Regular.ttf",
    Path("/app/fonts/NotoSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]


def _load_font(size: int, font_name: str | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in candidates_for(font_name) + FONT_CANDIDATES:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.replace("\n", " ").split()
    if not words:
        return [text]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _fit_font(text: str, box_w: int, box_h: int, draw: ImageDraw.ImageDraw, font_name: str | None = None) -> tuple[ImageFont.ImageFont, list[str], int]:
    # English is longer than JP/KR — start smaller and shrink aggressively.
    start = min(40, max(11, int(box_h * 0.4)))  # EN longer than JP/KR
    for size in range(start, 8, -1):
        font = _load_font(size, font_name=font_name)
        lines = _wrap_text(text, font, max(10, box_w - 10), draw)
        line_h = size + max(2, size // 6)
        total_h = line_h * len(lines)
        max_line_w = max((draw.textlength(line, font=font) for line in lines), default=0)
        if total_h <= box_h - 6 and max_line_w <= box_w - 6:
            return font, lines, line_h
    font = _load_font(9)
    lines = _wrap_text(text, font, max(10, box_w - 10), draw)
    return font, lines, 11


def render_translations(image_path: Path, regions: list[TextRegion], output_path: Path, font_name: str | None = None) -> Path:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    for region in regions:
        text = (region.translation or region.text or "").strip()
        if not text:
            continue
        x1, y1, x2, y2 = region.bbox
        # Slight inset so text sits inside the cleaned bubble
        pad = 4  # keep away from bubble edge
        x1, y1, x2, y2 = x1 + pad, y1 + pad, x2 - pad, y2 - pad
        box_w, box_h = max(12, x2 - x1), max(12, y2 - y1)
        font, lines, line_h = _fit_font(text, box_w, box_h, draw)
        total_h = line_h * len(lines)
        y = y1 + max(0, (box_h - total_h) // 2)  # vertical center
        for line in lines:
            line_w = draw.textlength(line, font=font)
            x = x1 + max(0, (box_w - line_w) // 2)
            # Thicker outline for busy artwork
            for ox, oy in (
                (-2, 0),
                (2, 0),
                (0, -2),
                (0, 2),
                (-1, -1),
                (1, 1),
                (-1, 1),
                (1, -1),
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
            ):
                draw.text((x + ox, y + oy), line, font=font, fill=(255, 255, 255))
            draw.text((x, y), line, font=font, fill=(20, 20, 20))
            y += line_h

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Keep JPEG-ish pages reasonably small
    suffix = output_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        image.save(output_path, quality=92, optimize=True)  # avoid huge outputs
    else:
        image.save(output_path)
    return output_path
