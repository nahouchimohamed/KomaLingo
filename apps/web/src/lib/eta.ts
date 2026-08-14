export function etaLabel(completed: number, total: number, startedAt?: string): string | null {
  if (!startedAt || completed <= 0 || total <= completed) return null;
  const elapsed = Date.now() - new Date(startedAt).getTime();
  if (elapsed <= 0) return null;
  const per = elapsed / completed;
  const remainMs = per * (total - completed);
  const mins = Math.max(1, Math.round(remainMs / 60000));
  return `~${mins}m left`;
}
