"use client";

import { useEffect, useMemo, useState } from "react";
import type { ChapterStatus, PageRegions, PageStatus, RegionStatus } from "@/lib/api";
import {
  cancelChapter,
  downloadUrl,
  getPageRegions,
  partialDownloadUrl,
  reprocessPage,
  retryChapter,
} from "@/lib/api";
import { CompareSlider } from "@/components/CompareSlider";
import { ProgressRing } from "@/components/ProgressRing";
import { ZoomControls } from "@/components/ZoomControls";
import { Toast } from "@/components/Toast";
import { PageSkeleton } from "@/components/PageSkeleton";
import { ScrollReader } from "@/components/ScrollReader";
import { RegionEditor } from "@/components/RegionEditor";
import { downloadText, regionsToCsv, regionsToTxt } from "@/lib/exportScript";

type Props = {
  job: ChapterStatus;
  onReset: () => void;
};

function modeLabel(mode: string): string {
  if (mode === "strip") return "Strip text";
  if (mode === "translate_only") return "Translate only";
  if (mode === "ocr_only") return "OCR only";
  if (mode === "typeset_from_json") return "Typeset from JSON";
  return "Full redraw";
}

function doneLabel(mode: string): string {
  if (mode === "strip") return "Text stripped — click to view";
  if (mode === "translate_only" || mode === "ocr_only") return "Ready — click for text";
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
    if (stage.startsWith("typeset")) return "Drawing text…";
    return stage;
  }
  return "Queued";
}

