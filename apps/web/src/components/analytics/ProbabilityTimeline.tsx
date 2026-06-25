"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { SectionCard } from "@/components/ui/SectionCard";
import { fetchProbabilityHistory, fetchTeams, ProbabilityHistory, Team } from "@/lib/api";
import { formatPercent } from "@/lib/format";

const LINE_COLORS = [
  "#34d399",
  "#60a5fa",
  "#f472b6",
  "#fbbf24",
  "#a78bfa",
  "#fb7185",
  "#22d3ee",
  "#f97316",
];

export function ProbabilityTimeline() {
  const [history, setHistory] = useState<ProbabilityHistory | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;
    Promise.all([fetchProbabilityHistory(), fetchTeams()])
      .then(([historyData, teamData]) => {
        if (isActive) {
          setHistory(historyData);
          setTeams(teamData);
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
      return { rows: [], teamIds: [] as string[] };
    }

    const latest = history.snapshots[history.snapshots.length - 1];
    const topTeams = Object.entries(latest.champion_probabilities)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([teamId]) => teamId);

    const rows = history.snapshots.map((snapshot) => {
      const row: Record<string, string | number> = {
        label: snapshot.timestamp.slice(0, 10),
      };
      for (const teamId of topTeams) {
        row[teamId] = snapshot.champion_probabilities[teamId] ?? 0;
      }
      return row;
    });

    return { rows, teamIds: topTeams };
  }, [history]);

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
        <h2 className="mt-1 text-lg font-semibold text-white">
          Champion probability history
        </h2>
        <p className="mt-3 text-sm text-zinc-400">
          Run sync to capture the first probability snapshot.
        </p>
      </SectionCard>
    );
  }

  return (
    <SectionCard>
      <p className="text-xs font-semibold uppercase text-primary">
        Timeline
      </p>
      <h2 className="mt-1 text-lg font-semibold text-white">
        Champion probability history
      </h2>
      <p className="mt-1 text-sm text-zinc-400">
        Top eight teams by latest champion probability.
      </p>

      <div className="mt-5 h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData.rows}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
            <XAxis dataKey="label" stroke="#71717a" fontSize={12} />
            <YAxis
              tickFormatter={(value: number) => formatPercent(value)}
              stroke="#71717a"
              fontSize={12}
              domain={[0, "auto"]}
            />
            <Tooltip
              contentStyle={{
                background: "#0f1720",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "0.5rem",
              }}
              formatter={(value, name) => {
                const numeric = typeof value === "number" ? value : 0;
                return [formatPercent(numeric), teamNames[String(name)] ?? String(name)];
              }}
            />
            <Legend
              formatter={(value) => teamNames[value] ?? value}
            />
            {chartData.teamIds.map((teamId, index) => (
              <Line
                key={teamId}
                type="monotone"
                dataKey={teamId}
                stroke={LINE_COLORS[index % LINE_COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  );
}
