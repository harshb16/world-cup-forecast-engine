"use client";

import { useCallback, useMemo } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BookOpenText,
  CalendarDays,
  FlaskConical,
  GitBranch,
  Table2,
  Users,
} from "lucide-react";

import { ProbabilityMoversPanel } from "@/components/analytics/ProbabilityMoversPanel";
import { UpsetRadarPanel } from "@/components/analytics/UpsetRadarPanel";
import { DataFreshness } from "@/components/DataFreshness";
import { ErrorState } from "@/components/ErrorState";
import { ForecastRefreshControl } from "@/components/ForecastRefreshControl";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { ChampionOddsTable } from "@/components/dashboard/ChampionOddsTable";
import { StageProbabilityTable } from "@/components/dashboard/StageProbabilityTable";
import { SyncResultsControl } from "@/components/SyncResultsControl";
import { TitleRaceRail } from "@/components/dashboard/TitleRaceRail";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import {
  DEFAULT_MODEL_TYPE,
  fetchLatestForecast,
  fetchProbabilityMovers,
  GroupChaosReport,
  ProbabilityMovers,
  SimulationSummary,
  UpsetRadar,
  BracketMatch,
} from "@/lib/api";
import { formatModelLabel, formatNumber, formatPercent } from "@/lib/format";
import { usePublishedForecast } from "@/hooks/usePublishedForecast";

type DashboardForecast = {
  summary: SimulationSummary;
  upsets: UpsetRadar;
  groupChaos: GroupChaosReport;
  movers: ProbabilityMovers;
  featuredFinal: BracketMatch;
};

