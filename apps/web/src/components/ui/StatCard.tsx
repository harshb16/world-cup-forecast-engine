export function StatCard({
  label,
  value,
  detail,
  tone = "default",
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: "default" | "green" | "amber" | "red";
}) {
  const toneClass = {
    default: "text-white",
    green: "text-emerald-200",
    amber: "text-amber-200",
    red: "text-rose-200",
  }[tone];

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.055] p-4">
      <p className="text-xs font-medium uppercase text-zinc-400">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${toneClass}`}>{value}</p>
      {detail ? <p className="mt-1 text-sm text-zinc-400">{detail}</p> : null}
    </div>
  );
}
