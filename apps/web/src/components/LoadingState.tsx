import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return <LoadingSkeleton label={label} />;
}
