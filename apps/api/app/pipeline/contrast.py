from __future__ import annotations

import cv2
import numpy as np


def boost_local_contrast(image: np.ndarray) -> np.ndarray:
    """CLAHE on L channel keeps bubble ink readable on gray fills."""
    if len(image.shape) != 3:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l2, a, b)), cv2.COLOR_LAB2BGR)
