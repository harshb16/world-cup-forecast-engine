export function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-white/15 bg-white/[0.035] p-6 text-center">
      <p className="font-semibold text-white">{title}</p>
      {description ? (
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-zinc-400">
          {description}
        </p>
      ) : null}
    </div>
  );
}
