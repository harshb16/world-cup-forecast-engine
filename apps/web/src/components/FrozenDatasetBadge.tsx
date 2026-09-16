import { Badge } from "@/components/ui/badge";

type FrozenDatasetBadgeProps = {
  label: string;
  compact?: boolean;
};

export function FrozenDatasetBadge({
  label,
  compact = false,
}: FrozenDatasetBadgeProps) {
  if (compact) {
    return (
      <Badge variant="secondary" className="font-normal">
        {label}
      </Badge>
    );
  }

  return (
    <Badge variant="secondary" className="font-normal">
      {label}
    </Badge>
  );
}
