"use client";

import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { useEffect, useState } from "react";
import { ChapterSummary, deleteChapter, listChapters } from "@/lib/api";
import { StatusPill } from "@/components/StatusPill";
import { EmptyState } from "@/components/EmptyState";

export default function HistoryPage() {
  const [items, setItems] = useState<ChapterSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function refresh(nextStatus = status) {
    try {
      const data = await listChapters({ status: nextStatus || undefined, limit: 50 });
      setItems(data.items);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-5 pb-20 pt-10 sm:px-8">
      <AppNav />
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold" style={{ fontFamily: "var(--font-display), sans-serif" }}>
          Job history
        </h1>
        <p className="mt-2 text-sm text-black/55">{total} jobs</p>
      </div>

      <div className="mb-4 flex gap-2">
        {["", "processing", "completed", "failed", "cancelled"].map((value) => (
          <button
            key={value || "all"}
            type="button"
            onClick={() => {
              setStatus(value);
              refresh(value);
            }}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
              status === value ? "bg-[var(--accent)] text-white" : "bg-black/5 text-black/70"
            }`}
          >
            {value || "all"}
          </button>
        ))}
      </div>

      {error && <p className="mb-4 text-sm text-[var(--accent)]">{error}</p>}

      <div className="space-y-3">
        {items.map((job) => (
          <article key={job.job_id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[var(--line)] bg-white/70 px-4 py-3">
            <div>
              <Link href={`/job/${job.job_id}`} className="font-semibold text-[var(--ink)] hover:underline">
                {job.title}
              </Link>
              <div className="mt-1 flex items-center gap-2 text-xs text-black/50">
                <StatusPill status={job.status} />
                <span>
                  {job.completed_pages}/{job.total_pages} · {job.processing_mode}
                </span>
              </div>
            </div>
            <button
              type="button"
              disabled={busyId === job.job_id}
              onClick={async () => {
                setBusyId(job.job_id);
                try {
                  await deleteChapter(job.job_id);
                  await refresh();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Delete failed");
                } finally {
                  setBusyId(null);
                }
              }}
              className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-xs font-medium"
            >
              Delete
            </button>
          </article>
        ))}
        {!items.length && (
          <EmptyState title="No jobs yet" body="Upload a chapter to see it listed here." />
        )}
      </div>
    </main>
  );
}
