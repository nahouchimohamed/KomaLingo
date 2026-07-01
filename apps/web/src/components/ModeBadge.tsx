const LABELS: Record<string, string> = {
  full: "Full redraw", strip: "Strip text", translate_only: "Translate only",
  ocr_only: "OCR only", typeset_from_json: "Typeset JSON",
};
export function ModeBadge({ mode }: { mode: string }) {
  return (
    <span className="rounded-full bg-[var(--accent)]/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-[var(--accent)]">
      {LABELS[mode] || mode}
    </span>
  );
}
