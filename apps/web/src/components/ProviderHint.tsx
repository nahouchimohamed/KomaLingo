export function ProviderHint({ provider }: { provider?: string | null }) {
  return <span className="text-xs text-black/45">Translator: {provider || "google"}</span>;
}
