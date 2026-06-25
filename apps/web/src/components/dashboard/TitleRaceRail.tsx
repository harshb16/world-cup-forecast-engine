import Link from "next/link";

import { TeamProbability } from "@/lib/api";
import { formatPercent } from "@/lib/format";

export function TitleRaceRail({ teams }: { teams: TeamProbability[] }) {
  const contenders = [...teams]
    .sort((a, b) => b.champion - a.champion)
    .slice(0, 8);
  const leader = contenders[0]?.champion ?? 1;

  return (
    <section aria-labelledby="title-race-heading" className="min-w-0">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-[var(--turf)]">
            Title probability board
          </p>
          <h2
            id="title-race-heading"
            className="mt-2 text-lg font-semibold text-white"
          >
            Eight teams setting the pace
          </h2>
        </div>
        <Link
          href="/teams"
          className="shrink-0 text-xs font-semibold text-zinc-400 transition hover:text-white"
        >
          All 48 teams →
        </Link>
      </div>

      <ol className="mt-5 space-y-3">
        {contenders.map((team, index) => (
          <li key={team.team_id}>
            <Link
              href={`/teams/${team.team_id}`}
              className="group grid grid-cols-[1.6rem_minmax(6rem,0.8fr)_minmax(7rem,1.4fr)_3.5rem] items-center gap-3 rounded-md px-2 py-1.5 transition hover:bg-white/[0.04]"
            >
              <span className="font-mono text-xs text-zinc-600">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="truncate text-sm font-semibold text-zinc-200 group-hover:text-white">
                {team.team_name}
              </span>
              <span className="h-1.5 overflow-hidden rounded-full bg-white/[0.07]">
                <span
                  className={`block h-full rounded-full ${
                    index === 0 ? "bg-[var(--turf)]" : "bg-[var(--var-blue)]"
                  }`}
                  style={{
                    width: `${Math.max((team.champion / leader) * 100, 3)}%`,
                  }}
                />
              </span>
              <span className="text-right font-mono text-xs font-semibold text-zinc-300">
                {formatPercent(team.champion)}
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
