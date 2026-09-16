import { Info } from "lucide-react";

export function HelpText({ children }: { children: React.ReactNode }) {
  return (
    <p className="flex gap-2 rounded-md border border-border bg-accent/50 px-3 py-2 text-sm leading-6 text-muted-foreground">
      <Info size={16} aria-hidden="true" className="mt-1 shrink-0 text-cyan-200" />
      <span>{children}</span>
    </p>
  );
}
