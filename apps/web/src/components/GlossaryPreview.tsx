import { useMemo } from "react";
type Props = { raw: string };
export function GlossaryPreview({ raw }: Props) {
  const pairs = useMemo(() => raw.split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("#") && l.includes("=")).map(l => {
    const [src, dst] = l.split("=", 1);
    return { src: src.trim(), dst: (dst || "").trim() };
  }).slice(0, 8), [raw]);
  if (!pairs.length) return null;
  return (
    <ul className="mt-2 flex flex-wrap gap-2">
      {pairs.map((pair) => (
        <li key={pair.src} className="rounded-full bg-black/5 px-2 py-1 text-[11px]">
          <span className="text-black/45">{pair.src}</span> → <span className="font-medium">{pair.dst}</span>
        </li>
      ))}
    </ul>
  );
}
