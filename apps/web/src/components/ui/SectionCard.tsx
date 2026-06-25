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
    <section
      className={cn(
        "relative overflow-hidden rounded-lg border border-border bg-card/85 p-5 shadow-lg",
        className,
      )}
    >
      <div
        className="absolute inset-y-0 left-0 w-1 bg-primary"
        aria-hidden="true"
      />
      {title ? (
        <header className="mb-4">
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
          {description ? (
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          ) : null}
        </header>
      ) : null}
      {children}
    </section>
  );
}
