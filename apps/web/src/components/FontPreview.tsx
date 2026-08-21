export function FontPreview({ fontName }: { fontName: string }) {
  const family =
    fontName === "comic" ? "Comic Sans MS, comic, sans-serif" :
    fontName === "heavy" ? "Impact, Haettenschweiler, sans-serif" :
    fontName === "sans" ? "Segoe UI, Helvetica, sans-serif" :
    "Georgia, Times New Roman, serif";
  return <p className="mt-1 text-sm text-black/70" style={{ fontFamily: family }}>Sample bubble text</p>;
}
