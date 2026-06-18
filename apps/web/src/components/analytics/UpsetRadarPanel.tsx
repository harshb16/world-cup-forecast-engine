import { SectionCard } from "@/components/ui/SectionCard";
import { UpsetFixture } from "@/lib/api";
import { formatPercent } from "@/lib/format";

export function UpsetRadarPanel({ fixtures }: { fixtures: UpsetFixture[] }) {
  return (
    <SectionCard>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-[var(--score-amber)]">
            Upset radar
          </p>
          <h2 className="mt-1 text-lg font-semibold text-white">
            Danger fixtures
          </h2>
          <p className="mt-1 text-sm text-zinc-400">
            Ranked by upset score from advance probability gaps and stage
            importance.
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {fixtures.map((fixture) => (
          <article
            key={`${fixture.match_id}-${fixture.stage}`}
            className="rounded-md border border-white/10 bg-black/20 p-4"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase text-zinc-500">
                  {fixture.stage}
                  {fixture.group_id ? ` · ${fixture.group_id}` : ""}
                </p>
                <h3 className="mt-1 font-semibold text-white">
                  {fixture.team_a_name} vs {fixture.team_b_name}
                </h3>
              </div>
              <RiskBadge label={fixture.risk_label} />
            </div>

            <div className="mt-3 grid gap-2 text-xs text-zinc-400 sm:grid-cols-3">
              <Metric
                label="Underdog advance"
                value={formatPercent(fixture.underdog_advance_probability)}
              />
              <Metric
                label="Favorite edge"
                value={formatPercent(fixture.advance_probability_gap)}
              />
              <Metric
                label="Upset score"
                value={formatPercent(fixture.upset_score, 0)}
              />
            </div>

            <ul className="mt-3 space-y-1 text-sm leading-6 text-zinc-300">
              {fixture.reasons.map((reason) => (
                <li key={reason}>• {reason}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </SectionCard>
  );
}

function RiskBadge({ label }: { label: string }) {
  const tone =
    label === "High"
      ? "border-[var(--risk-red)]/40 bg-[var(--risk-red)]/10 text-[var(--risk-red)]"
      : label === "Elevated"
        ? "border-[var(--score-amber)]/40 bg-[var(--score-amber)]/10 text-[var(--score-amber)]"
        : "border-[var(--var-blue)]/40 bg-[var(--var-blue)]/10 text-[var(--var-blue)]";

  return (
    <span
      className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${tone}`}
    >
      {label}
    </span>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-white/[0.04] px-3 py-2">
      <span className="block text-zinc-500">{label}</span>
      <span className="font-semibold text-zinc-100">{value}</span>
    </div>
  );
}
