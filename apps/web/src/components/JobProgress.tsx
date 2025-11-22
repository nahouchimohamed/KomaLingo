"use client";

import { useEffect, useMemo, useState } from "react";
import type { ChapterStatus, PageRegions, PageStatus, RegionStatus } from "@/lib/api";
import { downloadUrl, getPageRegions } from "@/lib/api";

type Props = {
  job: ChapterStatus;
  onReset: () => void;
};

function modeLabel(mode: string): string {
  if (mode === "strip") return "Strip text";
  if (mode === "translate_only") return "Translate only";
  return "Full redraw";
}

function doneLabel(mode: string): string {
  if (mode === "strip") return "Text stripped — click to view";
  if (mode === "translate_only") return "Translation ready — click for text";
  return "Translated — click to view";
}

function stageLabel(page: PageStatus, job: ChapterStatus): string {
  if (page.status === "done") return doneLabel(job.processing_mode);
  if (page.status === "failed") return page.error || "Failed";
  if (page.status === "processing") {
    const stage = page.stage || job.current_stage || "working";
    if (stage.startsWith("ocr")) return "Reading text (OCR)…";
    if (stage.startsWith("translate")) return "Translating…";
    if (stage.startsWith("inpaint")) {
      return job.processing_mode === "strip" ? "Erasing text…" : "Cleaning bubbles…";
    }
    if (stage.startsWith("typeset")) return "Drawing English…";
    return stage;
  }
  return "Queued";
}

function downloadButtonLabel(mode: string): string {
  if (mode === "strip") return "Download cleaned ZIP";
  if (mode === "translate_only") return "Download pages + translations";
  return "Download translated ZIP";
}

export function JobProgress({ job, onReset }: Props) {
  const pct = Math.round(job.progress * 100);
  const [viewer, setViewer] = useState<{ src: string; title: string; pageIndex: number } | null>(null);
  const [regions, setRegions] = useState<RegionStatus[] | null>(null);
  const [regionsLoading, setRegionsLoading] = useState(false);

  const hint = useMemo(() => {
    if (job.status === "completed") return "All pages ready.";
    if (job.completed_pages === 0 && job.status === "processing") {
      return "First page may take a bit while OCR models load. Later pages are faster — each finished page appears below.";
    }
    if (job.processing_mode === "translate_only") {
      return "Original art stays untouched. Open a finished page to read the English lines.";
    }
    if (job.processing_mode === "strip") {
      return "Dialogue is erased from each page as it finishes. No translation is written back.";
    }
    return "Pages unlock one-by-one as they finish. Click any completed page to zoom.";
  }, [job]);

  useEffect(() => {
    if (!viewer || job.processing_mode !== "translate_only") {
      setRegions(null);
      return;
    }
    const page = job.pages[viewer.pageIndex];
    if (!page?.regions_url) {
      setRegions([]);
      return;
    }
    let cancelled = false;
    setRegionsLoading(true);
    getPageRegions(job.job_id, viewer.pageIndex)
      .then((payload: PageRegions) => {
        if (!cancelled) setRegions(payload.regions);
      })
      .catch(() => {
        if (!cancelled) setRegions([]);
      })
      .finally(() => {
        if (!cancelled) setRegionsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [viewer, job.job_id, job.pages, job.processing_mode]);

  return (
    <section className="rise space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-black/45">Job · {modeLabel(job.processing_mode)}</p>
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
              {downloadButtonLabel(job.processing_mode)}
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
          const imageSrc = page.preview_url || page.original_url;
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
                    title: `${page.filename} · ${page.status}`,
                    pageIndex: page.index,
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
            className="grid max-h-[92vh] w-full max-w-5xl gap-4 overflow-auto rounded-2xl bg-[var(--paper)] p-3 shadow-2xl lg:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.9fr)]"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div>
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
            {job.processing_mode === "translate_only" && (
              <div className="rounded-xl border border-[var(--line)] bg-white/70 p-3">
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-black/45">Translations</p>
                {regionsLoading ? (
                  <p className="text-sm text-black/50">Loading…</p>
                ) : !regions || regions.length === 0 ? (
                  <p className="text-sm text-black/50">No dialogue detected on this page.</p>
                ) : (
                  <ul className="max-h-[70vh] space-y-3 overflow-auto pr-1">
                    {regions.map((region, index) => (
                      <li key={`${region.bbox.join("-")}-${index}`} className="rounded-lg bg-[var(--paper-deep)]/60 p-3">
                        <p className="text-xs text-black/45">{region.text || "—"}</p>
                        <p className="mt-1 text-sm font-medium text-[var(--ink)]">
                          {region.translation || "(no translation)"}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
