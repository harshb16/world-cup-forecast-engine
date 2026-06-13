import { ProbabilityBar as BaseProbabilityBar } from "@/components/ui/ProbabilityBar";

export function ProbabilityBar({
  value,
  tone = "emerald",
}: {
  value: number;
  tone?: "emerald" | "amber" | "rose";
}) {
  return <BaseProbabilityBar value={value} label={toneLabel[tone]} />;
}

const toneLabel = {
  emerald: "Champion",
  amber: "Semi-final",
  rose: "Final",
};
