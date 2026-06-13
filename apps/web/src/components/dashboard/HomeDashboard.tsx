"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FlaskConical, Table2, Users, BarChart3, GitBranch } from "lucide-react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { ChampionOddsTable } from "@/components/dashboard/ChampionOddsTable";
import { StageProbabilityTable } from "@/components/dashboard/StageProbabilityTable";
import { TopWinnersCards } from "@/components/dashboard/TopWinnersCards";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import { formatNumber, formatPercent } from "@/lib/format";
import { simulateTournament, SimulationSummary } from "@/lib/api";

export function HomeDashboard() {
  const [summary, setSummary] = useState<SimulationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    simulateTournament({
      n_simulations: 1000,
      model_type: "poisson",
      seed: 42,
    })
      .then((data) => {
        if (isActive) {
          setSummary(data);
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

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!summary) {
    return <LoadingState label="Running simulation" />;
  }

  const teams = summary.teams;
  const topChampion = [...teams].sort((a, b) => b.champion - a.champion)[0];
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
            <p className="text-xs font-semibold uppercase text-emerald-200">
              Live simulation dashboard
            </p>
            <h2 className="mt-3 max-w-3xl text-4xl font-semibold tracking-normal text-white sm:text-5xl">
              {topChampion.team_name} leads the current title race.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-zinc-300">
              This view runs World Cup 2026 data through the backend Monte Carlo
              engine and turns the results into probabilities normal fans can scan.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <StatCard
              label="Most likely champion"
              value={topChampion.team_name}
              detail={formatPercent(topChampion.champion)}
              tone="green"
            />
            <StatCard
              label="Simulation run"
              value={formatNumber(summary.metadata.n_simulations)}
              detail={`${summary.metadata.model_type.toUpperCase()} model · seed ${
                summary.metadata.seed ?? "none"
              }`}
            />
            <StatCard
              label="Data status"
              value={summary.metadata.is_real_data ? "Real" : "Sample"}
              detail={summary.metadata.data_version ?? "No version"}
              tone="amber"
            />
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Average qualification"
          value={formatPercent(averageQualification)}
          detail="Across all teams"
          tone="amber"
        />
        <StatCard
          label="Teams simulated"
          value={formatNumber(teams.length)}
          detail="48-team World Cup format"
        />
        <StatCard
          label="Overrides applied"
          value={formatNumber(summary.metadata.overrides_applied.length)}
          detail="Baseline run"
        />
      </div>

      <section className="space-y-4">
        <DataStatusCard metadata={summary.metadata} />
      </section>

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
            Stage probabilities show how often a team reaches that round or
            later in the simulated bracket.
          </HelpText>
          <HelpText>
            Small gaps should be treated as directional, because Monte Carlo
            runs include normal sampling noise.
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
              className="rounded-lg border border-white/10 bg-white/[0.05] p-4 transition hover:border-emerald-300/30 hover:bg-white/[0.08]"
            >
              <Icon size={20} aria-hidden="true" className="text-emerald-200" />
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
    description: "Track the model roadmap from Elo to ensembles.",
    icon: BarChart3,
  },
];
