"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { JobProgress } from "@/components/JobProgress";
import { ChapterStatus, getChapter } from "@/lib/api";

export default function JobPage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;
  const [job, setJob] = useState<ChapterStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    let timer: number | undefined;

    async function poll() {
      try {
        const status = await getChapter(jobId);
        if (!cancelled) {
          setJob(status);
          setError(null);
        }
        if (status.status === "completed" || status.status === "failed" || status.status === "cancelled") {
          return;
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load job");
      }
      if (!cancelled) timer = window.setTimeout(poll, 1200);
    }

    poll();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId]);

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-5 pb-20 pt-10 sm:px-8">
      <div className="mb-6 flex gap-3 text-sm">
        <Link href="/" className="text-[var(--accent)] hover:underline">
          Upload
        </Link>
        <Link href="/history" className="text-[var(--accent)] hover:underline">
          History
        </Link>
      </div>
      {error && <p className="text-sm text-[var(--accent)]">{error}</p>}
      {job ? (
        <JobProgress job={job} onReset={() => (window.location.href = "/")} />
      ) : (
        <p className="text-sm text-black/55">Loading job…</p>
      )}
    </main>
  );
}
