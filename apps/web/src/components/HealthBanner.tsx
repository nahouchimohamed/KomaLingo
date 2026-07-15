"use client";
import { useEffect, useState } from "react";
type Health = { status: string; redis_ok?: boolean; database_ok?: boolean };
export function HealthBanner() {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetch("/api/health").then(r => r.json()).then(d => { if (!cancelled) setHealth(d); })
      .catch(() => { if (!cancelled) setHealth({ status: "down" }); });
    return () => { cancelled = true; };
  }, []);
  if (!health || health.status === "ok") return null;
  return (
    <div className="mb-4 rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/10 px-4 py-3 text-sm text-[var(--accent)]">
      API is {health.status}. Redis: {String(health.redis_ok)} · DB: {String(health.database_ok)}
    </div>
  );
}
