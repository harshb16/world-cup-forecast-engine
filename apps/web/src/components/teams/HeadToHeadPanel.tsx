"use client";

import { useEffect, useState } from "react";

import { DEFAULT_MODEL_TYPE, fetchHeadToHead, fetchTimeMachineHeadToHead, type HeadToHead } from "@/lib/api";
import { formatModelLabel, formatNumber, formatPercent } from "@/lib/format";
import { useTimeMachine } from "@/components/time-machine/TimeMachineProvider";

export function HeadToHeadPanel({
  teamAId,
  teamBId,
  title = "Tournament meeting odds",
}: {
  teamAId: string;
  teamBId: string;
  title?: string;
}) {
  const replay = useTimeMachine();
  const [data, setData] = useState<HeadToHead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isActive = true;
    setLoading(true);
    setError(null);
    const request = replay.isReplay && replay.milestoneId
      ? fetchTimeMachineHeadToHead(replay.milestoneId, teamAId, teamBId)
      : fetchHeadToHead(teamAId, teamBId, DEFAULT_MODEL_TYPE);
    request
      .then((response) => {
        if (isActive) {
          setData(response);
        }
      })
      .catch((caught: unknown) => {
        if (isActive) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Head-to-head request failed",
          );
        }
      })
      .finally(() => {
        if (isActive) {
          setLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [replay.isReplay, replay.milestoneId, teamAId, teamBId]);

  if (loading) {
    return (
      <div className="mt-5 rounded-lg border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
        Loading meeting probabilities…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mt-5 rounded-lg border border-destructive/25 bg-destructive/10 p-3 text-sm text-destructive-foreground">
        {error ?? "Meeting probabilities unavailable."}
      </div>
    );
  }

  return (
    <div className="mt-5 rounded-lg border border-border bg-muted/40 p-4">
      <h3 className="text-xs font-semibold uppercase text-muted-foreground">
        {title}
      </h3>
      <p className="mt-2 text-sm text-foreground">
        {data.team_a_name} and {data.team_b_name} meet in{" "}
        <span className="font-semibold">{formatPercent(data.probability)}</span>{" "}
        of {formatNumber(data.n_simulations)} simulations.
      </p>
      <div className="mt-3 grid gap-2 text-xs sm:grid-cols-3">
        <Metric
          label="Before final"
          value={formatPercent(data.meet_before_final_probability)}
        />
        <Metric
          label="Semi-final"
          value={formatPercent(data.meet_in_semi_final_probability)}
        />
        <Metric
          label="Final"
          value={formatPercent(data.meet_in_final_probability)}
        />
      </div>
      {data.stages_they_could_meet.length > 0 ? (
        <p className="mt-3 text-xs text-muted-foreground">
          Possible rounds: {data.stages_they_could_meet.join(", ")} ·{" "}
          {formatModelLabel(DEFAULT_MODEL_TYPE)}
        </p>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-accent/50 px-3 py-2">
      <span className="block text-muted-foreground">{label}</span>
      <span className="font-semibold text-foreground">{value}</span>
    </div>
  );
}
