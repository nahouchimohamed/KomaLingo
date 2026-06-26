"use client";
type Props = { message: string | null; onClose: () => void };
export function Toast({ message, onClose }: Props) {
  if (!message) return null;
  return (
    <div className="fixed bottom-5 right-5 z-[60] max-w-sm rounded-xl bg-[var(--ink)] px-4 py-3 text-sm text-[var(--paper)] shadow-lg">
      <div className="flex items-start gap-3">
        <p className="flex-1">{message}</p>
        <button type="button" className="text-xs opacity-70" onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
