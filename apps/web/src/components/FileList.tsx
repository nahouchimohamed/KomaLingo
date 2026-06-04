import { moveItem } from "@/lib/reorder";

type Props = { files: File[]; onChange: (files: File[]) => void };

export function FileList({ files, onChange }: Props) {
  if (!files.length) return null;
  return (
    <ul className="mt-4 max-h-48 space-y-1 overflow-auto text-left text-sm">
      {files.map((file, index) => (
        <li key={`${file.name}-${index}`} className="flex items-center justify-between gap-2 rounded-lg bg-white/70 px-3 py-1.5">
          <span className="truncate">{index + 1}. {file.name}</span>
          <span className="flex shrink-0 gap-1">
            <button type="button" className="text-xs text-black/50" disabled={index === 0} onClick={() => onChange(moveItem(files, index, index - 1))}>Up</button>
            <button type="button" className="text-xs text-black/50" disabled={index === files.length - 1} onClick={() => onChange(moveItem(files, index, index + 1))}>Down</button>
            <button type="button" className="text-xs text-[var(--accent)]" onClick={() => onChange(files.filter((_, i) => i !== index))}>Remove</button>
          </span>
        </li>
      ))}
    </ul>
  );
}
