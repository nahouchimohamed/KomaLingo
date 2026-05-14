from __future__ import annotations

import cv2
import numpy as np


def sharpen_for_ocr(image: np.ndarray, amount: float = 0.35) -> np.ndarray:
    if amount <= 0:
        return image
    blur = cv2.GaussianBlur(image, (0, 0), 1.2)
    return cv2.addWeighted(image, 1 + amount, blur, -amount, 0)


def to_ocr_gray(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
