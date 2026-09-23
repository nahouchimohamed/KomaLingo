"use client";
import { useState } from "react";
export function SettingsDrawer({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-[var(--line)] bg-white/40">
      <button type="button" className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold" onClick={() => setOpen(v => !v)}>
        <span>{title}</span>
        <span className="text-xs text-black/45">{open ? "Hide" : "Show"}</span>
      </button>
      {open && <div className="space-y-4 border-t border-[var(--line)] px-4 py-4">{children}</div>}
    </div>
  );
}
