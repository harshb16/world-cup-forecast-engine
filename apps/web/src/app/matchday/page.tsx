"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/PageHeader";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import {
  fetchMatchday,
  type MatchdayData,
  type MatchdayFixture,
  type MatchdayGroup,
} from "@/lib/api";
import { formatPercent } from "@/lib/format";

export default function MatchdayPage() {
  const [data, setData] = useState<MatchdayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMatchday()
      .then(setData)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Failed to load matchday data"),
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <PageHeader
        eyebrow={data?.matchday_label ?? "Matchday"}
        title={data ? `${data.matchday_label} — ${formatDate(data.date)}` : "Today's Matches"}
        description="Live group standings, today's fixtures, and model probabilities."
      />
      {loading && <LoadingState label="Loading matchday data" />}
      {error && <ErrorState message={error} />}
      {data && (
        <div className="space-y-10">
          <FixturesSection fixtures={data.fixtures} />
          <GroupStandingsSection groups={data.groups} />
        </div>
      )}
    </>
  );
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr + "T00:00:00Z").toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      timeZone: "UTC",
    });
  } catch {
    return dateStr;
  }
}

function formatKickoff(kickoffUtc: string | null): string {
  if (!kickoffUtc) return "TBD";
  try {
    return new Date(kickoffUtc).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    return kickoffUtc;
  }
}

function StatusBadge({ status }: { status: string }) {
  const lower = status.toLowerCase();

  if (lower === "finished") {
    return <Badge variant="secondary">Finished</Badge>;
  }
  if (lower === "live" || lower === "in_progress") {
    return <Badge variant="destructive">Live</Badge>;
  }
  return <Badge variant="outline">Upcoming</Badge>;
}

function ProbBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-5 shrink-0 text-right text-xs text-muted-foreground">{label}</span>
      <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-muted/50">
        <div
          className={`absolute left-0 top-0 h-full rounded-full ${color}`}
          style={{ width: `${value * 100}%` }}
        />
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-xs text-muted-foreground">
        {formatPercent(value)}
      </span>
    </div>
  );
}

function FixtureCard({ fixture }: { fixture: MatchdayFixture }) {
  const isFinished = fixture.status.toLowerCase() === "finished";

  return (
    <div
      className={`rounded-xl border bg-secondary p-4 transition ${
        fixture.what_still_matters
          ? "border-amber-500/30"
          : "border-border"
      }`}
    >
      {/* Header row */}
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {fixture.group_id && (
            <span className="rounded bg-muted/50 px-1.5 py-0.5 font-mono text-xs text-muted-foreground">
              Group {fixture.group_id}
            </span>
          )}
          {fixture.what_still_matters && (
            <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-semibold text-amber-300">
              Still matters
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={fixture.status} />
          <span className="text-xs text-muted-foreground">{formatKickoff(fixture.kickoff_utc)}</span>
        </div>
      </div>

      {/* Teams + score */}
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex-1">
          <p className="truncate text-sm font-semibold text-foreground">{fixture.team_a_name}</p>
        </div>
        <div className="shrink-0 text-center">
          {isFinished ? (
            <span className="font-mono text-xl font-bold text-foreground">
              {fixture.team_a_goals} – {fixture.team_b_goals}
            </span>
          ) : (
            <span className="font-mono text-sm text-muted-foreground">
              {fixture.projected_team_a_goals} – {fixture.projected_team_b_goals}
              <span className="ml-1 text-xs text-muted-foreground">xG</span>
            </span>
          )}
        </div>
        <div className="flex-1 text-right">
          <p className="truncate text-sm font-semibold text-foreground">{fixture.team_b_name}</p>
        </div>
      </div>

      {/* Probability bars */}
      {!isFinished && (
        <div className="space-y-1.5">
          <ProbBar label="W" value={fixture.team_a_win_probability} color="bg-primary" />
          <ProbBar label="D" value={fixture.draw_probability} color="bg-zinc-500" />
          <ProbBar label="W" value={fixture.team_b_win_probability} color="bg-blue-500" />
        </div>
      )}
    </div>
  );
}

function FixturesSection({ fixtures }: { fixtures: MatchdayFixture[] }) {
  if (fixtures.length === 0) {
    return (
      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Fixtures
        </h2>
        <p className="text-sm text-muted-foreground">No upcoming fixtures found for today.</p>
      </section>
    );
  }

  return (
    <section>
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        Fixtures
      </h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {fixtures.map((f) => (
          <FixtureCard key={f.match_id} fixture={f} />
        ))}
      </div>
    </section>
  );
}

function GroupStandingTable({ group }: { group: MatchdayGroup }) {
  return (
    <div className="rounded-xl border border-border bg-secondary overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <h3 className="text-sm font-semibold text-foreground">{group.group_name}</h3>
        {group.is_complete && (
          <span className="rounded-full bg-emerald-900/40 px-2 py-0.5 text-xs font-semibold text-primary">
            Complete
          </span>
        )}
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/5 text-muted-foreground">
            <th className="py-1.5 pl-4 text-left font-medium">#</th>
            <th className="py-1.5 text-left font-medium">Team</th>
            <th className="py-1.5 text-center font-medium">P</th>
            <th className="py-1.5 text-center font-medium">W</th>
            <th className="py-1.5 text-center font-medium">D</th>
            <th className="py-1.5 text-center font-medium">L</th>
            <th className="py-1.5 text-center font-medium">GD</th>
            <th className="py-1.5 pr-4 text-center font-medium">Pts</th>
          </tr>
        </thead>
        <tbody>
          {group.standings.map((row, idx) => (
            <tr
              key={row.team_id}
              className={`border-b border-white/5 last:border-0 ${
                idx < 2 ? "text-foreground" : "text-muted-foreground"
              }`}
            >
              <td className="py-1.5 pl-4 font-mono text-muted-foreground">{row.position}</td>
              <td className="py-1.5 font-medium">{row.team_name}</td>
              <td className="py-1.5 text-center font-mono">{row.played}</td>
              <td className="py-1.5 text-center font-mono">{row.wins}</td>
              <td className="py-1.5 text-center font-mono">{row.draws}</td>
              <td className="py-1.5 text-center font-mono">{row.losses}</td>
              <td className="py-1.5 text-center font-mono">
                {row.goal_difference > 0 ? "+" : ""}
                {row.goal_difference}
              </td>
              <td className="py-1.5 pr-4 text-center font-mono font-bold text-primary">
                {row.points}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GroupStandingsSection({ groups }: { groups: MatchdayGroup[] }) {
  return (
    <section>
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        Group Standings
      </h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {groups.map((g) => (
          <GroupStandingTable key={g.group_id} group={g} />
        ))}
      </div>
    </section>
  );
}
