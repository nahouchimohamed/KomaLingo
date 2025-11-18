# Pipeline overview

KomaLingo runs a modular page pipeline:

1. OCR (Paddle) with downscaled input
2. Bubble merge
3. Translate (Google free by default, optional Gemini)
4. Inpaint (OpenCV TELEA)
5. Typeset English back into bubbles

Free defaults need no keys. Gemini is optional for cleaner dialogue phrasing.

Pages unlock in the UI as soon as each one finishes — no need to wait for the ZIP.

Design inspiration: zyddnys/manga-image-translator (separate implementation).

## Timing tips

- Warm the worker once so JP/KR OCR packs are cached.
- Parallel Google translate helps pages with many bubbles.
- Tall manhwa pages are still processed as whole images.

## Empty results

If a page comes back unchanged, OCR likely found no text above the confidence floor.
Try a sharper scan or set source language explicitly to Japanese or Korean.
