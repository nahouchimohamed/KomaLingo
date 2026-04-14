"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ChapterSummary, deleteChapter, listChapters } from "@/lib/api";

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
      <div className="mb-8 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--accent)]">KomaLingo</p>
          <h1 className="text-3xl font-extrabold" style={{ fontFamily: "var(--font-display), sans-serif" }}>
            Job history
          </h1>
          <p className="mt-2 text-sm text-black/55">{total} jobs</p>
        </div>
        <Link href="/" className="rounded-xl bg-[var(--ink)] px-4 py-2.5 text-sm font-semibold text-[var(--paper)]">
          New chapter
        </Link>
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
              <p className="text-xs text-black/50">
                {job.status} · {job.completed_pages}/{job.total_pages} · {job.processing_mode}
              </p>
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
        {!items.length && <p className="text-sm text-black/50">No jobs yet.</p>}
      </div>
    </main>
  );
}
