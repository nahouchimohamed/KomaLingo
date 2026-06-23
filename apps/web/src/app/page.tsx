"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { UploadPanel, UploadOptions } from "@/components/UploadPanel";
import { AppNav } from "@/components/AppNav";
import { JobProgress } from "@/components/JobProgress";
import { ChapterStatus, createChapter, getChapter } from "@/lib/api";

export default function HomePage() {
  const [busy, setBusy] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<ChapterStatus | null>(null);

  useEffect(() => {
    try {
      const last = window.localStorage.getItem("komalingo.last_job");
      if (last && !jobId) setJobId(last);
    } catch {
      // ignore
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    let timer: number | undefined;

    async function poll() {
      try {
        const status = await getChapter(jobId!);
        if (!cancelled) setJob(status);
        if (status.status === "completed" || status.status === "failed" || status.status === "cancelled") {
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
      form.append("target_lang", options.targetLang);
      form.append("processing_mode", options.processingMode);
      form.append("translate_provider", options.translateProvider);
      form.append("font_name", options.fontName);
      form.append("glossary", options.glossary);
      form.append("skip_sfx", options.skipSfx ? "true" : "false");
      if (options.translateApiKey) {
        form.append("translate_api_key", options.translateApiKey);
      }
      for (const file of options.files) {
        form.append("files", file);
      }
      const created = await createChapter(form);
      setJobId(created.job_id);
      setJob(null);
      try {
        window.localStorage.setItem("komalingo.last_job", created.job_id);
      } catch {
        // ignore
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-5 pb-20 pt-10 sm:px-8">
      <AppNav />
      <header className="rise mb-10 max-w-2xl">
        <h1
          className="text-4xl font-extrabold leading-tight tracking-tight text-[var(--ink)] sm:text-5xl"
          style={{ fontFamily: "var(--font-display), sans-serif" }}
        >
          Translate a chapter the way you upload it.
        </h1>
        <p className="mt-4 max-w-xl text-base text-black/65">
          Full redraw, strip text, translate-only, OCR-only, or typeset from edited regions — pages unlock one-by-one.
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
            try {
              window.localStorage.removeItem("komalingo.last_job");
            } catch {
              // ignore
            }
          }}
        />
      ) : (
        <p className="text-sm text-black/55">Starting job…</p>
      )}
    </main>
  );
}
