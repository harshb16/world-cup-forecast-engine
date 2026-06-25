import { ProbabilityBar as BaseProbabilityBar } from "@/components/ui/ProbabilityBar";
import { cn } from "@/lib/utils";

export function ProbabilityBar({
  value,
  tone = "emerald",
  showLabel = true,
}: {
  value: number;
  tone?: "emerald" | "amber" | "rose";
  showLabel?: boolean;
}) {
  return (
    <div
      className={cn(
        tone === "amber" && "[&_[data-fill]]:bg-signal-amber",
        tone === "rose" && "[&_[data-fill]]:bg-signal-red",
      )}
    >
      <BaseProbabilityBar
        value={value}
        label={toneLabel[tone]}
        showLabel={showLabel}
      />
    </div>
  );
}

const toneLabel = {
  emerald: "Champion",
  amber: "Semi-final",
  rose: "Final",
};
