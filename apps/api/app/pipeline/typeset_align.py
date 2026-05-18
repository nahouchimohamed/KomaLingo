from __future__ import annotations


def line_x(align: str, x1: int, box_w: int, line_w: float) -> int:
    if align == "left":
        return x1
    if align == "right":
        return int(x1 + max(0, box_w - line_w))
    return int(x1 + max(0, (box_w - line_w) / 2))
