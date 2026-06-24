"use client";

import { useEffect, useState } from "react";
import { BarChart3, BrainCircuit, Loader2, Target, type LucideIcon } from "lucide-react";

import { CalibrationChart } from "@/components/analytics/CalibrationChart";
import { DataQualityDesk } from "@/components/analytics/DataQualityDesk";
import { ModelComparisonPanel } from "@/components/analytics/ModelComparisonPanel";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  fetchCurrentTournamentScoring,
  fetchDataQuality,
  fetchModelComparison,
  fetchModelMetadata,
  fetchTeams,
  DEFAULT_MODEL_TYPE,
  CurrentTournamentScoring,
  DataQualityReport,
  ModelComparison,
  ModelMetadata,
  ModelType,
} from "@/lib/api";
import { formatModelLabel, formatNumber, formatPercent } from "@/lib/format";

const SCORING_MODELS: ModelType[] = [
  "elo",
  "poisson",
  "oracle_v2",
  "dixon_coles",
  "oracle_v3",
];

export default function ModelsPage() {
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [dataQuality, setDataQuality] = useState<DataQualityReport | null>(null);
  const [comparison, setComparison] = useState<ModelComparison | null>(null);
  const [teamNames, setTeamNames] = useState<Record<string, string>>({});
  const [loadingComparison, setLoadingComparison] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [scoringModel, setScoringModel] =
    useState<ModelType>(DEFAULT_MODEL_TYPE);
  const [scoring, setScoring] = useState<CurrentTournamentScoring | null>(null);
  const [scoringError, setScoringError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;
    fetchCurrentTournamentScoring(scoringModel)
      .then((metrics) => {
        if (isActive) {
          setScoring(metrics);
          setScoringError(null);
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setScoringError(
            caughtError instanceof Error
              ? caughtError.message
              : "Current tournament scoring request failed",
          );
        }
      });
    return () => {
      isActive = false;
    };
  }, [scoringModel]);

  useEffect(() => {
    let isActive = true;

    Promise.all([fetchModelMetadata(), fetchDataQuality(), fetchTeams()])
      .then(([modelData, quality, teams]) => {
        if (isActive) {
          setModels(modelData);
          setDataQuality(quality);
          setTeamNames(
            Object.fromEntries(teams.map((team) => [team.id, team.name])),
          );
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Model metadata request failed",
          );
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  async function loadComparison() {
    setLoadingComparison(true);
    setComparisonError(null);

    try {
      const comparisonData = await fetchModelComparison(200, 42, DEFAULT_MODEL_TYPE);
      setComparison(comparisonData);
    } catch (caughtError: unknown) {
      setComparisonError(
        caughtError instanceof Error
          ? caughtError.message
          : "Model comparison request failed",
      );
    } finally {
      setLoadingComparison(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Models"
        title="Model trust desk"
        description="Production, baseline, and experimental models — with scoring on completed tournament fixtures."
      />

      {error ? <ErrorState message={error} /> : null}
      {!error && models.length === 0 ? (
        <LoadingState label="Loading model metadata" />
      ) : null}

      {!error && models.length > 0 ? (
        <div className="space-y-6">
          <section className="grid gap-4 md:grid-cols-3">
            <SummaryCard
              icon={Target}
              label="Default model"
              value={formatModelLabel(DEFAULT_MODEL_TYPE)}
              detail="Open-data Elo from senior international results"
            />
            <SummaryCard
              icon={BarChart3}
              label="Primary output"
              value="Stage probabilities"
              detail="Monte Carlo aggregation over tournament runs"
            />
            <SummaryCard
              icon={BrainCircuit}
              label="ML status"
              value="Experimental"
              detail="GBM and Oracle v3 are comparison-only until validated"
            />
          </section>

          <div className="grid gap-5 xl:grid-cols-2">
            {models.map((model) => (
              <SectionCard key={model.id}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase text-emerald-200">
                      {model.id}
                    </p>
                    <h2 className="mt-1 text-lg font-semibold text-white">
                      {model.name}
                    </h2>
                  </div>
                  <div className="flex flex-wrap justify-end gap-2">
                    <span className="rounded-md border border-white/10 bg-white/[0.06] px-2.5 py-1 text-xs font-semibold text-zinc-300">
                      {model.is_ml ? "ML" : "Statistical"}
                    </span>
                    <span className="rounded-md border border-white/10 bg-white/[0.06] px-2.5 py-1 text-xs font-semibold capitalize text-zinc-300">
                      {model.maturity}
                    </span>
                  </div>
                </div>

                <ModelList title="Inputs" items={model.inputs} />
                <ModelList title="Assumptions" items={model.assumptions} />
                <ModelList title="Limitations" items={model.limitations} />
                <ModelList
                  title="Supported outputs"
                  items={model.supported_outputs}
                />
              </SectionCard>
            ))}
          </div>

          {dataQuality ? <DataQualityDesk report={dataQuality} /> : null}

          <SectionCard>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase text-[var(--turf)]">
                  Current tournament scoring
                </p>
                <h2 className="mt-1 text-lg font-semibold text-white">
                  Scores against completed fixtures
                </h2>
                <p className="mt-1 text-sm text-zinc-400">
                  A current-tournament check only. This is not historical
                  out-of-sample backtesting.
                </p>
              </div>
              <label className="flex flex-col gap-1 text-xs text-zinc-400">
                Model
                <select
                  value={scoringModel}
                  onChange={(event) =>
                    setScoringModel(event.target.value as ModelType)
                  }
                  className="rounded-md border border-white/10 bg-black/20 px-3 py-2 text-sm text-white"
                >
                  {SCORING_MODELS.map((model) => (
                    <option key={model} value={model}>
                      {formatModelLabel(model)}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {scoringError ? (
              <p className="mt-4 text-sm text-red-200">{scoringError}</p>
            ) : null}

            {scoring ? (
              <>
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <SummaryCard
                    icon={Target}
                    label="Accuracy"
                    value={
                      scoring.accuracy === null
                        ? "—"
                        : formatPercent(scoring.accuracy)
                    }
                    detail={`${scoring.sample_size} completed fixtures`}
                  />
                  <SummaryCard
                    icon={BarChart3}
                    label="Brier score"
                    value={
                      scoring.brier_score === null
                        ? "—"
                        : formatNumber(scoring.brier_score, 3)
                    }
                    detail="Lower is better"
                  />
                  <SummaryCard
                    icon={BrainCircuit}
                    label="Log loss"
                    value={
                      scoring.log_loss === null
                        ? "—"
                        : formatNumber(scoring.log_loss, 3)
                    }
                    detail="Lower is better"
                  />
                </div>
                <div className="mt-6">
                  <CalibrationChart bins={scoring.calibration_bins} />
                </div>
                <ul className="mt-5 space-y-1 text-sm text-zinc-400">
                  {scoring.limitations.map((limitation) => (
                    <li key={limitation}>• {limitation}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </SectionCard>

          {!comparison ? (
            <SectionCard>
              <p className="text-xs font-semibold uppercase text-[var(--turf)]">
                Model comparison
              </p>
              <h2 className="mt-1 text-lg font-semibold text-white">
                Compare champion probabilities across models
              </h2>
              <p className="mt-1 text-sm text-zinc-400">
                Runs four simulations on demand — load only when you want to
                inspect model divergence.
              </p>
              <div className="mt-4">
                <button
                  type="button"
                  onClick={loadComparison}
                  disabled={loadingComparison}
                  className="inline-flex items-center gap-2 rounded-md bg-[var(--turf)] px-4 py-2 text-sm font-semibold text-zinc-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loadingComparison ? (
                    <Loader2 size={16} className="animate-spin" aria-hidden="true" />
                  ) : null}
                  {loadingComparison ? "Loading comparison…" : "Load model comparison"}
                </button>
                {comparisonError ? (
                  <p className="mt-3 text-sm text-red-200">{comparisonError}</p>
                ) : null}
              </div>
            </SectionCard>
          ) : (
            <ModelComparisonPanel
              comparison={comparison}
              teamNames={teamNames}
            />
          )}
        </div>
      ) : null}
    </AppShell>
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
    <div className="rounded-lg border border-white/10 bg-white/[0.055] p-4">
      <Icon size={18} className="text-emerald-200" aria-hidden="true" />
      <p className="mt-4 text-xs font-medium uppercase text-zinc-400">
        {label}
      </p>
      <p className="mt-2 text-xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-sm leading-5 text-zinc-400">{detail}</p>
    </div>
  );
}

function ModelList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-5">
      <h3 className="text-xs font-semibold uppercase text-zinc-500">{title}</h3>
      <ul className="mt-2 space-y-2">
        {items.map((item) => (
          <li key={item} className="text-sm leading-6 text-zinc-300">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
