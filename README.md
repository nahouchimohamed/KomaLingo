# KomaLingo

Personal manga / manhwa chapter translator. Upload a ZIP/CBZ (or page images), run OCR → JP/KR→EN translation → text cleanup → typesetting, then download a translated ZIP.

Pipeline design is inspired by [zyddnys/manga-image-translator](https://github.com/zyddnys/manga-image-translator). KomaLingo is a separate web app with its own modular providers.

**Author:** nahouchimohamed

## Stack

- **Frontend:** Next.js 15 + TypeScript + Tailwind (`apps/web`)
- **Backend:** FastAPI + SQLAlchemy + Redis/RQ (`apps/api`)
- **OCR:** PaddleOCR (local, downscaled pages, merged bubbles)
- **Translate (free default):** Google Translate endpoint (no key)
- **Translate (optional):** Gemini API key, MyMemory, LibreTranslate
- **Inpaint (default):** OpenCV TELEA (local, free)

## Quick start

```bash
cp .env.example .env
docker compose up --build
cd apps/web && npm install && npm run dev
```

- App: http://localhost:3000
- API health: http://localhost:8000/api/health

## Processing modes

| Mode | What it does |
|------|----------------|
| `full` | OCR → translate → inpaint → typeset English onto the page (default) |
| `strip` | OCR → inpaint only — erase dialogue without translating |
| `translate_only` | OCR → translate — keep original art and write a `.regions.json` sidecar per page |

Choose the mode in the upload UI (`processing_mode` form field). Strip mode skips the translator. Translate-only keeps the artwork untouched and shows English lines in the page viewer.

## Upload format

Same convention scanlation sites use:

- Numbered page images (`001.jpg`, `002.jpg`, …) inside a **ZIP/CBZ**, or
- Multiple image files dropped together

Source: Auto / Japanese / Korean → English.

## Providers

```env
TRANSLATE_PROVIDER=google   # google | mymemory | gemini | libre
INPAINT_PROVIDER=cv2        # cv2 | fill | lama
OCR_PROVIDER=paddle
GEMINI_API_KEY=             # optional; also pasteable in the upload UI
```

Free path needs no keys. For cleaner comic dialogue, choose Gemini in the UI and paste a free [Google AI Studio](https://aistudio.google.com) key.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chapters` | Upload chapter (`files`, `processing_mode`, optional translator fields) |
| GET | `/api/chapters/{id}` | Job status + per-page progress |
| GET | `/api/chapters/{id}/pages/{n}` | Result preview (falls back to original) |
| GET | `/api/chapters/{id}/pages/{n}/original` | Original page |
| GET | `/api/chapters/{id}/pages/{n}/regions` | OCR/translation sidecar (translate-only) |
| GET | `/api/chapters/{id}/download` | Result ZIP |

## Notes

- First worker boot may download OCR models into the `paddle_models` volume; later runs reuse them.
- Pages appear one-by-one as they finish — you do not need to wait for the full chapter.
- Stylized SFX are best-effort; dialogue bubbles are the main target.
- Tall manhwa strips are processed as single images in the MVP.

## License

All rights reserved unless otherwise noted.
