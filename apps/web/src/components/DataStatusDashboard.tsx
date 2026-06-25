"use client";

import { useCallback, useEffect, useState } from "react";
import { Radio } from "lucide-react";

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
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="System"
        title="Data Status"
        description="Provider freshness, match lifecycle counts, and operator sync controls."
      />

      <DataStatusCard metadata={status.metadata} />

      <div className="grid gap-4 lg:grid-cols-3">
        <SectionCard title="Match lifecycle">
          <dl className="grid grid-cols-3 gap-3 text-sm">
            {(["scheduled", "in_play", "finished"] as const).map((key) => (
              <div
                key={key}
                className="rounded-md border border-border bg-muted/40 p-3"
              >
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                  {key.replace("_", " ")}
                </dt>
                <dd className="mt-1 text-2xl font-semibold tabular-nums text-foreground">
                  {formatNumber(status.match_status_counts[key] ?? 0)}
                </dd>
              </div>
            ))}
          </dl>
        </SectionCard>

        <SectionCard title="Scheduler">
          <div className="flex flex-col gap-2 text-sm text-muted-foreground">
            <p>
              Tournament active:{" "}
              <span className="font-semibold text-foreground">
                {status.tournament_active ? "yes" : "no"}
              </span>
            </p>
            <p>
              Recommended interval:{" "}
              <span className="font-semibold text-foreground">
                {status.recommended_interval_minutes} min
              </span>
            </p>
            <p>
              Active window every {status.scheduler_active_interval_minutes} min;
              idle window every {status.scheduler_idle_interval_minutes} min.
            </p>
          </div>
        </SectionCard>

        <SectionCard title="Manual sync">
          {status.admin_sync_configured ? (
            <SyncResultsControl onSynced={refresh} />
          ) : (
            <p className="text-sm text-muted-foreground">
              Admin sync is not configured on this API instance.
            </p>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Providers">
        <div className="grid gap-3 md:grid-cols-2">
          {status.providers.map((provider) => (
            <div
              key={provider.name}
              className="rounded-lg border border-border bg-card/85 p-4 text-sm"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="flex items-center gap-2 font-semibold text-foreground">
                  <Radio className="text-primary" aria-hidden="true" />
                  {provider.name}
                </p>
                <span className="rounded-full border border-border px-2 py-0.5 text-[0.65rem] uppercase tracking-widest text-muted-foreground">
                  {provider.is_primary ? "primary" : "fallback"}
                </span>
              </div>
              <p className="mt-2 text-muted-foreground">
                Configured:{" "}
                <span className="text-foreground">
                  {provider.configured ? "yes" : "no"}
                </span>
              </p>
              <p className="mt-1 text-muted-foreground">
                Last used:{" "}
                {provider.last_used ? (
                  <DataFreshness timestamp={provider.last_used} />
                ) : (
                  <span className="text-foreground">not yet</span>
                )}
              </p>
            </div>
          ))}
        </div>
      </SectionCard>

      {latestJob ? (
        <SectionCard title="Latest sync job">
          <div className="grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
            <p>
              Status:{" "}
              <span className="font-semibold text-foreground">
                {latestJob.status}
              </span>
            </p>
            <p>
              Stage:{" "}
              <span className="font-semibold text-foreground">
                {latestJob.stage}
              </span>
            </p>
            <p>
              Provider:{" "}
              <span className="font-semibold text-foreground">
                {latestJob.provider ?? "n/a"}
              </span>
            </p>
            <p>
              Finished:{" "}
              <span className="font-semibold text-foreground">
                {latestJob.finished_at ? (
                  <DataFreshness timestamp={latestJob.finished_at} />
                ) : (
                  "in progress"
                )}
              </span>
            </p>
          </div>
          {latestJob.errors.length > 0 ? (
            <p className="mt-3 font-mono text-xs text-destructive-foreground">
              {latestJob.errors[0]}
            </p>
          ) : null}
        </SectionCard>
      ) : null}
    </div>
  );
}
