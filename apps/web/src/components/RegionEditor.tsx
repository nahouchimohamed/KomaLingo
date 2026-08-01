"use client";

import { useState } from "react";
import type { RegionStatus } from "@/lib/api";
import { confidenceColor, confidenceLabel } from "@/lib/confidence";

type Props = {
  regions: RegionStatus[];
  onSave: (regions: RegionStatus[]) => Promise<void>;
};

export function RegionEditor({ regions, onSave }: Props) {
  const [draft, setDraft] = useState(regions);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-black/45">Edit translations</p>
      <ul className="max-h-[50vh] space-y-2 overflow-auto">
        {draft.map((region, index) => (
          <li key={`${region.bbox.join("-")}-${index}`} className="rounded-lg bg-[var(--paper-deep)]/60 p-2">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs text-black/45">{region.text}</p>
              <span className={`text-[10px] font-semibold uppercase ${confidenceColor(region.confidence)}`}>
                {confidenceLabel(region.confidence)}
              </span>
            </div>
            <textarea
              className="mt-1 w-full rounded-md border border-[var(--line)] bg-white/80 px-2 py-1 text-sm"
              rows={2}
              value={region.translation}
              onChange={(e) => {
                const next = [...draft];
                next[index] = { ...region, translation: e.target.value };
                setDraft(next);
              }}
            />
          </li>
        ))}
      </ul>
      {error && <p className="text-xs text-[var(--accent)]">{error}</p>}
      <button
        type="button"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError(null);
          try {
            await onSave(draft);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Save failed");
          } finally {
            setBusy(false);
          }
        }}
        className="rounded-lg bg-[var(--ink)] px-3 py-1.5 text-xs font-semibold text-[var(--paper)]"
      >
        {busy ? "Saving…" : "Save & re-typeset"}
      </button>
    </div>
  );
}
