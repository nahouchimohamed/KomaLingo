"use client";

import { useState } from "react";

type Props = {
  beforeSrc: string;
  afterSrc: string;
  alt: string;
};

export function CompareSlider({ beforeSrc, afterSrc, alt }: Props) {
  const [pct, setPct] = useState(50);
  return (
    <div className="relative overflow-hidden rounded-lg">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={beforeSrc} alt={`${alt} original`} className="block w-full" />
      <div className="absolute inset-0 overflow-hidden" style={{ width: `${pct}%` }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={afterSrc} alt={`${alt} result`} className="block h-full max-w-none" style={{ width: `${10000 / Math.max(pct, 1)}%`, maxWidth: "none" }} />
      </div>
      <input
        aria-label="Compare original and result"
        type="range"
        min={0}
        max={100}
        value={pct}
        onChange={(e) => setPct(Number(e.target.value))}
        className="absolute bottom-3 left-1/2 w-2/3 -translate-x-1/2"
      />
    </div>
  );
}
