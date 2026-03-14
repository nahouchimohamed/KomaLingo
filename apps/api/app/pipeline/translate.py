from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx

from app.config import get_settings
from app.pipeline.retry import with_retries
from app.pipeline.types import TextRegion
from app.services.translation_cache import get_cached_translation, set_cached_translation

logger = logging.getLogger(__name__)


class TranslateProvider(ABC):
    @abstractmethod
    def translate_regions(self, regions: list[TextRegion], target_lang: str = "en") -> list[TextRegion]:
        raise NotImplementedError


def _detect_source(text: str, language: str = "unknown") -> str:
    if language in ("ja", "ko"):
        return language
    from app.pipeline.ocr import guess_script

    script = guess_script(text)
    if script in ("ja", "ko"):
        return script
    return "ja"


class GoogleFreeTranslateProvider(TranslateProvider):  # no API key
    """Unofficial Google Translate endpoint — free, no API key, decent for comics testing."""

    ENDPOINT = "https://translate.googleapis.com/translate_a/single"

    def _translate_one(self, client: httpx.Client, text: str, source: str, target: str) -> str:
        resp = client.get(
            self.ENDPOINT,
            params={
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        # Response shape: [[[translated, original, ...], ...], ...]
        parts = []
        for chunk in data[0] or []:
            if chunk and chunk[0]:
                parts.append(chunk[0])
        return "".join(parts).strip() or text  # never blank out a bubble

    def translate_regions(self, regions: list[TextRegion], target_lang: str = "en") -> list[TextRegion]:
        if not regions:
            return regions

        # Parallelize bubble translations — biggest free-path speed win vs serial MyMemory.
        max_workers = min(8, max(1, len(regions)))  # concurrent HTTP
        results: dict[int, str] = {}

        with httpx.Client(timeout=30.0) as client:
            def work(idx: int, region: TextRegion) -> tuple[int, str]:
                source = _detect_source(region.text, region.language)
                if source == "auto":
                    source = "ja"
                cached = get_cached_translation(region.text, target_lang, "google")
                if cached:
                    return idx, cached
                try:
                    translated = with_retries(
                        lambda: self._translate_one(client, region.text[:4500], source, target_lang)
                    )
                    set_cached_translation(region.text, target_lang, "google", translated)
                    return idx, translated
                except Exception:
                    logger.exception("Google translate failed for %r", region.text[:40])
                    return idx, region.text

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(work, i, r) for i, r in enumerate(regions)]
                for fut in as_completed(futures):
                    idx, text = fut.result()
                    results[idx] = text

        for i, region in enumerate(regions):
            region.translation = results.get(i, region.text)
        return regions


class GeminiTranslateProvider(TranslateProvider):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def translate_regions(self, regions: list[TextRegion], target_lang: str = "en") -> list[TextRegion]:
        if not regions:
            return regions
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        payload = [{"i": i, "t": r.text} for i, r in enumerate(regions)]
        prompt = (
            "You translate manga/manhwa dialogue from Japanese or Korean to English.\n"
            "Return ONLY a JSON array like [{\"i\":0,\"t\":\"English text\"}, ...] "
            "with the same indices. Keep tone natural for comics. No explanations.\n\n"
            f"Target language: {target_lang}\n"
            f"Items: {json.dumps(payload, ensure_ascii=False)}"
        )
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        by_index = {int(item["i"]): str(item["t"]) for item in data}
        for i, region in enumerate(regions):
            region.translation = by_index.get(i, region.text)
        return regions


class MyMemoryTranslateProvider(TranslateProvider):
    BASE_URL = "https://api.mymemory.translated.net/get"

    def translate_regions(self, regions: list[TextRegion], target_lang: str = "en") -> list[TextRegion]:
        if not regions:
            return regions

        with httpx.Client(timeout=60.0) as client:
            for region in regions:
                source = _detect_source(region.text, region.language)
                try:
                    text = region.text[:450]
                    resp = client.get(
                        self.BASE_URL,
                        params={"q": text, "langpair": f"{source}|{target_lang}"},
                    )
                    if resp.status_code >= 400:
                        region.translation = region.text
                        continue
                    data = resp.json()
                    translated = (data.get("responseData") or {}).get("translatedText")
                    if not translated or translated.upper().startswith("INVALID"):
                        region.translation = region.text
                    else:
                        region.translation = translated
                except Exception:
                    logger.exception("MyMemory failed for text=%r", region.text[:40])
                    region.translation = region.text
        return regions


class LibreTranslateProvider(TranslateProvider):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def translate_regions(self, regions: list[TextRegion], target_lang: str = "en") -> list[TextRegion]:
        if not regions:
            return regions

        with httpx.Client(timeout=60.0) as client:
            for region in regions:
                source = _detect_source(region.text, region.language)
                try:
                    resp = client.post(
                        f"{self.base_url}/translate",
                        json={
                            "q": region.text,
                            "source": source,
                            "target": target_lang,
                            "format": "text",
                        },
                    )
                    if resp.status_code >= 400:
                        logger.warning("LibreTranslate error %s: %s", resp.status_code, resp.text[:200])
                        region.translation = region.text
                        continue
                    data = resp.json()
                    region.translation = data.get("translatedText") or region.text
                except Exception:
                    logger.exception("LibreTranslate failed for text=%r", region.text[:40])
                    region.translation = region.text
        return regions


class PassthroughTranslateProvider(TranslateProvider):
    def translate_regions(self, regions: list[TextRegion], target_lang: str = "en") -> list[TextRegion]:
        for region in regions:
            region.translation = f"[EN] {region.text}"
        return regions


def get_translate_provider(override: str | None = None, api_key: str | None = None) -> TranslateProvider:
    settings = get_settings()
    provider = (override or settings.translate_provider).lower()
    key = api_key if api_key is not None else settings.gemini_api_key

    if provider == "gemini":
        if key:
            return GeminiTranslateProvider(key)
        logger.warning("GEMINI_API_KEY missing; falling back to Google free translate")
        return GoogleFreeTranslateProvider()
    if provider == "google":
        return GoogleFreeTranslateProvider()
    if provider == "libre":
        return LibreTranslateProvider(settings.libretranslate_url)
    if provider == "mymemory":
        return MyMemoryTranslateProvider()
    return GoogleFreeTranslateProvider()
