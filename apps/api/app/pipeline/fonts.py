from __future__ import annotations

from pathlib import Path

FONT_DIR = Path(__file__).resolve().parents[2] / "fonts"

FONT_PRESETS: dict[str, list[Path]] = {
    "default": [
        FONT_DIR / "ComicNeue-Bold.ttf",
        FONT_DIR / "NotoSans-Bold.ttf",
        FONT_DIR / "NotoSans-Regular.ttf",
        Path("/app/fonts/NotoSans-Regular.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ],
    "comic": [
        FONT_DIR / "ComicNeue-Bold.ttf",
        Path("C:/Windows/Fonts/comic.ttf"),
        Path("C:/Windows/Fonts/comicbd.ttf"),
    ],
    "sans": [
        FONT_DIR / "NotoSans-Bold.ttf",
        FONT_DIR / "NotoSans-Regular.ttf",
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ],
    "heavy": [
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/impact.ttf"),
        FONT_DIR / "ComicNeue-Bold.ttf",
    ],
}


def candidates_for(font_name: str | None) -> list[Path]:
    key = (font_name or "default").strip().lower() or "default"
    presets = list(FONT_PRESETS.get(key, FONT_PRESETS["default"]))
    # Always fall back through default chain
    for path in FONT_PRESETS["default"]:
        if path not in presets:
            presets.append(path)
    return presets
