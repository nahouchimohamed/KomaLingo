export type ProcessingMode = "full" | "strip" | "translate_only" | "ocr_only" | "typeset_from_json";

export type UploadOptions = {
  files: File[];
  title: string;
  sourceLang: string;
  targetLang: string;
  processingMode: ProcessingMode;
  translateProvider: string;
  translateApiKey: string;
  fontName: string;
  glossary: string;
  skipSfx: boolean;
};

export const MODE_COPY: Record<ProcessingMode, { label: string; hint: string; submit: string }> = {
  full: {
    label: "Full translate + redraw",
    hint: "OCR → translate → clean bubbles → draw English on the page.",
    submit: "Translate to English",
  },
  strip: {
    label: "Strip text only",
    hint: "Erase dialogue bubbles and leave clean art — no translation pass.",
    submit: "Strip text from pages",
  },
  translate_only: {
    label: "Translate without redraw",
    hint: "Keep original art. Export OCR text + English beside each page.",
    submit: "Translate text only",
  },
  ocr_only: {
    label: "OCR only",
    hint: "Detect bubbles and save region JSON without translating.",
    submit: "Run OCR only",
  },
  typeset_from_json: {
    label: "Typeset from JSON",
    hint: "Re-draw pages using an existing regions sidecar (after edits).",
    submit: "Typeset from regions",
  },
};
