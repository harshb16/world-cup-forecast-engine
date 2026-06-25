"use client";

import { useCallback, useEffect, useState } from "react";
import { Activity, Database, Radio } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { DataFreshness } from "@/components/DataFreshness";
import { DataStatusCard } from "@/components/DataStatusCard";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { SyncResultsControl } from "@/components/SyncResultsControl";
import { SectionCard } from "@/components/ui/SectionCard";
import { fetchDataStatus, type DataStatus } from "@/lib/api";
import { formatNumber } from "@/lib/format";

export function DataStatusDashboard() {
  const [status, setStatus] = useState<DataStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setStatus(await fetchDataStatus());
    } catch (caught: unknown) {
      setError(
        caught instanceof Error ? caught.message : "Failed to load data status.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (loading && !status) {
    return <LoadingState label="Loading data status" />;
  }

  if (error && !status) {
    return <ErrorState message={error} onRetry={() => void refresh()} />;
  }

  if (!status) {
    return null;
  }

  const latestJob = status.latest_job;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Status"
        description="Provider freshness, match lifecycle counts, and operator sync controls."
        icon={Database}
      />

      <DataStatusCard metadata={status.metadata} />

      <div className="grid gap-4 lg:grid-cols-3">
        <SectionCard title="Match lifecycle" icon={Activity}>
          <dl className="grid grid-cols-3 gap-3 text-sm">
            {(["scheduled", "in_play", "finished"] as const).map((key) => (
              <div key={key} className="rounded-md border border-white/10 bg-black/20 p-3">
                <dt className="text-xs uppercase tracking-[0.08em] text-zinc-500">
                  {key.replace("_", " ")}
                </dt>
                <dd className="mt-1 text-2xl font-semibold text-zinc-100">
                  {formatNumber(status.match_status_counts[key] ?? 0)}
                </dd>
              </div>
            ))}
          </dl>
        </SectionCard>

        <SectionCard title="Scheduler" icon={Radio}>
          <div className="space-y-2 text-sm text-zinc-300">
            <p>
              Tournament active:{" "}
              <span className="font-semibold text-zinc-100">
                {status.tournament_active ? "yes" : "no"}
              </span>
            </p>
            <p>
              Recommended interval:{" "}
              <span className="font-semibold text-zinc-100">
                {status.recommended_interval_minutes} min
              </span>
            </p>
            <p className="text-zinc-400">
              Active window every {status.scheduler_active_interval_minutes} min;
              idle window every {status.scheduler_idle_interval_minutes} min.
            </p>
          </div>
        </SectionCard>

        <SectionCard title="Manual sync" icon={Database}>
          {status.admin_sync_configured ? (
            <SyncResultsControl onSynced={refresh} />
          ) : (
            <p className="text-sm text-zinc-400">
              Admin sync is not configured on this API instance.
            </p>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Providers" icon={Radio}>
        <div className="grid gap-3 md:grid-cols-2">
          {status.providers.map((provider) => (
            <div
              key={provider.name}
              className="rounded-lg border border-white/10 bg-[#101722]/85 p-4 text-sm"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-zinc-100">{provider.name}</p>
                <span className="rounded-full border border-white/10 px-2 py-0.5 text-[0.65rem] uppercase tracking-[0.08em] text-zinc-400">
                  {provider.is_primary ? "primary" : "fallback"}
                </span>
              </div>
              <p className="mt-2 text-zinc-400">
                Configured:{" "}
                <span className="text-zinc-200">
                  {provider.configured ? "yes" : "no"}
                </span>
              </p>
              <p className="mt-1 text-zinc-400">
                Last used:{" "}
                {provider.last_used ? (
                  <DataFreshness timestamp={provider.last_used} />
                ) : (
                  <span className="text-zinc-200">not yet</span>
                )}
              </p>
            </div>
          ))}
        </div>
      </SectionCard>

      {latestJob ? (
        <SectionCard title="Latest sync job" icon={Activity}>
          <div className="grid gap-2 text-sm text-zinc-300 md:grid-cols-2">
            <p>
              Status:{" "}
              <span className="font-semibold text-zinc-100">{latestJob.status}</span>
            </p>
            <p>
              Stage:{" "}
              <span className="font-semibold text-zinc-100">{latestJob.stage}</span>
            </p>
            <p>
              Provider:{" "}
              <span className="font-semibold text-zinc-100">
                {latestJob.provider ?? "n/a"}
              </span>
            </p>
            <p>
              Finished:{" "}
              <span className="font-semibold text-zinc-100">
                {latestJob.finished_at ? (
                  <DataFreshness timestamp={latestJob.finished_at} />
                ) : (
                  "in progress"
                )}
              </span>
            </p>
          </div>
          {latestJob.errors.length > 0 ? (
            <p className="mt-3 font-mono text-xs text-rose-300">{latestJob.errors[0]}</p>
          ) : null}
        </SectionCard>
      ) : null}
    </div>
  );
}
