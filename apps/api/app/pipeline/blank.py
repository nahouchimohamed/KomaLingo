from __future__ import annotations
from pathlib import Path
import cv2

def is_mostly_blank(image_path: Path, *, std_threshold: float = 8.0) -> bool:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return False
    return float(image.std()) < std_threshold
