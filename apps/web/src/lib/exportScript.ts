import type { RegionStatus } from "@/lib/api";

export function regionsToTxt(regions: RegionStatus[]): string {
  return regions
    .map((r, i) => `#${i + 1}\nSRC: ${r.text}\nEN: ${r.translation || ""}\n`)
    .join("\n");
}

export function regionsToCsv(regions: RegionStatus[]): string {
  const header = "index,text,translation,language,confidence";
  const rows = regions.map((r, i) =>
    [i + 1, csv(r.text), csv(r.translation), csv(r.language), r.confidence].join(",")
  );
  return [header, ...rows].join("\n");
}

function csv(value: string): string {
  const v = value.replaceAll('"', '""');
  return `"${v}"`;
}

export function downloadText(filename: string, content: string, mime = "text/plain") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
