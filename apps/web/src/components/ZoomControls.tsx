"use client";
type Props = { zoom: number; onChange: (zoom: number) => void };
export function ZoomControls({ zoom, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <button type="button" className="rounded-lg border border-[var(--line)] px-2 py-1" onClick={() => onChange(Math.max(0.5, zoom - 0.1))}>-</button>
      <span className="w-10 text-center font-semibold">{Math.round(zoom * 100)}%</span>
      <button type="button" className="rounded-lg border border-[var(--line)] px-2 py-1" onClick={() => onChange(Math.min(2.5, zoom + 0.1))}>+</button>
    </div>
  );
}
