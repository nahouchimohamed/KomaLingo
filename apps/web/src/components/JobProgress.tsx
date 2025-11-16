"use client";

import { useMemo, useState } from "react";
import type { ChapterStatus, PageStatus } from "@/lib/api";
import { downloadUrl } from "@/lib/api";

type Props = {
  job: ChapterStatus;
  onReset: () => void;
};

function stageLabel(page: PageStatus, job: ChapterStatus): string {
  if (page.status === "done") return "Translated — click to view";
  if (page.status === "failed") return page.error || "Failed";
  if (page.status === "processing") {
    const stage = page.stage || job.current_stage || "working";
    if (stage.startsWith("ocr")) return "Reading text (OCR)…";
    if (stage.startsWith("translate")) return "Translating…";
    if (stage.startsWith("inpaint")) return "Cleaning bubbles…";
    if (stage.startsWith("typeset")) return "Drawing English…";
    return stage;
  }
  return "Queued";
}

export function JobProgress({ job, onReset }: Props) {
  const pct = Math.round(job.progress * 100);
  const [viewer, setViewer] = useState<{ src: string; title: string } | null>(null);

  const hint = useMemo(() => {
    if (job.status === "completed") return "All pages ready.";
    if (job.completed_pages === 0 && job.status === "processing") {
      return "First page may take a bit while OCR models load. Later pages are faster — each finished page appears below.";
    }
    return "Pages unlock one-by-one as they finish. Click any completed page to zoom.";
  }, [job]);

  return (
    <section className="rise space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-black/45">Job</p>
          <h2 className="text-2xl font-bold" style={{ fontFamily: "var(--font-display), sans-serif" }}>
            {job.title}
          </h2>
          <p className="mt-1 text-sm text-black/55">
            {job.completed_pages}/{job.total_pages} pages · {job.current_stage}
          </p>
        </div>
        <div className="flex gap-2">
          {job.download_ready && (
            <a
              href={downloadUrl(job.job_id)}
              className="rounded-xl bg-[var(--ink)] px-4 py-2.5 text-sm font-semibold text-[var(--paper)]"
            >
              Download translated ZIP
            </a>
          )}
          <button
            type="button"
            onClick={onReset}
            className="rounded-xl border border-[var(--line)] bg-white/70 px-4 py-2.5 text-sm font-medium"
          >
            New chapter
          </button>
        </div>
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between text-xs text-black/50">
          <span>{pct}% complete</span>
          <span>
            {job.completed_pages} of {job.total_pages}
          </span>
        </div>
        <div className="overflow-hidden rounded-full bg-black/10">
          <div
            className={`h-2 rounded-full bg-[var(--accent)] transition-[width] duration-500 ${
              job.status === "processing" ? "progress-pulse" : ""
            }`}
            style={{ width: `${Math.max(pct, job.status === "pending" ? 3 : pct)}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-black/55">{hint}</p>
      </div>

      {job.error && (
        <div className="rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/10 px-4 py-3 text-sm text-[var(--accent)]">
          {job.error}
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {job.pages.map((page) => {
          const imageSrc = page.preview_url || page.original_url; // original while pending
          const canOpen = Boolean(imageSrc);
          return (
            <article
              key={page.index}
              className={`overflow-hidden rounded-2xl border bg-white/60 shadow-[0_10px_30px_rgba(18,16,14,0.06)] ${
                page.status === "done"
                  ? "border-[var(--ok)]/35"
                  : page.status === "processing"
                    ? "border-[var(--accent)]/40"
                    : "border-[var(--line)]"
              }`}
            >
              <button
                type="button"
                disabled={!canOpen}
                onClick={() =>
                  imageSrc &&
                  setViewer({
                    src: page.preview_url || page.original_url || imageSrc,
                    title: `${page.filename} · ${page.status}{page.status === "done" ? " ✓" : ""}`,
                  })
                }
                className="relative block aspect-[3/4] w-full bg-[var(--paper-deep)] text-left"
              >
                {imageSrc ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={imageSrc}
                    alt={page.filename}
                    className={`h-full w-full object-cover transition ${
                      page.status === "done" ? "" : "opacity-70"
                    }`}
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-xs uppercase tracking-wider text-black/35">
                    {page.status}
                  </div>
                )}
                <span
                  className={`absolute left-2 top-2 rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-white ${
                    page.status === "done"
                      ? "bg-[var(--ok)]"
                      : page.status === "processing"
                        ? "bg-[var(--accent)]"
                        : page.status === "failed"
                          ? "bg-[var(--accent)]"
                          : "bg-black/45"
                  }`}
                >
                  {page.status}
                </span>
              </button>
              <div className="space-y-1 px-3 py-3">
                <p className="truncate text-sm font-medium">{page.filename}</p>
                <p className="text-xs text-black/50">{stageLabel(page, job)}</p>
              </div>
            </article>
          );
        })}
      </div>

      {viewer && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setViewer(null)}
          role="presentation"
        >
          <div
            className="max-h-[92vh] max-w-4xl overflow-auto rounded-2xl bg-[var(--paper)] p-3 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true" /* page lightbox */
          >
            <div className="mb-2 flex items-center justify-between gap-3">
              <p className="truncate text-sm font-medium">{viewer.title}</p>
              <button
                type="button"
                onClick={() => setViewer(null)}
                className="rounded-lg bg-[var(--ink)] px-3 py-1.5 text-xs font-semibold text-[var(--paper)]"
              >
                Close
              </button>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={viewer.src} alt={viewer.title} className="max-h-[80vh] w-auto max-w-full rounded-lg" />
          </div>
        </div>
      )}
    </section>
  );
}
