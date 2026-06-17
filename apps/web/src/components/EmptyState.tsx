type Props = { title: string; body: string };

export function EmptyState({ title, body }: Props) {
  return (
    <div className="rounded-2xl border border-dashed border-[var(--line)] bg-white/40 px-6 py-10 text-center">
      <p className="text-lg font-semibold" style={{ fontFamily: "var(--font-display), sans-serif" }}>
        {title}
      </p>
      <p className="mt-2 text-sm text-black/55">{body}</p>
    </div>
  );
}
