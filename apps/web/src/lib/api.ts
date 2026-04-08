export type RegionStatus = {
  text: string;
  translation: string;
  bbox: number[];
  confidence: number;
  language: string;
};

export type PageStatus = {
  index: number;
  filename: string;
  status: "pending" | "processing" | "done" | "failed";
  stage: string | null;
  original_url: string | null;
  preview_url: string | null;
  regions_url: string | null;
  error: string | null;
};

export type ChapterStatus = {
  job_id: string;
  title: string;
  status: string;
  source_lang: string;
  target_lang: string;
  processing_mode: string;
  total_pages: number;
  completed_pages: number;
  failed_pages?: number;
  progress: number;
  current_stage: string;
  error: string | null;
  cancel_requested?: boolean;
  font_name?: string | null;
  pages: PageStatus[];
  download_ready: boolean;
  created_at: string;
  updated_at: string;
};

export type ChapterSummary = {
  job_id: string;
  title: string;
  status: string;
  processing_mode: string;
  total_pages: number;
  completed_pages: number;
  failed_pages: number;
  progress: number;
  current_stage: string;
  error: string | null;
  download_ready: boolean;
  created_at: string;
  updated_at: string;
};

export type PageRegions = {
  mode: string;
  regions: RegionStatus[];
};

export async function createChapter(form: FormData): Promise<{
  job_id: string;
  total_pages: number;
  processing_mode: string;
}> {
  const res = await fetch("/api/chapters", {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || "Upload failed");
  }
  return res.json();
}

export async function getChapter(jobId: string): Promise<ChapterStatus> {
  const res = await fetch(`/api/chapters/${jobId}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to load job status");
  }
  return res.json();
}

export async function listChapters(params?: { status?: string; limit?: number }): Promise<{
  items: ChapterSummary[];
  total: number;
}> {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.limit) q.set("limit", String(params.limit));
  const res = await fetch(`/api/chapters?${q.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to list jobs");
  return res.json();
}

export async function cancelChapter(jobId: string): Promise<void> {
  const res = await fetch(`/api/chapters/${jobId}/cancel`, { method: "POST" });
  if (!res.ok) throw new Error("Cancel failed");
}

export async function deleteChapter(jobId: string): Promise<void> {
  const res = await fetch(`/api/chapters/${jobId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

export async function retryChapter(jobId: string): Promise<{ job_id: string }> {
  const res = await fetch(`/api/chapters/${jobId}/retry`, { method: "POST" });
  if (!res.ok) throw new Error("Retry failed");
  return res.json();
}

export async function getPageRegions(jobId: string, pageIndex: number): Promise<PageRegions> {
  const res = await fetch(`/api/chapters/${jobId}/pages/${pageIndex}/regions`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to load page regions");
  }
  return res.json();
}

export async function reprocessPage(jobId: string, pageIndex: number): Promise<void> {
  const res = await fetch(`/api/chapters/${jobId}/pages/${pageIndex}/reprocess`, { method: "POST" });
  if (!res.ok) throw new Error("Reprocess failed");
}

export function downloadUrl(jobId: string): string {
  return `/api/chapters/${jobId}/download`;
}

export function partialDownloadUrl(jobId: string, format: "zip" | "cbz" = "zip"): string {
  return `/api/chapters/${jobId}/download/partial?format=${format}`;
}
