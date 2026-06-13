"use client";

import { useEffect, useState } from "react";
import { BarChart3, BrainCircuit, Target, type LucideIcon } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { fetchModelMetadata, ModelMetadata } from "@/lib/api";

export default function ModelsPage() {
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    fetchModelMetadata()
      .then((data) => {
        if (isActive) {
          setModels(data);
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

  return (
    <AppShell>
      <PageHeader
        eyebrow="Models"
        title="Transparent baselines before ML"
        description="Current simulations use honest statistical baselines. Machine learning comes after data coverage and evaluation are strong enough."
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
              label="Current model class"
              value="Statistical baselines"
              detail="No trained ML in production yet"
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
              value="Deferred"
              detail="Planned after validation and backtesting"
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
                  <span className="rounded-md border border-white/10 bg-white/[0.06] px-2.5 py-1 text-xs font-semibold text-zinc-300">
                    {model.is_ml ? "ML" : "No ML"}
                  </span>
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
