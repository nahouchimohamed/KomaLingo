"use client";

import { useCallback, useEffect, useState } from "react";

export type UploadOptions = {
  files: File[];
  title: string;
  sourceLang: string;
  translateProvider: string;
  translateApiKey: string;
};

type Props = {
  onSubmit: (options: UploadOptions) => Promise<void>;
  busy: boolean;
};

const KEY_STORAGE = "komalingo.gemini_key"; // browser-only
const PROVIDER_STORAGE = "komalingo.translate_provider"; // remember choice

export function UploadPanel({ onSubmit, busy }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [title, setTitle] = useState("");
  const [sourceLang, setSourceLang] = useState("auto");
  const [translateProvider, setTranslateProvider] = useState("google");
  const [translateApiKey, setTranslateApiKey] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const savedKey = window.localStorage.getItem(KEY_STORAGE);
      const savedProvider = window.localStorage.getItem(PROVIDER_STORAGE);
      if (savedKey) setTranslateApiKey(savedKey);
      if (savedProvider) setTranslateProvider(savedProvider);
    } catch {
      // ignore storage failures
    }
  }, []);

  const acceptFiles = useCallback((list: FileList | File[]) => {
    const next = Array.from(list).filter((f) => {
      const name = f.name.toLowerCase();
      return (
        name.endsWith(".zip") ||
        name.endsWith(".cbz") ||
        name.endsWith(".jpg") ||
        name.endsWith(".jpeg") ||
        name.endsWith(".png") ||
        name.endsWith(".webp")
      );
    });
    setFiles(next);
    setError(null);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!files.length) {
      setError("Drop a ZIP/CBZ chapter or page images first.");
      return;
    }
    if (translateProvider === "gemini" && !translateApiKey.trim()) {
      setError("Paste a Gemini API key, or switch back to the free translator.");
      return;
    }
    try {
      window.localStorage.setItem(KEY_STORAGE, translateApiKey.trim());
      window.localStorage.setItem(PROVIDER_STORAGE, translateProvider);
    } catch {
      // ignore
    }
    try {
      await onSubmit({
        files,
        title,
        sourceLang,
        translateProvider,
        translateApiKey: translateApiKey.trim(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rise space-y-5">
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
          ZIP / CBZ with numbered pages, or multiple JPG/PNG/WebP files — same convention scanlation sites use.
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
        {files.length > 0 && (
          <p className="mt-4 text-sm text-[var(--accent)]">
            {files.length} file{files.length > 1 ? "s" : ""} ready
            {files[0] ? ` · ${files[0].name}` : ""}
          </p>
        )}
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
            <option value="auto">Auto-detect (JP / KR)</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
          </select>
        </label>
      </div>

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
            disabled={translateProvider !== "gemini"} // hide unused key entry
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none ring-[var(--accent)] focus:ring-2 disabled:opacity-50"
          />
        </label>
      </div>

      {error && <p className="text-sm text-[var(--accent)]">{error}</p>}

      <button
        type="submit"
        disabled={busy}
        className="w-full rounded-xl bg-[var(--accent)] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-soft)] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {busy ? "Uploading chapter…" : "Translate to English"}
      </button>
    </form>
  );
}