export function HomeDashboard() {
  const loadForecast = useCallback(async (): Promise<DashboardForecast> => {
    const [snapshot, movers] = await Promise.all([
      fetchLatestForecast(),
      fetchProbabilityMovers(8),
    ]);
    return {
      summary: snapshot.summary,
      upsets: snapshot.upsets,
      groupChaos: snapshot.group_chaos,
      movers,
      featuredFinal: snapshot.featured_final,
    };
  }, []);

  const {
    data,
    error,
    isRefreshing,
    lastRunAt,
    refresh,
  } = usePublishedForecast(loadForecast);
  const summary = data?.summary ?? null;
  const upsets = data?.upsets ?? null;
  const groupChaos = data?.groupChaos ?? null;
  const movers = data?.movers ?? null;
  const featuredFinal = data?.featuredFinal ?? null;

  const featuredFinalWinner =
    featuredFinal?.winner_team_id === featuredFinal?.team_a.team_id
      ? featuredFinal.team_a
      : featuredFinal?.team_b;

  const insights = useMemo(() => {
    if (!summary || !groupChaos) {
      return null;
    }

    const teams = summary.teams;
    const championSorted = [...teams].sort((a, b) => b.champion - a.champion);
    const topChampion = championSorted[0];
    const secondChampion = championSorted[1];
    const mostVolatileGroup = groupChaos.groups[0];

    return {
      topChampion,
      closestTitleRace: formatPercent(
        topChampion.champion - (secondChampion?.champion ?? 0),
      ),
      mostVolatileGroup: mostVolatileGroup
        ? `${mostVolatileGroup.group_id} · ${mostVolatileGroup.chaos_label}`
        : "-",
    };
  }, [summary, groupChaos]);

  if (error && !summary) {
    return <ErrorState message={error} />;
  }

  if (!summary || !insights || !featuredFinal) {
    return <LoadingState label="Loading forecast" />;
  }

  const teams = summary.teams;
  const titleConcentration = [...teams]
    .sort((a, b) => b.champion - a.champion)
    .slice(0, 8)
    .reduce((total, team) => total + team.champion, 0);
  const highestUpset = upsets?.fixtures[0] ?? null;

  return (
    <div className="space-y-8 pb-12">
      <section className="relative overflow-hidden rounded-xl border border-white/10 bg-[#080d13] shadow-[0_28px_90px_rgba(0,0,0,0.3)]">
        <div
          className="pointer-events-none absolute inset-y-0 right-0 w-1/2 opacity-30"
          aria-hidden="true"
          style={{
            background:
              "repeating-linear-gradient(115deg,transparent 0 26px,rgba(75,141,255,.15) 26px 27px)",
          }}
        />
        <div className="relative grid xl:grid-cols-[minmax(0,1.05fr)_minmax(24rem,0.95fr)]">
          <div className="flex flex-col justify-between border-b border-white/10 p-6 sm:p-8 xl:min-h-[34rem] xl:border-b-0 xl:border-r">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded-full border border-[var(--turf)]/30 bg-[var(--turf)]/10 px-3 py-1 font-mono text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-[var(--turf)]">
                  Forecast snapshot
                </span>
                <DataFreshness
                  timestamp={summary.metadata.last_updated}
                  compact
                />
              </div>
              <div className="mt-4">
                <div className="flex flex-wrap items-start gap-3">
                  <SyncResultsControl onSynced={refresh} />
                  <ForecastRefreshControl
                    isRefreshing={isRefreshing}
                    lastRunAt={lastRunAt}
                    onRefresh={refresh}
                  />
                </div>
              </div>
              <p className="mt-8 font-mono text-xs uppercase tracking-[0.16em] text-zinc-500">
                Current title leader
              </p>
              <h2 className="mt-3 max-w-3xl text-5xl font-semibold leading-[0.95] tracking-[-0.055em] text-white sm:text-7xl">
                {insights.topChampion.team_name}
              </h2>
              <div className="mt-5 flex items-end gap-4">
                <p className="font-mono text-4xl font-semibold text-[var(--turf)] sm:text-5xl">
                  {formatPercent(insights.topChampion.champion)}
                </p>
                <p className="max-w-xs pb-1 text-sm leading-5 text-zinc-400">
                  wins tournament across{" "}
                  {formatNumber(summary.metadata.n_simulations)} seeded paths
                </p>
              </div>
              <p className="mt-7 max-w-2xl text-base leading-7 text-zinc-300">
                One screen for title pressure, dangerous fixtures, volatile
                groups, and probability movement. Powered by{" "}
                {formatModelLabel(DEFAULT_MODEL_TYPE)}.
              </p>
            </div>

            <div className="mt-10 flex flex-wrap gap-3">
              <Link
                href="/matchday"
                className="inline-flex items-center gap-2 rounded-md bg-[var(--turf)] px-4 py-2.5 text-sm font-semibold text-[var(--primary-foreground)] transition hover:brightness-110"
              >
                Open matchday <ArrowRight size={16} aria-hidden="true" />
              </Link>
              <Link
                href="/what-if"
                className="inline-flex items-center gap-2 rounded-md border border-white/15 bg-white/[0.04] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/[0.08]"
              >
                Run scenario
              </Link>
            </div>
          </div>
          <div className="relative p-6 sm:p-8">
            <TitleRaceRail teams={teams} />
          </div>
        </div>

        <div className="relative grid border-t border-white/10 sm:grid-cols-2 xl:grid-cols-4">
          <Signal
            label="Featured final"
            value={`${featuredFinal.team_a.team_name} vs ${featuredFinal.team_b.team_name}`}
            detail={`Favorite-path winner ${featuredFinalWinner?.team_name ?? "-"} · ${formatPercent(
              featuredFinal.winner_team_id === featuredFinal.team_a.team_id
                ? featuredFinal.probabilities.team_a_advance
                : featuredFinal.probabilities.team_b_advance,
            )}`}
          />
          <Signal
            label="Title concentration"
            value={formatPercent(titleConcentration)}
            detail="Held by top eight teams"
          />
          <Signal
            label="Chaos watch"
            value={insights.mostVolatileGroup}
            detail="Most unsettled group"
            tone="amber"
          />
          <Signal
            label="Upset watch"
            value={
              highestUpset
                ? `${highestUpset.team_a_name}–${highestUpset.team_b_name}`
                : "No fixture"
            }
            detail={
              highestUpset
                ? `${highestUpset.risk_label} risk`
                : "No risk signal"
            }
            tone="blue"
          />
        </div>
      </section>

      {error ? (
        <p
          role="status"
          className="rounded-md border border-[var(--risk-red)]/25 bg-[var(--risk-red)]/10 px-4 py-3 text-sm text-red-200"
        >
          Latest refresh failed. Showing previous forecast. {error}
        </p>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Model"
          value={formatModelLabel(summary.metadata.model_type)}
          detail="Current baseline · validation pending"
        />
        <StatCard
          label="Known results"
          value={formatNumber(summary.metadata.completed_result_count)}
          detail="Locked into every run"
        />
        <StatCard
          label="Data coverage"
          value={`${summary.metadata.rating_coverage_count}/${summary.metadata.team_count}`}
          detail="Teams with ratings"
          tone="amber"
        />
      </div>

      {movers ? <ProbabilityMoversPanel movers={movers} /> : null}

      <SectionCard>
        <h2 className="text-base font-semibold text-white">Data status</h2>
        <div className="mt-3">
          <DataStatusCard metadata={summary.metadata} />
        </div>
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-2">
        {upsets ? <UpsetRadarPanel fixtures={upsets.fixtures} /> : null}
        {groupChaos ? (
          <SectionCard>
            <p className="text-xs font-semibold uppercase text-[var(--score-amber)]">
              Group chaos board
            </p>
            <h2 className="mt-1 text-lg font-semibold text-white">
              Most unsettled groups
            </h2>
            <div className="mt-5 space-y-3">
              {groupChaos.groups.slice(0, 6).map((group) => (
                <div
                  key={group.group_id}
                  className="rounded-md border border-white/10 bg-black/20 p-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-white">
                        {group.group_name}
                      </p>
                      <p className="text-xs text-zinc-500">
                        Key swing: {group.key_swing_match_label ?? "TBD"}
                      </p>
                    </div>
                    <span className="text-sm font-semibold text-[var(--score-amber)]">
                      {group.chaos_label} · {formatPercent(group.chaos_score, 0)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        ) : null}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_1fr]">
        <ChampionOddsTable teams={teams} />
        <StageProbabilityTable teams={teams} />
      </div>

      <SectionCard>
        <h2 className="text-base font-semibold text-white">How to read this</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <HelpText>
            Champion odds mean the share of simulations where a team wins the
            whole tournament.
          </HelpText>
          <HelpText>
            Upset radar highlights fixtures where the underdog still has a
            credible advance path.
          </HelpText>
          <HelpText>
            Group chaos scores rise when qualification odds are bunched and
            projected points are tight.
          </HelpText>
        </div>
      </SectionCard>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {quickLinks.map((link) => {
          const Icon = link.icon;
          return (
            <Link
              key={link.href}
              href={link.href}
              className="group rounded-lg border border-white/10 bg-card p-5 transition hover:-translate-y-0.5 hover:border-[var(--turf)]/30 hover:bg-white/[0.06]"
            >
              <div className="flex items-center justify-between">
                <Icon
                  size={20}
                  aria-hidden="true"
                  className="text-[var(--turf)]"
                />
                <ArrowRight
                  size={16}
                  className="text-zinc-600 transition group-hover:translate-x-1 group-hover:text-white"
                  aria-hidden="true"
                />
              </div>
              <h3 className="mt-5 font-semibold text-white">{link.title}</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                {link.description}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function Signal({
  label,
  value,
  detail,
  tone = "green",
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "green" | "amber" | "blue";
}) {
  const toneClass =
    tone === "amber"
      ? "text-[var(--score-amber)]"
      : tone === "blue"
        ? "text-[var(--var-blue)]"
        : "text-[var(--turf)]";

  return (
    <div className="border-b border-white/10 p-5 last:border-b-0 sm:border-b-0 sm:border-r sm:nth-[2n]:border-r-0 xl:nth-[2n]:border-r xl:last:border-r-0">
      <p className="font-mono text-[0.68rem] uppercase tracking-[0.13em] text-zinc-500">
        {label}
      </p>
      <p className={`mt-2 truncate text-lg font-semibold ${toneClass}`}>
        {value}
      </p>
      <p className="mt-1 text-xs text-zinc-500">{detail}</p>
    </div>
  );
}

const quickLinks = [
  {
    href: "/matchday",
    title: "Matchday",
    description: "Read current fixtures, model probabilities, and results.",
    icon: CalendarDays,
  },
  {
    href: "/bracket",
    title: "Bracket",
    description: "Reveal a seeded knockout path from Round of 32 to champion.",
    icon: GitBranch,
  },
  {
    href: "/groups",
    title: "Groups",
    description: "See qualification races, average points, and group volatility.",
    icon: Table2,
  },
  {
    href: "/what-if",
    title: "What-if Lab",
    description: "Override match scores and compare probability movement.",
    icon: FlaskConical,
  },
  {
    href: "/teams",
    title: "Teams",
    description: "Open team profiles with rating and stage probability ladders.",
    icon: Users,
  },
  {
    href: "/models",
    title: "Models",
    description: "Review baseline and experimental models.",
    icon: BarChart3,
  },
  {
    href: "/methodology",
    title: "Methodology",
    description: "Trace data, ratings, simulation, evaluation, and limits.",
    icon: BookOpenText,
  },
];
