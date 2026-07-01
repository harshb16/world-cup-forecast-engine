"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Target,
  Trophy,
  XCircle,
  type LucideIcon,
} from "lucide-react";
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

import { CalibrationChart } from "@/components/analytics/CalibrationChart";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { SectionCard } from "@/components/ui/SectionCard";
import { Badge } from "@/components/ui/badge";
import {
  DEFAULT_MODEL_TYPE,
  fetchRetrospective,
  fetchTeams,
  ModelType,
  Retrospective,
  RetrospectiveMatchInsight,
  Team,
} from "@/lib/api";
import { CHART_LINE_COLORS, CHART_TOOLTIP_STYLE } from "@/lib/chart-colors";
import { formatModelLabel, formatNumber, formatPercent } from "@/lib/format";

const SCORING_MODELS: ModelType[] = [
  "elo",
  "poisson",
  "oracle_v2",
  "dixon_coles",
  "oracle_v3",
];

export function RetrospectiveExperience() {
  const [modelType, setModelType] = useState<ModelType>(DEFAULT_MODEL_TYPE);
  const [retrospective, setRetrospective] = useState<Retrospective | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;
    setError(null);
    Promise.all([fetchRetrospective(modelType), fetchTeams()])
      .then(([data, teamData]) => {
        if (isActive) {
          setRetrospective(data);
          setTeams(teamData);
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Retrospective request failed",
          );
        }
      });
    return () => {
      isActive = false;
    };
  }, [modelType]);

  const teamNames = useMemo(
    () => Object.fromEntries(teams.map((team) => [team.id, team.name])),
    [teams],
  );

  const chartData = useMemo(() => {
    if (!retrospective || retrospective.champion_arc.length === 0) {
      return { rows: [], teamIds: [] as string[], knockoutLabels: [] as string[] };
    }

    const latest = retrospective.champion_arc.at(-1)?.champion_probabilities ?? {};
    const topTeams = Object.entries(latest)
      .sort((a, b) => b[1] - a[1])
      .map(([teamId]) => teamId);

    const rows = retrospective.champion_arc.map((point) => {
      const row: Record<string, string | number> = {
        label: point.label,
        milestone_id: point.milestone_id ?? "",
      };
      for (const teamId of topTeams) {
        row[teamId] = point.champion_probabilities[teamId] ?? 0;
      }
      return row;
    });

    const knockoutLabels = retrospective.champion_arc
      .filter((point) => (point.milestone_id ?? "").startsWith("after_"))
      .map((point) => point.label);

    return { rows, teamIds: topTeams, knockoutLabels };
  }, [retrospective]);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!retrospective) {
    return <LoadingState label="Loading tournament retrospective" />;
  }

  return (
    <div className="space-y-6">
      <SectionCard>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-primary">
              Retrospective
            </p>
            <h2 className="mt-1 text-lg font-semibold text-foreground">
              How the model tracked the tournament
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Champion arc, high-confidence calls, and calibration against
              completed fixtures.
            </p>
          </div>
          <label className="text-sm text-muted-foreground">
            Model
            <select
              className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
              value={modelType}
              onChange={(event) => setModelType(event.target.value as ModelType)}
            >
              {SCORING_MODELS.map((model) => (
                <option key={model} value={model}>
                  {formatModelLabel(model)}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard
            icon={Trophy}
            label="Champion"
            value={retrospective.champion_team_name ?? "TBD"}
            detail={
              retrospective.pre_tournament_champion_probability === null
                ? "Final not recorded yet"
                : `${formatPercent(retrospective.pre_tournament_champion_probability)} pre-tournament`
            }
          />
          <SummaryCard
            icon={Target}
            label="Accuracy"
            value={
              retrospective.scoring.accuracy === null
                ? "—"
                : formatPercent(retrospective.scoring.accuracy)
            }
            detail={`${retrospective.scoring.sample_size} completed fixtures`}
          />
          <SummaryCard
            icon={BarChart3}
            label="Brier score"
            value={
              retrospective.scoring.brier_score === null
                ? "—"
                : formatNumber(retrospective.scoring.brier_score, 3)
            }
            detail="Lower is better"
          />
          <SummaryCard
            icon={BrainCircuit}
            label="Log loss"
            value={
              retrospective.scoring.log_loss === null
                ? "—"
                : formatNumber(retrospective.scoring.log_loss, 3)
            }
            detail="Lower is better"
          />
        </div>
      </SectionCard>

      <SectionCard>
        <p className="text-xs font-semibold uppercase text-primary">
          Champion arc
        </p>
        <h2 className="mt-1 text-lg font-semibold text-foreground">
          Top five teams through the tournament
        </h2>
        {chartData.rows.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            Milestone snapshots will appear once probability history is available.
          </p>
        ) : (
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
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </SectionCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <InsightList
          title="Top model hits"
          subtitle="Highest-confidence correct calls"
          items={retrospective.top_hits}
          variant="hit"
        />
        <InsightList
          title="Top model misses"
          subtitle="Highest-confidence wrong calls"
          items={retrospective.top_misses}
          variant="miss"
        />
      </div>

      <SectionCard>
        <p className="text-xs font-semibold uppercase text-primary">
          Calibration
        </p>
        <h2 className="mt-1 text-lg font-semibold text-foreground">
          Predicted vs observed frequencies
        </h2>
        <div className="mt-6">
          <CalibrationChart bins={retrospective.scoring.calibration_bins} />
        </div>
        <ul className="mt-5 space-y-1 text-sm text-muted-foreground">
          {retrospective.limitations.map((limitation) => (
            <li key={limitation}>• {limitation}</li>
          ))}
        </ul>
      </SectionCard>
    </div>
  );
}

function InsightList({
  title,
  subtitle,
  items,
  variant,
}: {
  title: string;
  subtitle: string;
  items: RetrospectiveMatchInsight[];
  variant: "hit" | "miss";
}) {
  const Icon = variant === "hit" ? CheckCircle2 : XCircle;

  return (
    <SectionCard>
      <p className="text-xs font-semibold uppercase text-primary">{title}</p>
      <h2 className="mt-1 text-lg font-semibold text-foreground">{subtitle}</h2>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">
          Not enough completed fixtures yet.
        </p>
      ) : (
        <ul className="mt-4 space-y-3">
          {items.map((item) => (
            <li
              key={item.match_id}
              className="rounded-lg border border-border bg-white/[0.04] p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-foreground">
                    {item.team_a_name} vs {item.team_b_name}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {item.stage} · predicted {item.predicted_outcome} · actual{" "}
                    {item.actual_outcome}
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className={
                    variant === "hit"
                      ? "border-emerald-500/40 text-emerald-300"
                      : "border-red-500/40 text-red-300"
                  }
                >
                  <Icon size={14} className="mr-1" aria-hidden="true" />
                  {formatPercent(item.confidence)}
                </Badge>
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-white/[0.055] p-4">
      <Icon size={18} className="text-primary" aria-hidden="true" />
      <p className="mt-4 text-xs font-medium uppercase text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-xl font-semibold text-foreground">{value}</p>
      <p className="mt-1 text-sm leading-5 text-muted-foreground">{detail}</p>
    </div>
  );
}
