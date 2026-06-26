import Link from "next/link";

import { TeamProbability } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

export function TitleRaceRail({ teams }: { teams: TeamProbability[] }) {
  const contenders = [...teams]
    .sort((a, b) => b.champion - a.champion)
    .slice(0, 8);
  const leader = contenders[0]?.champion ?? 1;

  return (
    <section aria-labelledby="title-race-heading" className="min-w-0">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-eyebrow">Title probability board</p>
          <h2
            id="title-race-heading"
            className="mt-2 text-lg font-semibold text-foreground"
          >
            Eight teams setting the pace
          </h2>
        </div>
        <Link
          href="/teams"
          className="shrink-0 text-xs font-semibold text-muted-foreground transition hover:text-primary"
        >
          All 48 teams →
        </Link>
      </div>

      <ol className="mt-5 flex flex-col gap-3">
        {contenders.map((team, index) => (
          <li key={team.team_id}>
            <Link
              href={`/teams/${team.team_id}`}
              className="group grid grid-cols-[1.6rem_minmax(6rem,0.8fr)_minmax(7rem,1.4fr)_3.5rem] items-center gap-3 rounded-md px-2 py-1.5 transition hover:bg-accent/50"
            >
              <span className="font-mono text-xs text-muted-foreground">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="truncate text-sm font-semibold text-foreground group-hover:text-primary">
                {team.team_name}
              </span>
              <span className="h-1.5 overflow-hidden rounded-full bg-muted/60">
                <span
                  className={cn(
                    "block h-full rounded-full",
                    index === 0 ? "bg-chart-3" : "bg-primary/75",
                  )}
                  style={{
                    width: `${Math.max((team.champion / leader) * 100, 3)}%`,
                  }}
                />
              </span>
              <span className="text-right font-mono text-xs font-semibold tabular-nums text-muted-foreground">
                {formatPercent(team.champion)}
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
