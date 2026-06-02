"use client";

import { useEffect, useState } from "react";

const KEY = "komalingo.reader_mode";

export function ReaderToggle() {
  const [on, setOn] = useState(false);

  useEffect(() => {
    const saved = window.localStorage.getItem(KEY) === "1";
    setOn(saved);
    document.body.classList.toggle("reader-mode", saved);
  }, []);

  return (
    <button
      type="button"
      className="rounded-full border border-[var(--line)] bg-white/50 px-3 py-1.5 text-xs font-semibold"
      onClick={() => {
        const next = !on;
        setOn(next);
        document.body.classList.toggle("reader-mode", next);
        window.localStorage.setItem(KEY, next ? "1" : "0");
      }}
    >
      {on ? "Paper view" : "Reader view"}
    </button>
  );
}
