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
| POST | `/api/chapters` | Upload chapter (`files`, optional `translate_provider`, `translate_api_key`) |
| GET | `/api/chapters/{id}` | Job status + per-page progress |
| GET | `/api/chapters/{id}/pages/{n}` | Translated preview (falls back to original) |
| GET | `/api/chapters/{id}/pages/{n}/original` | Original page |
| GET | `/api/chapters/{id}/download` | Translated ZIP |

## Notes

- First worker boot may download OCR models into the `paddle_models` volume; later runs reuse them.
- Pages appear one-by-one as they finish — you do not need to wait for the full chapter.
- Stylized SFX are best-effort; dialogue bubbles are the main target.
- Tall manhwa strips are processed as single images in the MVP.

## License

All rights reserved unless otherwise noted.

Aim for readable dialogue first; perfect SFX recreation is out of scope for the free path.

Default path stays free; paid/cloud keys remain optional.

Finished pages can be opened before the ZIP is ready.

Gemini keys can be created in Google AI Studio for optional higher-quality phrasing.

OpenCV inpaint replaces hard white rectangle fills on the free path.

Expect imperfect SFX; prioritize readable dialogue first.

Worker warm-up loads JP/KR OCR packs once per container start.

Maintained solely by nahouchimohamed.

OCR weights persist in the `paddle_models` Docker volume across restarts.

Source language Auto picks JP/KR from OCR script hints.
