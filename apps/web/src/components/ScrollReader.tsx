"use client";
type Props = { images: { src: string; title: string }[] };
export function ScrollReader({ images }: Props) {
  if (!images.length) return null;
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-3">
      {images.map((img) => (
        // eslint-disable-next-line @next/next/no-img-element
        <img key={img.src} src={img.src} alt={img.title} className="w-full rounded-lg" />
      ))}
    </div>
  );
}
