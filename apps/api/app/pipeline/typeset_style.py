from __future__ import annotations


def outline_width(font_size: int, style: str = "default") -> int:
    if style == "heavy":
        return max(3, font_size // 8)
    if style == "soft":
        return max(1, font_size // 16)
    return max(2, font_size // 12)
