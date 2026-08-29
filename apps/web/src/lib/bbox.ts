export function clampBox(box: number[], width: number, height: number): number[] {
  const [x1, y1, x2, y2] = box;
  return [
    Math.max(0, Math.min(width, x1)),
    Math.max(0, Math.min(height, y1)),
    Math.max(0, Math.min(width, x2)),
    Math.max(0, Math.min(height, y2)),
  ];
}
