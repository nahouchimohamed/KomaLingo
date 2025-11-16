"use client";

import { useEffect, useState } from "react";
import { UploadPanel, UploadOptions } from "@/components/UploadPanel";
import { JobProgress } from "@/components/JobProgress";
import { ChapterStatus, createChapter, getChapter } from "@/lib/api";

export default function HomePage() {
  const [busy, setBusy] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<ChapterStatus | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    let timer: number | undefined;

    async function poll() {
      try {
        const status = await getChapter(jobId!);
        if (!cancelled) setJob(status);
        if (status.status === "completed" || status.status === "failed") {
          return;
        }
      } catch {
        // keep polling through transient network blips
      }
      if (!cancelled) {
        timer = window.setTimeout(poll, 1200);
      }
    }

    poll();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId]);

  async function handleUpload(options: UploadOptions) {
    setBusy(true);
    try {
      const form = new FormData();
      form.append("title", options.title || "Untitled Chapter");
      form.append("source_lang", options.sourceLang);
      form.append("target_lang", "en");
      form.append("translate_provider", options.translateProvider);
      if (options.translateApiKey) {
        form.append("translate_api_key", options.translateApiKey);
      }
      for (const file of options.files) {
        form.append("files", file);
      }
      const created = await createChapter(form);
      setJobId(created.job_id);
      setJob(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-5 pb-20 pt-10 sm:px-8">
      <header className="rise mb-10 max-w-2xl">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.22em] text-[var(--accent)]">KomaLingo</p>
        <h1
          className="text-4xl font-extrabold leading-tight tracking-tight text-[var(--ink)] sm:text-5xl"
          style={{ fontFamily: "var(--font-display), sans-serif" }}
        >
          Translate a chapter the way you upload it.
        </h1>
        <p className="mt-4 max-w-xl text-base text-black/65">
          Drop a ZIP/CBZ of Japanese or Korean pages. Pages unlock one-by-one — free by default, optional Gemini key for
          better dialogue.
        </p>
      </header>

      {!jobId ? (
        <UploadPanel onSubmit={handleUpload} busy={busy} />
      ) : job ? (
        <JobProgress
          job={job}
          onReset={() => {
            setJobId(null);
            setJob(null);
          }}
        />
      ) : (
        <p className="text-sm text-black/55">Starting job…</p>
      )}
    </main>
  );
}
