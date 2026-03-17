from __future__ import annotations

import logging

from app.pipeline.types import TextRegion

logger = logging.getLogger(__name__)


class FailoverTranslateProvider:
    """Try primary provider, then fall back to secondary on hard failures."""

    def __init__(self, primary, secondary) -> None:
        self.primary = primary
        self.secondary = secondary

    def translate_regions(self, regions: list[TextRegion], target_lang: str = "en") -> list[TextRegion]:
        try:
            return self.primary.translate_regions(regions, target_lang=target_lang)
        except Exception:
            logger.exception("primary translator failed; trying failover")
            return self.secondary.translate_regions(regions, target_lang=target_lang)
