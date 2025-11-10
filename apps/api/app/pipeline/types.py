from dataclasses import dataclass, field


@dataclass
class TextRegion:
    text: str
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float = 1.0
    translation: str = ""
    language: str = "unknown"


@dataclass
class PageResult:
    regions: list[TextRegion] = field(default_factory=list)
    output_path: str = ""
