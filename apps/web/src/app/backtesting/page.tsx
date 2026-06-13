"use client";

import { useEffect, useState } from "react";
import { Activity, CheckCircle2, Sigma, type LucideIcon } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  BacktestingMetrics,
  fetchBacktestingMetrics,
  ModelType,
} from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

export default function BacktestingPage() {
  const [modelType, setModelType] = useState<ModelType>("calibrated_elo");
  const [metrics, setMetrics] = useState<BacktestingMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    fetchBacktestingMetrics(modelType)
      .then((data) => {
        if (isActive) {
          setMetrics(data);
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Backtesting request failed",
          );
        }
      });

    return () => {
      isActive = false;
    };
  }, [modelType]);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Backtesting"
        title="Baseline validation"
        description="Completed fixtures are scored against current model probabilities. This is evaluation groundwork, not machine learning."
      />

      <div className="mb-5 flex flex-wrap gap-2">
        {(["calibrated_elo", "poisson", "elo"] as ModelType[]).map((model) => (
          <button
            key={model}
            type="button"
            onClick={() => {
              if (model === modelType) {
                return;
              }
              setMetrics(null);
              setError(null);
              setModelType(model);
            }}
            className={`rounded-md border px-3 py-2 text-sm font-semibold transition ${
              modelType === model
                ? "border-emerald-300/40 bg-emerald-300 text-zinc-950"
                : "border-white/10 bg-white/[0.05] text-zinc-300 hover:bg-white/[0.08]"
            }`}
          >
            {formatModelLabel(model)}
          </button>
        ))}
      </div>

      {error ? <ErrorState message={error} /> : null}
      {!error && !metrics ? <LoadingState label="Loading metrics" /> : null}

      {!error && metrics ? (
        <div className="space-y-6">
          <section className="grid gap-4 md:grid-cols-4">
            <MetricCard
              icon={Activity}
              label="Completed fixtures"
              value={formatNumber(metrics.sample_size)}
              detail={`${metrics.data_mode} data mode`}
            />
            <MetricCard
              icon={CheckCircle2}
              label="Accuracy"
              value={formatMetric(metrics.accuracy, "percent")}
              detail="Most likely 1X2 outcome"
            />
            <MetricCard
              icon={Sigma}
              label="Brier score"
              value={formatMetric(metrics.brier_score, "number")}
              detail="Lower is better"
            />
            <MetricCard
              icon={Sigma}
              label="Log loss"
              value={formatMetric(metrics.log_loss, "number")}
              detail="Lower is better"
            />
          </section>

          <SectionCard>
            <h2 className="text-base font-semibold text-white">
              How this foundation is used
            </h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="text-xs font-semibold uppercase text-zinc-500">
                  Current scoring
                </h3>
                <p className="mt-2 text-sm leading-6 text-zinc-300">
                  Each completed match is converted into win, draw, or loss.
                  The selected baseline model provides probabilities before
                  scoring accuracy, Brier score, and log loss.
                </p>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase text-zinc-500">
                  Limitations
                </h3>
                <ul className="mt-2 space-y-2">
                  {metrics.limitations.map((limitation) => (
                    <li
                      key={limitation}
                      className="text-sm leading-6 text-zinc-300"
                    >
                      {limitation}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </SectionCard>
        </div>
      ) : null}
    </AppShell>
  );
}

function formatModelLabel(modelType: ModelType): string {
  if (modelType === "calibrated_elo") {
    return "Calibrated Elo";
  }

  return modelType.toUpperCase();
}

function MetricCard({
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
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-sm leading-5 text-zinc-400">{detail}</p>
    </div>
  );
}

function formatMetric(
  value: number | null,
  format: "number" | "percent",
): string {
  if (value === null) {
    return "Pending";
  }

  if (format === "percent") {
    return formatPercent(value);
  }

  return formatNumber(value, 3);
}
