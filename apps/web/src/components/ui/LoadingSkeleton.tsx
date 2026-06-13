export function LoadingSkeleton({ label = "Loading" }: { label?: string }) {
  return (
    <div className="space-y-4" role="status" aria-label={label}>
      <div className="h-28 animate-pulse rounded-lg border border-white/10 bg-white/[0.06]" />
      <div className="grid gap-4 md:grid-cols-3">
        <div className="h-24 animate-pulse rounded-lg border border-white/10 bg-white/[0.05]" />
        <div className="h-24 animate-pulse rounded-lg border border-white/10 bg-white/[0.05]" />
        <div className="h-24 animate-pulse rounded-lg border border-white/10 bg-white/[0.05]" />
      </div>
      <span className="sr-only">{label}</span>
    </div>
  );
}
