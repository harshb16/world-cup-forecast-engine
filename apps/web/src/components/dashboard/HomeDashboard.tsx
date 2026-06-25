"use client";

import { useCallback, useMemo } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

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
import { MotionBorderBeam } from "@/components/ui/MotionBorderBeam";
import { Button } from "@/components/ui/button";
import { HelpText } from "@/components/ui/HelpText";
import { NumberTicker } from "@/components/ui/number-ticker";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { cn } from "@/lib/utils";

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
    featuredFinal === null
      ? null
      : featuredFinal.winner_team_id === featuredFinal.team_a.team_id
        ? featuredFinal.team_a
        : featuredFinal.team_b;

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
  const championPercent = insights.topChampion.champion * 100;

  return (
    <div className="flex flex-col gap-8 pb-12">
      <section className="surface-hero relative overflow-hidden rounded-xl border border-border/80">
        <div
          className="pointer-events-none absolute inset-y-0 right-0 w-1/2 opacity-40"
          aria-hidden="true"
          style={{
            background:
              "repeating-linear-gradient(115deg,transparent 0 24px,color-mix(in oklch,var(--chart-2) 18%,transparent) 24px 25px)",
          }}
        />
        <div className="relative grid xl:grid-cols-[minmax(0,1.05fr)_minmax(20rem,0.95fr)]">
          <div className="flex flex-col justify-between border-b border-border p-6 sm:p-7 xl:border-b-0 xl:border-r">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 font-mono text-[0.68rem] font-semibold uppercase tracking-widest text-primary">
                  Forecast snapshot
                </span>
                <DataFreshness
                  timestamp={summary.metadata.last_updated}
                  compact
                />
              </div>
              <div className="mt-4 flex flex-wrap items-start gap-3">
                <SyncResultsControl onSynced={refresh} />
                <ForecastRefreshControl
                  isRefreshing={isRefreshing}
                  lastRunAt={lastRunAt}
                  onRefresh={refresh}
                />
              </div>
              <p className="mt-6 font-mono text-xs uppercase tracking-widest text-muted-foreground">
                Current title leader
              </p>
              <h2 className="font-display mt-3 max-w-3xl text-4xl font-semibold leading-tight tracking-tight text-foreground sm:text-5xl">
                {insights.topChampion.team_name}
              </h2>
              <div className="mt-4 flex items-end gap-2">
                <p className="text-data-lg text-primary">
                  <NumberTicker
                    value={championPercent}
                    decimalPlaces={1}
                    className="text-primary"
                  />
                  %
                </p>
                <p className="max-w-xs pb-1 text-sm leading-5 text-muted-foreground">
                  across {formatNumber(summary.metadata.n_simulations)} paths
                </p>
              </div>
              <p className="mt-5 max-w-2xl text-sm leading-6 text-muted-foreground">
                Title pressure, dangerous fixtures, and group volatility in one
                desk. Powered by {formatModelLabel(DEFAULT_MODEL_TYPE)}.
              </p>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button render={<Link href="/matchday" />} size="lg">
                Open matchday
                <ArrowRight data-icon="inline-end" aria-hidden="true" />
              </Button>
              <Button render={<Link href="/what-if" />} variant="outline" size="lg">
                Run scenario
              </Button>
            </div>
          </div>
          <div className="relative p-6 sm:p-7">
            <TitleRaceRail teams={teams} />
          </div>
        </div>

        <div className="relative grid border-t border-border sm:grid-cols-2 xl:grid-cols-4">
          <div className="relative overflow-hidden border-b border-border sm:border-b-0 sm:border-r xl:nth-[2n]:border-r-0">
            <MotionBorderBeam
              size={80}
              duration={8}
              colorFrom="var(--primary)"
              colorTo="var(--chart-3)"
              borderWidth={1}
            />
            <Signal
              label="Featured final"
              value={`${featuredFinal.team_a.team_name} vs ${featuredFinal.team_b.team_name}`}
              detail={`Favorite-path winner ${featuredFinalWinner?.team_name ?? "-"} · ${formatPercent(
                featuredFinal.winner_team_id === featuredFinal.team_a.team_id
                  ? featuredFinal.probabilities.team_a_advance
                  : featuredFinal.probabilities.team_b_advance,
              )}`}
            />
          </div>
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
          className="rounded-md border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive-foreground"
        >
          Latest refresh failed. Showing previous forecast. {error}
        </p>
      ) : null}

      <Tabs defaultValue="overview">
        <TabsList className="h-10 w-full justify-start bg-secondary/80 p-1 sm:w-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="movers">Movers & risk</TabsTrigger>
          <TabsTrigger value="tables">Tables</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="flex flex-col gap-8 pt-2">
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
          <SectionCard title="Data status">
            <DataStatusCard metadata={summary.metadata} />
          </SectionCard>
        </TabsContent>

        <TabsContent value="movers" className="flex flex-col gap-8 pt-2">
          {movers ? <ProbabilityMoversPanel movers={movers} /> : null}
          <div className="grid gap-6 xl:grid-cols-2">
            {upsets ? <UpsetRadarPanel fixtures={upsets.fixtures} /> : null}
            {groupChaos ? (
              <SectionCard
                title="Most unsettled groups"
                description="Groups where qualification odds are bunched"
              >
                <div className="flex flex-col gap-3">
                  {groupChaos.groups.slice(0, 6).map((group) => (
                    <div
                      key={group.group_id}
                      className="rounded-md border border-border bg-muted/40 p-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-semibold text-foreground">
                            {group.group_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Key swing: {group.key_swing_match_label ?? "TBD"}
                          </p>
                        </div>
                        <span className="text-sm font-semibold text-signal-amber">
                          {group.chaos_label} ·{" "}
                          {formatPercent(group.chaos_score, 0)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </SectionCard>
            ) : null}
          </div>
        </TabsContent>

        <TabsContent value="tables" className="flex flex-col gap-8 pt-2">
          <div className="grid gap-6 xl:grid-cols-[1.1fr_1fr]">
            <ChampionOddsTable teams={teams} />
            <StageProbabilityTable teams={teams} />
          </div>
          <SectionCard title="How to read this">
            <div className="grid gap-3 md:grid-cols-3">
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
        </TabsContent>
      </Tabs>
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
      ? "text-signal-amber"
      : tone === "blue"
        ? "text-signal-blue"
        : "text-primary";

  return (
    <div className="border-b border-border p-5 last:border-b-0 sm:border-b-0 sm:border-r sm:nth-[2n]:border-r-0 xl:nth-[2n]:border-r xl:last:border-r-0">
      <p className="font-mono text-[0.68rem] uppercase tracking-widest text-muted-foreground">
        {label}
      </p>
      <p className={cn("mt-2 truncate text-lg font-semibold", toneClass)}>
        {value}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}
