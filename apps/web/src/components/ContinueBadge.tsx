export function ContinueBadge({ enabled }: { enabled?: boolean }) {
  if (!enabled) return null;
  return <span className="rounded-full bg-[var(--ok)]/15 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-[var(--ok)]">continues on errors</span>;
}
