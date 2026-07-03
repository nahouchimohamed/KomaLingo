export function confidenceLabel(value: number): string {
  if (value >= 0.85) return "high";
  if (value >= 0.6) return "medium";
  return "low";
}
export function confidenceColor(value: number): string {
  if (value >= 0.85) return "text-[var(--ok)]";
  if (value >= 0.6) return "text-[var(--warn)]";
  return "text-[var(--accent)]";
}
