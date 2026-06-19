from __future__ import annotations
import cv2
import numpy as np

def estimate_panel_gutters(image: np.ndarray) -> list[int]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    row_mean = gray.mean(axis=1)
    threshold = float(np.percentile(row_mean, 85))
    gutters = [int(i) for i, v in enumerate(row_mean) if v >= threshold]
    kept: list[int] = []
    last = -50
    for y in gutters:
        if y - last >= 40:
            kept.append(y)
            last = y
    return kept
