"use client";
import { useState } from "react";
export function CopyJobId({ jobId }: { jobId: string }) {
  const [ok, setOk] = useState(false);
  return (
    <button
      type="button"
      className="text-xs text-black/45 hover:text-[var(--accent)]"
      onClick={async () => {
        await navigator.clipboard.writeText(jobId);
        setOk(true);
        setTimeout(() => setOk(false), 1200);
      }}
    >
      {ok ? "Copied id" : "Copy id"}
    </button>
  );
}
