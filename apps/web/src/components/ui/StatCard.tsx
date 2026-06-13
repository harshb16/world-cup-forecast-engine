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
    default: "text-[#f4f7f5]",
    green: "text-[#39ff88]",
    amber: "text-[#f6c85f]",
    red: "text-rose-200",
  }[tone];

  return (
    <div className="rounded-lg border border-white/10 bg-[#101722]/80 p-4">
      <p className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-[#93a19a]">
        {label}
      </p>
      <p className={`mt-2 text-2xl font-semibold ${toneClass}`}>{value}</p>
      {detail ? <p className="mt-1 text-sm text-[#93a19a]">{detail}</p> : null}
    </div>
  );
}
