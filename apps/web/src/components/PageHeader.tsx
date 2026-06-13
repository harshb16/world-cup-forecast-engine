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
    <header className="mb-6">
      {eyebrow ? (
        <p className="text-xs font-semibold uppercase text-emerald-200">
          {eyebrow}
        </p>
      ) : null}
      <h1 className="mt-1 text-3xl font-semibold tracking-normal text-white sm:text-4xl">
        {title}
      </h1>
      {description ? (
        <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-400">
          {description}
        </p>
      ) : null}
    </header>
  );
}
