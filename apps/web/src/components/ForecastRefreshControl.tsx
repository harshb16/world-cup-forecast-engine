"use client";

import { RefreshCw } from "lucide-react";

import { FORECAST_REFRESH_INTERVAL_MS } from "@/lib/config";

export function ForecastRefreshControl({
  isRefreshing,
  lastRunAt,
  onRefresh,
}: {
  isRefreshing: boolean;
  lastRunAt: Date | null;
  onRefresh: () => Promise<void>;
}) {
  const minutes = Math.round(FORECAST_REFRESH_INTERVAL_MS / 60_000);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => void onRefresh()}
        disabled={isRefreshing}
        className="inline-flex items-center gap-2 rounded-md border border-white/15 bg-white/[0.05] px-3 py-2 text-sm font-semibold text-white transition hover:bg-white/[0.09] disabled:cursor-wait disabled:text-zinc-500"
      >
        <RefreshCw
          size={15}
          aria-hidden="true"
          className={isRefreshing ? "animate-spin" : ""}
        />
        {isRefreshing ? "Refreshing forecast" : "Refresh forecast"}
      </button>
      <span
        aria-live="polite"
        className="font-mono text-[0.65rem] uppercase tracking-[0.1em] text-zinc-500"
      >
        {lastRunAt
          ? `Auto ${minutes}m · ran ${lastRunAt.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}`
          : `Auto ${minutes}m`}
      </span>
    </div>
  );
}
