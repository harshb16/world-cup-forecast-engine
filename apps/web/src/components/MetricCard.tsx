import { StatCard } from "@/components/ui/StatCard";

export function MetricCard({
  label,
  value,
  detail,
  tone = "default",
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: "default" | "neutral" | "green" | "amber" | "red";
}) {
  return (
    <StatCard
      label={label}
      value={value}
      detail={detail}
      tone={tone === "neutral" ? "default" : tone}
    />
  );
}
