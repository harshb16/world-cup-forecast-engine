"use client";

import Link from "next/link";
import { ArrowRight, Clock3 } from "lucide-react";

import { ProbabilityMoversPanel } from "@/components/analytics/ProbabilityMoversPanel";
import { ProbabilityTimeline } from "@/components/analytics/ProbabilityTimeline";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import { formatNumber, formatPercent } from "@/lib/format";
import { useTimeMachine } from "./TimeMachineProvider";

export function ReplayLanding() {
  const { snapshot, loading, error, hrefFor } = useTimeMachine();
  if (error) return <ErrorState message={error} />;
  if (loading || !snapshot) return <LoadingState label="Loading reconstructed milestone" />;

  const leader = [...snapshot.forecast.summary.teams].sort(
    (a, b) => b.champion - a.champion,
  )[0];
  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        eyebrow="Tournament time machine"
        title={snapshot.milestone.label}
        description="Move through nine major tournament checkpoints and open the forecast exactly as reconstructed at that point."
      />
      <p className="rounded-lg border border-primary/25 bg-primary/10 px-4 py-3 text-sm font-medium text-foreground">
        Reconstructed with the frozen archive model; not the original published forecast.
      </p>
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Known results" value={formatNumber(snapshot.milestone.known_result_count)} detail="Locked into this replay" />
        <StatCard label="Forecast leader" value={leader.team_name} detail={`${formatPercent(leader.champion)} champion chance`} tone="green" />
        <StatCard label="Simulation paths" value={formatNumber(snapshot.provenance.simulation_count)} detail={`Seed ${snapshot.provenance.seed}`} tone="amber" />
      </div>
      <SectionCard title="Open this moment" description="The selected milestone follows you across every supported surface.">
        <div className="flex flex-wrap gap-3">
          {[ ["/", "Dashboard"], ["/groups", "Groups"], ["/bracket", "Bracket"], ["/teams", "Teams"] ].map(([href, label]) => (
            <Link key={href} href={hrefFor(href)} className={buttonVariants({ variant: "outline" })}>
              {label}<ArrowRight data-icon="inline-end" />
            </Link>
          ))}
        </div>
      </SectionCard>
      <SectionCard title="Champion-probability arc" description="Each point comes from a precomputed milestone bank.">
        <ProbabilityTimeline showScrubber={false} />
      </SectionCard>
      <ProbabilityMoversPanel movers={snapshot.movers} />
      <p className="flex items-center gap-2 text-xs text-muted-foreground">
        <Clock3 className="size-4" /> Generated from {snapshot.provenance.data_version} with {snapshot.provenance.model_version}.
      </p>
    </div>
  );
}
