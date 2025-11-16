export type PageStatus = {
  index: number;
  filename: string;
  status: "pending" | "processing" | "done" | "failed";
  stage: string | null;
  original_url: string | null;
  preview_url: string | null;
  error: string | null;
};

export type ChapterStatus = { // mirrored from FastAPI schema
  job_id: string;
  title: string;
  status: string;
  source_lang: string;
  target_lang: string;
  total_pages: number;
  completed_pages: number;
  progress: number;
  current_stage: string;
  error: string | null;
  pages: PageStatus[];
  download_ready: boolean;
  created_at: string;
  updated_at: string;
};

export async function createChapter(form: FormData): Promise<{ job_id: string; total_pages: number }> {
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

export function downloadUrl(jobId: string): string {
  return `/api/chapters/${jobId}/download`;
}
