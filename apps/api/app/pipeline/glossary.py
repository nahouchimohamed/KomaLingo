from __future__ import annotations

import json
import re


def parse_glossary(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    raw = raw.strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        data = json.loads(raw)
        return {str(k): str(v) for k, v in data.items()}
    mapping: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        src, dst = line.split("=", 1)
        mapping[src.strip()] = dst.strip()
    return mapping


def apply_glossary(text: str, glossary: dict[str, str]) -> str:
    if not text or not glossary:
        return text
    # Longer keys first so multi-word names win
    for src in sorted(glossary.keys(), key=len, reverse=True):
        dst = glossary[src]
        if not src:
            continue
        text = re.sub(re.escape(src), dst, text, flags=re.IGNORECASE)
    return text
