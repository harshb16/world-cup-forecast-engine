import { Skeleton } from "@/components/ui/skeleton";

export function LoadingSkeleton({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex flex-col gap-4" role="status" aria-label={label}>
      <Skeleton className="h-28 rounded-lg" />
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="h-24 rounded-lg" />
      </div>
      <span className="sr-only">{label}</span>
    </div>
  );
}
