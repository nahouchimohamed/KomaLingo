export function PageSkeleton() {
  return (
    <div className="animate-pulse overflow-hidden rounded-2xl border border-[var(--line)] bg-white/50">
      <div className="aspect-[3/4] bg-black/10" />
      <div className="space-y-2 px-3 py-3">
        <div className="h-3 w-2/3 rounded bg-black/10" />
        <div className="h-2 w-1/2 rounded bg-black/10" />
      </div>
    </div>
  );
}
