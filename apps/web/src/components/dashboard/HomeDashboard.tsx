"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { FlaskConical, GitBranch, Table2, Users, BarChart3 } from "lucide-react";

import { ProbabilityMoversPanel } from "@/components/analytics/ProbabilityMoversPanel";
import { UpsetRadarPanel } from "@/components/analytics/UpsetRadarPanel";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { ChampionOddsTable } from "@/components/dashboard/ChampionOddsTable";
import { StageProbabilityTable } from "@/components/dashboard/StageProbabilityTable";
import { TopWinnersCards } from "@/components/dashboard/TopWinnersCards";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import {
  fetchGroupChaos,
  fetchProbabilityMovers,
  fetchUpsetRadar,
  GroupChaosReport,
  ProbabilityMovers,
  simulateTournament,
  SimulationSummary,
  UpsetRadar,
} from "@/lib/api";
import { formatModelLabel, formatNumber, formatPercent } from "@/lib/format";

export function HomeDashboard() {
  const [summary, setSummary] = useState<SimulationSummary | null>(null);
  const [upsets, setUpsets] = useState<UpsetRadar | null>(null);
  const [groupChaos, setGroupChaos] = useState<GroupChaosReport | null>(null);
  const [movers, setMovers] = useState<ProbabilityMovers | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    Promise.all([
      simulateTournament({
        n_simulations: 1000,
        model_type: "oracle_v2",
        seed: 42,
      }),
      fetchUpsetRadar("oracle_v2", 6),
      fetchGroupChaos("oracle_v2", 500, 42),
      fetchProbabilityMovers(8),
    ])
      .then(([simulation, upsetRadar, chaos, probabilityMovers]) => {
        if (isActive) {
          setSummary(simulation);
          setUpsets(upsetRadar);
          setGroupChaos(chaos);
          setMovers(probabilityMovers);
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Simulation request failed",
          );
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  const insights = useMemo(() => {
    if (!summary || !groupChaos) {
      return null;
    }

    const teams = summary.teams;
    const championSorted = [...teams].sort((a, b) => b.champion - a.champion);
    const finalSorted = [...teams].sort((a, b) => b.final - a.final);
    const topChampion = championSorted[0];
    const secondChampion = championSorted[1];
    const mostVolatileGroup = groupChaos.groups[0];

    return {
      topChampion,
      finalistPair: `${finalSorted[0]?.team_name ?? "-"} vs ${finalSorted[1]?.team_name ?? "-"}`,
      closestTitleRace: formatPercent(
        topChampion.champion - (secondChampion?.champion ?? 0),
      ),
      mostVolatileGroup: mostVolatileGroup
        ? `${mostVolatileGroup.group_id} · ${mostVolatileGroup.chaos_label}`
        : "-",
    };
  }, [summary, groupChaos]);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!summary || !insights) {
    return <LoadingState label="Running simulation" />;
  }

  const teams = summary.teams;
  const averageQualification =
    teams.reduce(
      (total, team) => total + team.group_qualification_probability,
      0,
    ) / teams.length;

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-lg border border-white/10 bg-gradient-to-br from-white/[0.12] to-white/[0.035] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.24)]">
        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div>
            <p className="text-xs font-semibold uppercase text-[var(--turf)]">
              Tournament intelligence desk
            </p>
            <h2 className="mt-3 max-w-3xl text-4xl font-semibold tracking-normal text-white sm:text-5xl">
              {insights.topChampion.team_name} leads the current title race.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-zinc-300">
              Oracle v2 runs World Cup 2026 data through the Monte Carlo engine
              and surfaces champion odds, group volatility, upset risk, and
              data coverage in one broadcast-style desk.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <StatCard
              label="Most likely champion"
              value={insights.topChampion.team_name}
              detail={formatPercent(insights.topChampion.champion)}
              tone="green"
            />
            <StatCard
              label="Likely final pair"
              value={insights.finalistPair}
              detail={`Title gap ${insights.closestTitleRace}`}
            />
            <StatCard
              label="Most volatile group"
              value={insights.mostVolatileGroup}
              detail="Highest chaos score"
              tone="amber"
            />
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Model"
          value={formatModelLabel(summary.metadata.model_type)}
          detail={`Seed ${summary.metadata.seed ?? "none"}`}
        />
        <StatCard
          label="Simulations"
          value={formatNumber(summary.metadata.n_simulations)}
          detail="Baseline dashboard run"
        />
        <StatCard
          label="Average qualification"
          value={formatPercent(averageQualification)}
          detail="Across all teams"
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

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-white">Top contenders</h2>
          <p className="mt-1 text-sm text-zinc-400">
            The four teams with the highest champion probability.
          </p>
        </div>
        <TopWinnersCards teams={teams} />
      </section>

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

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickLinks.map((link) => {
          const Icon = link.icon;
          return (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-lg border border-white/10 bg-white/[0.05] p-4 transition hover:border-[var(--turf)]/30 hover:bg-white/[0.08]"
            >
              <Icon size={20} aria-hidden="true" className="text-[var(--turf)]" />
              <h3 className="mt-4 font-semibold text-white">{link.title}</h3>
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

const quickLinks = [
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
    description: "Track the model roadmap from Elo to Oracle v2.",
    icon: BarChart3,
  },
];
