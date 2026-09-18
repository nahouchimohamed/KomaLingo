import type { ChapterSummary } from "@/lib/api";
export function filterJobs(items: ChapterSummary[], query: string): ChapterSummary[] {
  const q = query.trim().toLowerCase();
  if (!q) return items;
  return items.filter((j) => j.title.toLowerCase().includes(q) || j.job_id.toLowerCase().includes(q));
}
