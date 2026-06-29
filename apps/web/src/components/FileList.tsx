type Props = { files: File[]; onRemove: (index: number) => void };

export function FileList({ files, onRemove }: Props) {
  if (!files.length) return null;
  return (
    <ul className="mt-4 max-h-40 space-y-1 overflow-auto text-left text-sm">
      {files.map((file, index) => (
        <li key={`${file.name}-${index}`} className="flex items-center justify-between gap-2 rounded-lg bg-white/70 px-3 py-1.5">
          <span className="truncate">{file.name}</span>
          <button type="button" className="text-xs text-[var(--accent)]" onClick={() => onRemove(index)}>
            Remove
          </button>
        </li>
      ))}
    </ul>
  );
}
