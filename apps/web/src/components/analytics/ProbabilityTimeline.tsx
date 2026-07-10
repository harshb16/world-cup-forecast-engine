"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  fetchProbabilityHistory,
  fetchTeams,
  ProbabilityHistory,
  ProbabilitySnapshot,
  Team,
} from "@/lib/api";
import { formatPercent } from "@/lib/format";
import { CHART_LINE_COLORS, CHART_TOOLTIP_STYLE } from "@/lib/chart-colors";

export function ProbabilityTimeline({ showScrubber = true }: { showScrubber?: boolean }) {
  const [history, setHistory] = useState<ProbabilityHistory | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    let isActive = true;
    Promise.all([fetchProbabilityHistory(), fetchTeams()])
      .then(([historyData, teamData]) => {
        if (isActive) {
          setHistory(historyData);
          setTeams(teamData);
          setSelectedIndex(Math.max(0, historyData.snapshots.length - 1));
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Timeline request failed",
          );
        }
      });
    return () => {
      isActive = false;
    };
  }, []);

  const chartData = useMemo(() => {
    if (!history || history.snapshots.length === 0) {
      return { rows: [], teamIds: [] as string[], knockoutLabels: [] as string[] };
    }

    const latest = history.snapshots[history.snapshots.length - 1];
    const topTeams = Object.entries(latest.champion_probabilities)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([teamId]) => teamId);

    const rows = history.snapshots.map((snapshot) => {
      const row: Record<string, string | number> = {
        label: snapshot.label,
        milestone_id: snapshot.milestone_id,
      };
      for (const teamId of topTeams) {
        row[teamId] = snapshot.champion_probabilities[teamId] ?? 0;
      }
      return row;
    });

    const knockoutLabels = history.snapshots
      .filter((snapshot) => snapshot.milestone_id.startsWith("after_"))
      .map((snapshot) => snapshot.label);

    return { rows, teamIds: topTeams, knockoutLabels };
  }, [history]);

  const selectedSnapshot = useMemo(() => {
    if (!history || history.snapshots.length === 0) {
      return null;
    }
    return history.snapshots[selectedIndex] ?? history.snapshots.at(-1) ?? null;
  }, [history, selectedIndex]);

  const teamNames = useMemo(
    () => Object.fromEntries(teams.map((team) => [team.id, team.name])),
    [teams],
  );

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!history) {
    return <LoadingState label="Loading probability timeline" />;
  }

  if (chartData.rows.length === 0) {
    return (
      <SectionCard>
        <p className="text-xs font-semibold uppercase text-primary">
          Timeline
        </p>
        <h2 className="mt-1 text-lg font-semibold text-foreground">
          Champion probability through the tournament
        </h2>
        <p className="mt-3 text-sm text-muted-foreground">
          Tournament milestones will appear here once fixtures are available.
        </p>
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      <SectionCard>
        <p className="text-xs font-semibold uppercase text-primary">
          Timeline
        </p>
        <h2 className="mt-1 text-lg font-semibold text-foreground">
          Champion probability through the tournament
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Top eight teams by latest champion probability across group matchdays
          and knockout rounds.
        </p>

        <div className="mt-5 h-80 w-full">
          <ResponsiveContainer width="100%" height="100%" minWidth={0}>
            <LineChart data={chartData.rows}>
              <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
              <XAxis dataKey="label" stroke="#71717a" fontSize={12} />
              <YAxis
                tickFormatter={(value: number) => formatPercent(value)}
                stroke="#71717a"
                fontSize={12}
                domain={[0, "auto"]}
              />
              {chartData.knockoutLabels.map((label) => (
                <ReferenceLine
                  key={label}
                  x={label}
                  stroke="rgba(255,255,255,0.18)"
                  strokeDasharray="4 4"
                />
              ))}
              <Tooltip
                contentStyle={CHART_TOOLTIP_STYLE}
                formatter={(value, name) => {
                  const numeric = typeof value === "number" ? value : 0;
                  return [
                    formatPercent(numeric),
                    teamNames[String(name)] ?? String(name),
                  ];
                }}
              />
              <Legend formatter={(value) => teamNames[value] ?? value} />
              {chartData.teamIds.map((teamId, index) => (
                <Line
                  key={teamId}
                  type="monotone"
                  dataKey={teamId}
                  stroke={CHART_LINE_COLORS[index % CHART_LINE_COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>

      {showScrubber ? <MilestoneScrubber
        snapshots={history.snapshots}
        selectedIndex={selectedIndex}
        onSelect={setSelectedIndex}
        teamNames={teamNames}
        selectedSnapshot={selectedSnapshot}
      /> : null}
    </div>
  );
}

function MilestoneScrubber({
  snapshots,
  selectedIndex,
  onSelect,
  teamNames,
  selectedSnapshot,
}: {
  snapshots: ProbabilitySnapshot[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  teamNames: Record<string, string>;
  selectedSnapshot: ProbabilitySnapshot | null;
}) {
  const topAtMilestone = useMemo(() => {
    if (!selectedSnapshot) {
      return [];
    }
    return Object.entries(selectedSnapshot.champion_probabilities)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);
  }, [selectedSnapshot]);

  return (
    <SectionCard>
      <p className="text-xs font-semibold uppercase text-primary">
        Time machine
      </p>
      <h2 className="mt-1 text-lg font-semibold text-foreground">
        Scrub tournament milestones
      </h2>
      <label className="mt-4 block text-sm text-muted-foreground">
        Milestone
        <input
          type="range"
          min={0}
          max={Math.max(0, snapshots.length - 1)}
          value={selectedIndex}
          onChange={(event) => onSelect(Number(event.target.value))}
          className="mt-2 w-full accent-primary"
        />
      </label>
      <p className="mt-2 text-sm font-semibold text-foreground">
        {selectedSnapshot?.label ?? "—"}
      </p>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {topAtMilestone.map(([teamId, probability]) => (
          <div
            key={teamId}
            className="flex items-center justify-between rounded-md border border-border bg-muted/40 px-3 py-2 text-sm"
          >
            <span className="font-medium text-foreground">
              {teamNames[teamId] ?? teamId}
            </span>
            <span className="font-mono text-muted-foreground">
              {formatPercent(probability)}
            </span>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
