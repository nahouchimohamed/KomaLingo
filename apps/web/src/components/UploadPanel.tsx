"use client";

import { useCallback, useEffect, useState } from "react";
import { MODE_COPY, ProcessingMode, UploadOptions } from "@/lib/uploadOptions";
import { FileList } from "@/components/FileList";

export type { UploadOptions, ProcessingMode };

type Props = {
  onSubmit: (options: UploadOptions) => Promise<void>;
  busy: boolean;
};

const KEY_STORAGE = "komalingo.gemini_key";
const PROVIDER_STORAGE = "komalingo.translate_provider";
const MODE_STORAGE = "komalingo.processing_mode";
const FONT_STORAGE = "komalingo.font_name";
const TARGET_STORAGE = "komalingo.target_lang";
const GLOSSARY_STORAGE = "komalingo.glossary";
const SFX_STORAGE = "komalingo.skip_sfx";

export function UploadPanel({ onSubmit, busy }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [title, setTitle] = useState("");
  const [sourceLang, setSourceLang] = useState("auto");
  const [targetLang, setTargetLang] = useState("en");
  const [processingMode, setProcessingMode] = useState<ProcessingMode>("full");
  const [translateProvider, setTranslateProvider] = useState("google");
  const [translateApiKey, setTranslateApiKey] = useState("");
  const [fontName, setFontName] = useState("default");
  const [glossary, setGlossary] = useState("");
  const [skipSfx, setSkipSfx] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadPct, setUploadPct] = useState<number | null>(null);

  useEffect(() => {
    try {
      const savedKey = window.localStorage.getItem(KEY_STORAGE);
      const savedProvider = window.localStorage.getItem(PROVIDER_STORAGE);
      const savedMode = window.localStorage.getItem(MODE_STORAGE);
      const savedFont = window.localStorage.getItem(FONT_STORAGE);
      const savedTarget = window.localStorage.getItem(TARGET_STORAGE);
      const savedGlossary = window.localStorage.getItem(GLOSSARY_STORAGE);
      const savedSfx = window.localStorage.getItem(SFX_STORAGE);
      if (savedKey) setTranslateApiKey(savedKey);
      if (savedProvider) setTranslateProvider(savedProvider);
      if (savedMode && savedMode in MODE_COPY) setProcessingMode(savedMode as ProcessingMode);
      if (savedFont) setFontName(savedFont);
      if (savedTarget) setTargetLang(savedTarget);
      if (savedGlossary) setGlossary(savedGlossary);
      if (savedSfx) setSkipSfx(savedSfx === "1");
    } catch {
      // ignore
    }
  }, []);

  const acceptFiles = useCallback((list: FileList | File[]) => {
    const next = Array.from(list).filter((f) => {
      const name = f.name.toLowerCase();
      return [".zip", ".cbz", ".jpg", ".jpeg", ".png", ".webp"].some((ext) => name.endsWith(ext));
    });
    setFiles(next);
    setError(null);
  }, []);

  const needsTranslator = processingMode !== "strip" && processingMode !== "ocr_only";
  const modeMeta = MODE_COPY[processingMode];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!files.length) {
      setError("Drop a ZIP/CBZ chapter or page images first.");
      return;
    }
    if (needsTranslator && translateProvider === "gemini" && !translateApiKey.trim()) {
      setError("Paste a Gemini API key, or switch back to the free translator.");
      return;
    }
    try {
      window.localStorage.setItem(KEY_STORAGE, translateApiKey.trim());
      window.localStorage.setItem(PROVIDER_STORAGE, translateProvider);
      window.localStorage.setItem(MODE_STORAGE, processingMode);
      window.localStorage.setItem(FONT_STORAGE, fontName);
      window.localStorage.setItem(TARGET_STORAGE, targetLang);
      window.localStorage.setItem(GLOSSARY_STORAGE, glossary);
      window.localStorage.setItem(SFX_STORAGE, skipSfx ? "1" : "0");
    } catch {
      // ignore
    }
    try {
      setUploadPct(5);
      await onSubmit({
        files,
        title,
        sourceLang,
        targetLang,
        processingMode,
        translateProvider,
        translateApiKey: translateApiKey.trim(),
        fontName,
        glossary,
        skipSfx,
      });
      setUploadPct(100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploadPct(null);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rise soft-panel space-y-5 rounded-3xl p-5 sm:p-6">
      <div
        className={`dropzone rounded-2xl border-2 border-dashed border-[var(--line)] bg-white/50 px-6 py-12 text-center ${dragOver ? "active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files?.length) acceptFiles(e.dataTransfer.files);
        }}
      >
        <p className="text-lg font-semibold" style={{ fontFamily: "var(--font-display), sans-serif" }}>
          Drop a full chapter here
        </p>
        <p className="mt-2 text-sm text-black/60">
          ZIP / CBZ with numbered pages, or multiple JPG/PNG/WebP files.
        </p>
        <label className="mt-6 inline-flex cursor-pointer items-center gap-2 rounded-full bg-[var(--ink)] px-5 py-2.5 text-sm font-medium text-[var(--paper)]">
          Browse files
          <input
            type="file"
            className="hidden"
            multiple
            accept=".zip,.cbz,.jpg,.jpeg,.png,.webp"
            onChange={(e) => e.target.files && acceptFiles(e.target.files)}
          />
        </label>
        <FileList files={files} onChange={setFiles} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1.5 block font-medium text-black/70">Chapter title</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Optional"
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1.5 block font-medium text-black/70">Source language</span>
          <select
            value={sourceLang}
            onChange={(e) => setSourceLang(e.target.value)}
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2"
          >
            <option value="auto">Auto-detect (JP / KR / ZH)</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="zh">Chinese</option>
          </select>
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1.5 block font-medium text-black/70">Processing mode</span>
          <select
            value={processingMode}
            onChange={(e) => setProcessingMode(e.target.value as ProcessingMode)}
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2"
          >
            {Object.entries(MODE_COPY).map(([value, meta]) => (
              <option key={value} value={value}>
                {meta.label}
              </option>
            ))}
          </select>
          <p className="mt-1.5 text-xs text-black/50">{modeMeta.hint}</p>
        </label>
        <label className="block text-sm">
          <span className="mb-1.5 block font-medium text-black/70">Target language</span>
          <select
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
            disabled={!needsTranslator}
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2 disabled:opacity-50"
          >
            <option value="en">English</option>
            <option value="fr">French</option>
            <option value="es">Spanish</option>
            <option value="de">German</option>
            <option value="pt">Portuguese</option>
          </select>
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1.5 block font-medium text-black/70">Font</span>
          <select
            value={fontName}
            onChange={(e) => setFontName(e.target.value)}
            disabled={processingMode === "strip" || processingMode === "translate_only" || processingMode === "ocr_only"}
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2 disabled:opacity-50"
          >
            <option value="default">Default</option>
            <option value="comic">Comic</option>
            <option value="sans">Sans</option>
            <option value="heavy">Heavy</option>
          </select>
        </label>
        <label className="mt-6 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={skipSfx} onChange={(e) => setSkipSfx(e.target.checked)} />
          <span className="font-medium text-black/70">Skip likely SFX bubbles</span>
        </label>
      </div>

      {needsTranslator && (
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium text-black/70">Translator</span>
            <select
              value={translateProvider}
              onChange={(e) => setTranslateProvider(e.target.value)}
              className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2"
            >
              <option value="google">Free Google translate (default)</option>
              <option value="mymemory">Free MyMemory</option>
              <option value="gemini">Gemini (API key)</option>
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium text-black/70">Gemini API key (optional)</span>
            <input
              type="password"
              value={translateApiKey}
              onChange={(e) => setTranslateApiKey(e.target.value)}
              placeholder="Only needed for Gemini"
              disabled={translateProvider !== "gemini"}
              className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2 disabled:opacity-50"
            />
          </label>
        </div>
      )}

      <label className="block text-sm">
        <span className="mb-1.5 block font-medium text-black/70">Glossary (optional)</span>
        <textarea
          value={glossary}
          onChange={(e) => setGlossary(e.target.value)}
          rows={3}
          placeholder={"name=Name\nhonorific=san"}
          className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2"
        />
        <p className="mt-1 text-xs text-black/45">One `source=target` per line, or a JSON object.</p>
      </label>

      {uploadPct !== null && (
        <div className="overflow-hidden rounded-full bg-black/10">
          <div className="h-1.5 rounded-full bg-[var(--accent)] transition-[width]" style={{ width: `${uploadPct}%` }} />
        </div>
      )}

      {error && <p className="text-sm text-[var(--accent)]">{error}</p>}

      <button
        type="submit"
        disabled={busy}
        className="w-full rounded-xl bg-[var(--accent)] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-soft)] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {busy ? "Uploading chapter…" : modeMeta.submit}
      </button>
    </form>
  );
}
