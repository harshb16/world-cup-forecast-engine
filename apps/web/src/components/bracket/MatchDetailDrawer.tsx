"use client";

import Link from "next/link";
import { X } from "lucide-react";

import { HeadToHeadPanel } from "@/components/teams/HeadToHeadPanel";
import { Button } from "@/components/ui/button";
import type { BracketMatch } from "@/lib/api";
import { buildWhatIfUrl, favoriteWinsOverride, upsetOverride } from "@/lib/scenario-overrides";
import { formatNumber, formatPercent } from "@/lib/format";

import { formatExpectedGoals } from "./utils";

export function MatchDetailDrawer({
  match,
  onClose,
}: {
  match: BracketMatch;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 sm:items-center">
      <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-xl border border-border bg-card p-5 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-eyebrow">
              {match.stage} · {match.id}
            </p>
            <h2 className="mt-1 text-xl font-semibold text-foreground">
              {match.team_a.team_name} vs {match.team_b.team_name}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-border p-2 text-muted-foreground hover:bg-accent/60"
            aria-label="Close match details"
          >
            <X aria-hidden="true" />
          </button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <DetailMetric
            label="Team A advance"
            value={formatPercent(match.probabilities.team_a_advance)}
          />
          <DetailMetric
            label="Team B advance"
            value={formatPercent(match.probabilities.team_b_advance)}
          />
          <DetailMetric
            label="Expected goals"
            value={`${formatExpectedGoals(match.team_a_expected_goals)} - ${formatExpectedGoals(match.team_b_expected_goals)}`}
          />
          <DetailMetric
            label="Confidence"
            value={match.confidence_label ?? "Projection"}
          />
        </div>

        {match.drivers.length > 0 ? (
          <div className="mt-5">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground">
              Model drivers
            </h3>
            <ul className="mt-2 flex flex-col gap-2 text-sm leading-6 text-muted-foreground">
              {match.drivers.map((driver) => (
                <li key={driver}>• {driver}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="mt-5 rounded-lg border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
          Ratings: {match.team_a.team_name} {formatNumber(match.team_a.rating)} ·{" "}
          {match.team_b.team_name} {formatNumber(match.team_b.rating)}
        </div>

        <HeadToHeadPanel
          teamAId={match.team_a.team_id}
          teamBId={match.team_b.team_id}
        />

        <div className="mt-3">
          <Link
            href={`/teams/compare?a=${match.team_a.team_id}&b=${match.team_b.team_id}`}
            className="text-sm font-semibold text-primary"
          >
            Compare teams
          </Link>
        </div>

        {!match.result_is_real ? (
          <div className="mt-5 flex flex-wrap gap-2">
            <Button
              render={<Link href={buildWhatIfUrl([upsetOverride(match)])} />}
              variant="outline"
              size="sm"
            >
              Simulate upset
            </Button>
            <Button
              render={<Link href={buildWhatIfUrl([favoriteWinsOverride(match)])} />}
              variant="outline"
              size="sm"
            >
              Favorite wins
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function DetailMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-accent/50 px-3 py-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 font-semibold text-foreground">{value}</p>
    </div>
  );
}
