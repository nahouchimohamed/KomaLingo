type Props = { status: string };

const COLORS: Record<string, string> = {
  done: "bg-[var(--ok)]",
  completed: "bg-[var(--ok)]",
  processing: "bg-[var(--accent)]",
  failed: "bg-[var(--accent)]",
  cancelled: "bg-black/45",
  pending: "bg-black/45",
};

export function StatusPill({ status }: Props) {
  return (
    <span
      className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-white ${
        COLORS[status] || "bg-black/45"
      }`}
    >
      {status}
    </span>
  );
}
