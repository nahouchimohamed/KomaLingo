"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReaderToggle } from "@/components/ReaderToggle";

const LINKS = [
  { href: "/", label: "Upload" },
  { href: "/history", label: "History" },
];

export function AppNav() {
  const path = usePathname();
  return (
    <nav className="mb-8 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <Link href="/" className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--accent)]">
          KomaLingo
        </Link>
        <div className="flex gap-1 rounded-full bg-black/5 p-1">
          {LINKS.map((link) => {
            const active = path === link.href || (link.href !== "/" && path.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
                  active ? "bg-[var(--ink)] text-[var(--paper)] shadow-[0_0_0_1px_rgba(196,60,40,0.35)]" : "text-black/60"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </div>
      <ReaderToggle />
    </nav>
  );
}