export function JobProgress({ job, onReset }: Props) {
  const pct = Math.round(job.progress * 100);
  const [viewer, setViewer] = useState<{ src: string; title: string; pageIndex: number } | null>(null);
  const [regions, setRegions] = useState<RegionStatus[] | null>(null);
  const [regionsLoading, setRegionsLoading] = useState(false);
  const [compare, setCompare] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [scrollMode, setScrollMode] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const hint = useMemo(() => {
    if (job.status === "completed") return "All pages ready.";
    if (job.status === "cancelled") return "Job cancelled.";
    if (job.completed_pages === 0 && job.status === "processing") {
      return "First page may take a bit while OCR models load.";
    }
    return "Pages unlock one-by-one. Use arrow keys in the viewer.";
  }, [job]);

  useEffect(() => {
    if (!viewer) {
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
  }, [viewer, job.job_id, job.pages]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!viewer) return;
      if (e.key === "Escape") setViewer(null);
      if (e.key === "ArrowRight") {
        const next = Math.min(job.pages.length - 1, viewer.pageIndex + 1);
        const page = job.pages[next];
        const src = page.preview_url || page.original_url;
        if (src) setViewer({ src, title: page.filename, pageIndex: next });
      }
      if (e.key === "ArrowLeft") {
        const next = Math.max(0, viewer.pageIndex - 1);
        const page = job.pages[next];
        const src = page.preview_url || page.original_url;
        if (src) setViewer({ src, title: page.filename, pageIndex: next });
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [viewer, job.pages]);

  return (
    <section className="rise soft-panel space-y-6 rounded-3xl p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <ProgressRing value={pct} />
            <p className="text-xs uppercase tracking-[0.18em] text-black/45">Job · {modeLabel(job.processing_mode)}</p>
          </div>
          <h2 className="text-2xl font-bold" style={{ fontFamily: "var(--font-display), sans-serif" }}>
            {job.title}
          </h2>
          <p className="mt-1 text-sm text-black/55">
            {job.completed_pages}/{job.total_pages} pages · {job.current_stage}
            {job.failed_pages ? ` · ${job.failed_pages} failed` : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {job.status === "processing" && (
            <button
              type="button"
              onClick={async () => {
                try {
                  await cancelChapter(job.job_id);
                } catch (err) {
                  setActionError(err instanceof Error ? err.message : "Cancel failed");
                }
              }}
              className="rounded-xl border border-[var(--line)] bg-white/70 px-4 py-2.5 text-sm font-medium"
            >
              Cancel
            </button>
          )}
          {(job.status === "failed" || job.status === "cancelled" || job.status === "completed") && (
            <button
              type="button"
              onClick={async () => {
                try {
                  await retryChapter(job.job_id);
                } catch (err) {
                  setActionError(err instanceof Error ? err.message : "Retry failed");
                }
              }}
              className="rounded-xl border border-[var(--line)] bg-white/70 px-4 py-2.5 text-sm font-medium"
            >
              Retry
            </button>
          )}
          {job.completed_pages > 0 && (
            <a
              href={partialDownloadUrl(job.job_id, "zip")}
              className="rounded-xl border border-[var(--line)] bg-white/70 px-4 py-2.5 text-sm font-medium"
            >
              Partial ZIP
            </a>
          )}
          {job.download_ready && (
            <a
              href={downloadUrl(job.job_id)}
              className="rounded-xl bg-[var(--ink)] px-4 py-2.5 text-sm font-semibold text-[var(--paper)]"
            >
              Download ZIP
            </a>
          )}
          <button
            type="button"
            onClick={() => setScrollMode((v) => !v)}
            className="rounded-xl border border-[var(--line)] bg-white/70 px-4 py-2.5 text-sm font-medium"
          >
            {scrollMode ? "Grid view" : "Scroll view"}
          </button>
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

      {(job.error || actionError) && (
        <div className="rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/10 px-4 py-3 text-sm text-[var(--accent)]">
          {actionError || job.error}
        </div>
      )}

      {scrollMode ? (
        <ScrollReader
          images={job.pages
            .filter((p) => p.preview_url || p.original_url)
            .map((p) => ({ src: (p.preview_url || p.original_url)!, title: p.filename }))}
        />
      ) : (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {job.pages.map((page) => {
          const imageSrc = page.preview_url || page.original_url;
          const canOpen = Boolean(imageSrc);
          return (
            <article
              key={page.index}
              className={`page-card overflow-hidden rounded-2xl border bg-white/60 shadow-[0_10px_30px_rgba(18,16,14,0.06)] ${
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
                    className={`h-full w-full object-cover transition ${page.status === "done" ? "" : "opacity-70"}`}
                  />
                ) : page.status === "pending" ? (
                  <div className="p-2"><PageSkeleton /></div>
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
                        : "bg-black/45"
                  }`}
                >
                  {page.status}
                </span>
              </button>
              <div className="space-y-1 px-3 py-3">
                <p className="truncate text-sm font-medium">{page.filename}</p>
                <p className="text-xs text-black/50">{stageLabel(page, job)}</p>
                {page.status === "failed" && (
                  <button
                    type="button"
                    className="text-xs font-medium text-[var(--accent)]"
                    onClick={() => reprocessPage(job.job_id, page.index)}
                  >
                    Reprocess page
                  </button>
                )}
              </div>
            </article>
          );
        })}
      </div>

            <Toast message={actionError} onClose={() => setActionError(null)} />

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
              <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
                <p className="truncate text-sm font-medium">{viewer.title}</p>
                <div className="flex gap-2">
                  {job.pages[viewer.pageIndex]?.original_url && job.pages[viewer.pageIndex]?.preview_url && (
                    <button type="button" className="rounded-lg border border-[var(--line)] px-2 py-1 text-xs" onClick={() => setCompare((v) => !v)}>
                      {compare ? "Single" : "Compare"}
                    </button>
                  <ZoomControls zoom={zoom} onChange={setZoom} />
                  )}
                  <button
                    type="button"
                    onClick={() => setViewer(null)}
                    className="rounded-lg bg-[var(--ink)] px-3 py-1.5 text-xs font-semibold text-[var(--paper)]"
                  >
                    Close
                  </button>
                </div>
              </div>
              {compare && job.pages[viewer.pageIndex]?.original_url && job.pages[viewer.pageIndex]?.preview_url ? (
                <CompareSlider
                  beforeSrc={job.pages[viewer.pageIndex].original_url!}
                  afterSrc={job.pages[viewer.pageIndex].preview_url!}
                  alt={viewer.title}
                />
              ) : (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={viewer.src} alt={viewer.title} className="max-h-[80vh] w-auto max-w-full rounded-lg origin-top-left transition-transform" style={{ transform: `scale(${zoom})` }} />
              )}
            </div>
            <div className="space-y-3 rounded-xl border border-[var(--line)] bg-white/70 p-3">
              {regionsLoading ? (
                <p className="text-sm text-black/50">Loading…</p>
              ) : regions && regions.length > 0 ? (
                <>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="rounded-lg border border-[var(--line)] px-2 py-1 text-xs"
                      onClick={() => downloadText(`${viewer.title}.txt`, regionsToTxt(regions))}
                    >
                      Export TXT
                    </button>
                    <button
                      type="button"
                      className="rounded-lg border border-[var(--line)] px-2 py-1 text-xs"
                      onClick={() => downloadText(`${viewer.title}.csv`, regionsToCsv(regions), "text/csv")}
                    >
                      Export CSV
                    </button>
                  </div>
                  <RegionEditor
                    regions={regions}
                    onSave={async (next) => {
                      const res = await fetch(`/api/chapters/${job.job_id}/pages/${viewer.pageIndex}/regions`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ regions: next }),
                      });
                      if (!res.ok) throw new Error("Save failed");
                      setRegions(next);
                    }}
                  />
                </>
              ) : (
                <p className="text-sm text-black/50">No region sidecar for this page.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
