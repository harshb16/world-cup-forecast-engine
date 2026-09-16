import { cn } from "@/lib/utils";

export function SectionCard({
  children,
  className = "",
  title,
  description,
}: {
  children: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
}) {
  return (
    <section className={cn("surface-panel relative overflow-hidden p-5", className)}>
      <div
        className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-primary via-chart-2 to-chart-3/80"
        aria-hidden="true"
      />
      {title ? (
        <header className="mb-4 pl-1">
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
          {description ? (
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          ) : null}
        </header>
      ) : null}
      <div className={title ? "pl-1" : undefined}>{children}</div>
    </section>
  );
}
