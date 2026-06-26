import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  description,
  eyebrow,
  actions,
  meta,
}: {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: React.ReactNode;
  meta?: React.ReactNode;
}) {
  return (
    <header className="mb-6 border-b border-border pb-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          {eyebrow ? <p className="text-eyebrow">{eyebrow}</p> : null}
          <h1
            className={cn(
              "font-display mt-2 max-w-5xl text-4xl font-semibold tracking-normal text-foreground sm:text-5xl",
              eyebrow && "mt-2",
            )}
          >
            {title}
          </h1>
          {description ? (
            <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        {(actions || meta) && (
          <div className="flex shrink-0 flex-col items-start gap-3 lg:items-end">
            {meta}
            {actions}
          </div>
        )}
      </div>
    </header>
  );
}
