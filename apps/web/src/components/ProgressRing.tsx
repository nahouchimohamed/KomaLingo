type Props = { value: number; size?: number };

export function ProgressRing({ value, size = 42 }: Props) {
  const r = (size - 6) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const offset = c - (pct / 100) * c;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-label={`${pct}%`}>
      <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(0,0,0,0.12)" strokeWidth="3" fill="none" />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke="var(--accent)"
        strokeWidth="3"
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text x="50%" y="54%" textAnchor="middle" fontSize="10" fontWeight="700" fill="currentColor">
        {pct}
      </text>
    </svg>
  );
}
