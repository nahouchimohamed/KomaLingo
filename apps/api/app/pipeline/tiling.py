from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def should_tile(image: np.ndarray, *, min_aspect: float = 2.4) -> bool:
    h, w = image.shape[:2]
    return h > 0 and (h / max(w, 1)) >= min_aspect


def split_tall_image(image_path: Path, out_dir: Path, *, tile_height: int = 2400, overlap: int = 80) -> list[Path]:
    """Slice tall manhwa strips into overlapping tiles for more stable OCR."""
    image = cv2.imread(str(image_path))
    if image is None:
        return [image_path]
    if not should_tile(image):
        return [image_path]
    out_dir.mkdir(parents=True, exist_ok=True)
    h, _w = image.shape[:2]
    paths: list[Path] = []
    y = 0
    index = 0
    while y < h:
        y2 = min(h, y + tile_height)
        tile = image[y:y2]
        path = out_dir / f"{image_path.stem}_tile{index:02d}{image_path.suffix or '.png'}"
        cv2.imwrite(str(path), tile)
        paths.append(path)
        if y2 >= h:
            break
        y = max(y + tile_height - overlap, y + 1)
        index += 1
    return paths or [image_path]
