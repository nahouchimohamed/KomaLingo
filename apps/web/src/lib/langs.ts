export const SOURCE_LABELS: Record<string, string> = { auto: "Auto", ja: "Japanese", ko: "Korean", zh: "Chinese" };
export const TARGET_LABELS: Record<string, string> = { en: "English", fr: "French", es: "Spanish", de: "German", pt: "Portuguese" };
export function langLabel(code: string, map: Record<string, string>): string { return map[code] || code; }
