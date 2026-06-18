export function PageHeader({
  title,
  description,
  eyebrow,
}: {
  title: string;
  description?: string;
  eyebrow?: string;
}) {
  return (
    <header className="mb-6 border-b border-white/10 pb-5">
      {eyebrow ? (
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-[var(--turf)]">
          {eyebrow}
        </p>
      ) : null}
      <h1 className="mt-2 max-w-5xl text-4xl font-semibold tracking-normal text-[#f4f7f5] sm:text-5xl">
        {title}
      </h1>
      {description ? (
        <p className="mt-3 max-w-3xl text-sm leading-6 text-[#93a19a]">
          {description}
        </p>
      ) : null}
    </header>
  );
}
