from __future__ import annotations

from app.config import get_settings


def mask_pad() -> int:
    return max(0, int(get_settings().inpaint_mask_pad))


def telea_radius() -> int:
    return max(1, int(get_settings().inpaint_radius))
